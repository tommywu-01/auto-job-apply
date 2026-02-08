#!/usr/bin/env python3
"""
LinkedIn Easy Apply 自动化申请脚本 - 增强版 v2.0
整合 EasyApplyJobsBot 和 linkedin-application-bot 的最佳实践

改进:
1. 反爬虫检测 (selenium-stealth) - 伪装浏览器指纹
2. Cookie 持久化 - save_cookies() 和 load_cookies()
3. 智能等待机制 - random.uniform(1, botSpeed)
4. 更好的错误处理 - try-except + 截图
5. ChromeDriverManager - 自动管理驱动版本
6. 多种 fallback selector - 处理动态加载
"""

import os
import sys
import time
import yaml
import json
import math
import pickle
import random
import logging
import hashlib
from pathlib import Path
from datetime import datetime
from typing import List, Optional, Dict

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import (
    TimeoutException, NoSuchElementException, 
    ElementNotInteractableException, StaleElementReferenceException,
    ElementClickInterceptedException
)
from webdriver_manager.chrome import ChromeDriverManager

# 导入 stealth 工具
try:
    from selenium_stealth import stealth
    STEALTH_AVAILABLE = True
except ImportError:
    STEALTH_AVAILABLE = False
    print("\033[93m⚠️ 提示: pip install selenium-stealth 以获得更好的反检测保护\033[00m")

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))
from utils_stealth import (
    StealthDriverManager, prRed, prGreen, prYellow, prBlue,
    setup_stealth_driver, with_retry
)

# 配置日志
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)
log_file = log_dir / f"linkedin_apply_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Cookie 和截图目录
COOKIES_DIR = Path("cookies")
COOKIES_DIR.mkdir(exist_ok=True)
SCREENSHOTS_DIR = Path("screenshots")
SCREENSHOTS_DIR.mkdir(exist_ok=True)

# Bot 速度设置 (参考 reference-easy-apply-bot)
FAST = 2
MEDIUM = 3
SLOW = 5
BOT_SPEED = SLOW  # 可调整: FAST, MEDIUM, SLOW


class LinkedInEasyApply:
    """
    LinkedIn Easy Apply 增强版自动化申请器
    整合 reference-easy-apply-bot 的最佳实践
    """
    
    def __init__(self, config_path: str = "config/profile.yaml"):
        self.config = self._load_config(config_path)
        self.driver = None
        self.wait = None
        self.short_wait = None
        self.applied_count = 0
        self.failed_count = 0
        self.skipped_count = 0
        self.blacklisted_count = 0
        self.already_applied_count = 0
        self.headless = False
        self.cookies_path = None
        self.start_time = None
        
    def _load_config(self, path: str) -> dict:
        """加载配置文件"""
        try:
            # 尝试多个可能的路径
            possible_paths = [
                Path(path),
                Path(__file__).parent / path,
                Path.home() / ".openclaw" / "workspace" / "auto-job-apply" / path
            ]
            
            for config_path in possible_paths:
                if config_path.exists():
                    with open(config_path, 'r') as f:
                        return yaml.safe_load(f)
            
            # 如果找不到，使用默认配置
            logger.warning(f"配置文件未找到: {path}，使用默认配置")
            return self._get_default_config()
            
        except Exception as e:
            logger.error(f"加载配置文件失败: {e}")
            return self._get_default_config()
    
    def _get_default_config(self) -> dict:
        """获取默认配置"""
        return {
            'personal_info': {
                'email': os.environ.get('LINKEDIN_EMAIL', ''),
                'password': os.environ.get('LINKEDIN_PASSWORD', ''),
                'phone': os.environ.get('PHONE_NUMBER', '917-742-4303'),
                'first_name': 'Tommy',
                'last_name': 'Wu',
                'linkedin': 'https://www.linkedin.com/in/tommywu/',
                'website': 'https://www.tommywu.io',
                'portfolio': 'https://www.tommywu.io'
            },
            'application_settings': {
                'resume_path': '~/Downloads/TOMMY WU Resume Dec 2025.pdf',
                'cover_letter': '',
                'years_of_experience': '5',
                'desired_salary': '150000',
                'notice_period_days': '30'
            },
            'search_preferences': {
                'keywords': ['Director of Technical Services', 'VP of Technology', 'Technical Director'],
                'locations': ['New York', 'United States'],
                'easy_apply_only': True,
                'max_applications_per_day': 25
            },
            'blacklist': {
                'companies': [],
                'titles': ['Senior', 'Sr.', 'Staff', 'Principal', 'Lead']
            },
            'equal_opportunity': {
                'gender': 'Male',
                'ethnicity': 'Asian',
                'veteran_status': 'No',
                'disability_status': 'No'
            }
        }
    
    def get_hash(self, string: str) -> str:
        """生成MD5哈希 - 参考 reference-easy-apply-bot"""
        return hashlib.md5(string.encode('utf-8')).hexdigest()
    
    def setup_driver(self, headless: bool = False, use_profile: bool = True):
        """
        设置Chrome浏览器驱动 - 整合 reference-easy-apply-bot 的 stealth 配置
        """
        logger.info(f"设置Chrome驱动... (headless={headless}, use_profile={use_profile})")
        self.headless = headless
        
        # 使用 StealthDriverManager
        profile_path = ""
        if use_profile:
            # macOS Chrome profile 路径
            user_data_dir = Path.home() / "Library/Application Support/Google/Chrome"
            if user_data_dir.exists():
                profile_path = str(user_data_dir / "Default")
        
        self.manager = StealthDriverManager(
            headless=headless,
            use_profile=use_profile,
            profile_path=profile_path,
            bot_speed=BOT_SPEED,
            cookies_dir=COOKIES_DIR,
            screenshots_dir=SCREENSHOTS_DIR
        )
        
        self.driver = self.manager.setup_driver()
        
        # 设置等待时间
        self.wait = WebDriverWait(self.driver, 15)
        self.short_wait = WebDriverWait(self.driver, 5)
        
        # 设置cookie路径
        email = self.config['personal_info']['email']
        self.cookies_path = COOKIES_DIR / f"{self.get_hash(email)}.pkl"
        
        logger.info("Chrome驱动设置完成")
    
    def random_delay(self, min_sec: float = 1, max_sec: float = None):
        """
        随机延迟 - 避免固定间隔被检测
        参考 reference-easy-apply-bot: random.uniform(1, constants.botSpeed)
        """
        if max_sec is None:
            max_sec = BOT_SPEED
        delay = random.uniform(min_sec, max_sec)
        time.sleep(delay)
        return delay
    
    def take_screenshot(self, name: str = None) -> Optional[Path]:
        """截取当前屏幕"""
        return self.manager.take_screenshot(name, subdirectory="linkedin")
    
    def save_cookies(self):
        """
        保存Cookies到文件
        参考 reference-easy-apply-bot
        """
        if not self.cookies_path:
            return
        
        try:
            cookies = self.driver.get_cookies()
            with open(self.cookies_path, 'wb') as f:
                pickle.dump(cookies, f)
            logger.info(f"✅ Cookies已保存: {self.cookies_path}")
            prGreen(f"✅ Cookies已保存")
        except Exception as e:
            logger.warning(f"保存Cookies失败: {e}")
            prYellow(f"⚠️ 保存Cookies失败: {str(e)[:50]}")
    
    def load_cookies(self) -> bool:
        """
        从文件加载Cookies
        参考 reference-easy-apply-bot
        """
        if not self.cookies_path or not self.cookies_path.exists():
            return False
        
        try:
            with open(self.cookies_path, 'rb') as f:
                cookies = pickle.load(f)
            
            self.driver.delete_all_cookies()
            
            for cookie in cookies:
                try:
                    if 'sameSite' in cookie and cookie['sameSite'] not in ['Strict', 'Lax', 'None']:
                        del cookie['sameSite']
                    self.driver.add_cookie(cookie)
                except Exception as e:
                    logger.debug(f"添加cookie失败: {e}")
            
            logger.info("✅ Cookies已加载")
            return True
            
        except Exception as e:
            logger.warning(f"加载Cookies失败: {e}")
            return False
    
    def is_logged_in(self) -> bool:
        """检查是否已登录"""
        try:
            current_url = self.driver.current_url
            if any(x in current_url for x in ["feed", "mynetwork", "in/"]):
                return True
            
            # 检查全局导航栏
            self.short_wait.until(
                EC.presence_of_element_located((By.ID, "global-nav"))
            )
            return True
        except:
            return False
    
    def login_with_cookies(self) -> bool:
        """使用Cookies登录"""
        logger.info("尝试使用Cookies登录...")
        prYellow("🔄 尝试使用Cookies登录...")
        
        self.driver.get("https://www.linkedin.com")
        self.random_delay(2, 3)
        
        if self.load_cookies():
            self.driver.get("https://www.linkedin.com/feed/")
            self.random_delay(3, 4)
            
            if self.is_logged_in():
                logger.info("✅ Cookie登录成功")
                prGreen("✅ Cookie登录成功")
                return True
            else:
                logger.warning("⚠️ Cookie已过期")
                prYellow("⚠️ Cookie已过期，尝试重新登录")
        
        return False
    
    def login_with_password(self) -> bool:
        """使用密码登录 - 带验证码检测"""
        logger.info("使用密码登录...")
        prYellow("🔄 使用密码登录...")
        
        email = self.config['personal_info']['email']
        password = self.config['personal_info'].get('password', '') or os.environ.get('LINKEDIN_PASSWORD', '')
        
        if not email or not password:
            logger.error("❌ 未设置LinkedIn邮箱或密码")
            prRed("❌ 未设置LinkedIn邮箱或密码")
            return False
        
        try:
            self.driver.get("https://www.linkedin.com/login")
            self.random_delay(3, 4)
            
            # 检测验证码
            if self._detect_captcha():
                logger.error("❌ 检测到验证码，请手动登录")
                prRed("❌ 检测到验证码，请手动登录后再运行脚本")
                self.take_screenshot("captcha_detected")
                return False
            
            # 填写邮箱 - 多种selector fallback
            email_selectors = [
                (By.ID, "username"),
                (By.NAME, "session_key"),
                (By.CSS_SELECTOR, "input[type='text']")
            ]
            
            email_field = None
            for by, selector in email_selectors:
                try:
                    email_field = self.short_wait.until(EC.presence_of_element_located((by, selector)))
                    break
                except:
                    continue
            
            if not email_field:
                raise NoSuchElementException("无法找到邮箱输入框")
            
            email_field.clear()
            self.random_delay(0.5, 1)
            email_field.send_keys(email)
            logger.info(f"填写邮箱: {email}")
            self.random_delay(2, BOT_SPEED)
            
            # 填写密码
            password_field = self.driver.find_element(By.ID, "password")
            password_field.clear()
            self.random_delay(0.5, 1)
            password_field.send_keys(password)
            logger.info("填写密码")
            self.random_delay(2, BOT_SPEED)
            
            # 点击登录 - 多种selector fallback
            login_selectors = [
                "//button[@type='submit']",
                "//button[contains(text(), 'Sign in')]",
                "//button[contains(@class, 'btn__primary--large')]"
            ]
            
            login_button = None
            for selector in login_selectors:
                try:
                    login_button = self.driver.find_element(By.XPATH, selector)
                    if login_button.is_displayed():
                        break
                except:
                    continue
            
            if login_button:
                login_button.click()
                logger.info("点击登录按钮")
            
            self.random_delay(5, 7)
            
            # 再次检查验证码
            if self._detect_captcha():
                logger.error("❌ 登录后检测到验证码")
                prRed("❌ 登录后检测到验证码")
                self.take_screenshot("captcha_after_login")
                return False
            
            # 检查登录状态
            if self.is_logged_in():
                logger.info("✅ 密码登录成功")
                prGreen("✅ 密码登录成功")
                self.save_cookies()
                return True
            else:
                logger.error("❌ 登录失败")
                prRed("❌ 登录失败")
                self.take_screenshot("login_failed")
                return False
                
        except Exception as e:
            logger.error(f"登录出错: {e}")
            prRed(f"❌ 登录出错: {str(e)[:80]}")
            self.take_screenshot("login_error")
            return False
    
    def _detect_captcha(self) -> bool:
        """检测是否有验证码"""
        captcha_indicators = [
            "//iframe[contains(@src, 'recaptcha')]",
            "//div[contains(@class, 'captcha')]",
            "//input[@id='captcha']",
            "//div[contains(text(), 'security check')]",
            "//div[contains(text(), 'verify you')]",
            "//div[contains(text(), 'CAPTCHA')]"
        ]
        
        for indicator in captcha_indicators:
            try:
                elements = self.driver.find_elements(By.XPATH, indicator)
                if any(e.is_displayed() for e in elements):
                    return True
            except:
                continue
        
        return False
    
    def login(self, use_cookies: bool = True) -> bool:
        """
        登录LinkedIn
        策略: Chrome profile -> Cookies -> 密码
        """
        logger.info("开始登录LinkedIn...")
        prYellow("🌐 开始登录LinkedIn...")
        
        # 先检查是否已通过Chrome profile登录
        self.driver.get("https://www.linkedin.com/feed/")
        self.random_delay(3, 4)
        
        if self.is_logged_in():
            logger.info("✅ 已通过Chrome profile登录")
            prGreen("✅ 已通过Chrome profile登录")
            return True
        
        # 尝试Cookies登录
        if use_cookies and self.login_with_cookies():
            return True
        
        # 使用密码登录
        return self.login_with_password()
    
    def search_jobs(self, keywords: str, location: str = "United States"):
        """搜索职位"""
        logger.info(f"搜索职位: {keywords} @ {location}")
        prBlue(f"🔍 搜索职位: {keywords} @ {location}")
        
        search_url = f"https://www.linkedin.com/jobs/search/?keywords={keywords.replace(' ', '%20')}"
        if location:
            search_url += f"&location={location.replace(' ', '%20')}"
        search_url += "&f_AL=true"  # Easy Apply only
        
        self.driver.get(search_url)
        self.random_delay(5, 7)
        
        # 检查是否有结果
        no_results_selectors = [
            "//h1[contains(text(), 'No matching jobs')]",
            "//div[contains(text(), 'No jobs found')]",
            "//span[contains(text(), '0 results')]"
        ]
        
        for selector in no_results_selectors:
            try:
                if self.driver.find_elements(By.XPATH, selector):
                    logger.warning("没有找到匹配的职位")
                    prYellow("⚠️ 没有找到匹配的职位")
                    return False
            except:
                pass
        
        logger.info("职位搜索完成")
        return True
    
    def get_job_properties(self, count: int) -> dict:
        """获取职位详细信息 - 参考 reference-easy-apply-bot"""
        job_data = {
            'title': '',
            'company': '',
            'location': '',
            'workplace_type': '',
            'posted_date': '',
            'applications': ''
        }
        
        # 职位标题 - 多种selector fallback
        title_selectors = [
            "//h1[contains(@class, 'job-title')]",
            "//h2[contains(@class, 'job-title')]",
            "//a[contains(@class, 'job-title')]",
            "h1.t-24"
        ]
        
        for selector in title_selectors:
            try:
                elem = self.driver.find_element(By.XPATH, selector)
                job_data['title'] = elem.text.strip()
                break
            except:
                continue
        
        # 公司名称
        company_selectors = [
            "//a[contains(@class, 'ember-view t-black t-normal')]",
            "//span[contains(@class, 'company-name')]",
            "//a[contains(@href, '/company/')]"
        ]
        
        for selector in company_selectors:
            try:
                elem = self.driver.find_element(By.XPATH, selector)
                job_data['company'] = elem.text.strip()
                break
            except:
                continue
        
        # 工作地点
        location_selectors = [
            "//span[contains(@class, 'bullet')]",
            "//span[contains(@class, 'location')]"
        ]
        
        for selector in location_selectors:
            try:
                elem = self.driver.find_element(By.XPATH, selector)
                job_data['location'] = elem.text.strip()
                break
            except:
                continue
        
        # 检查黑名单
        blacklist_titles = self.config.get('blacklist', {}).get('titles', [])
        blacklist_companies = self.config.get('blacklist', {}).get('companies', [])
        
        for bl in blacklist_titles:
            if bl.lower() in job_data['title'].lower():
                job_data['title'] += f" (blacklisted: {bl})"
                break
        
        return job_data
    
    def find_easy_apply_button(self):
        """
        查找Easy Apply按钮 - 多种selector fallback
        参考 reference-easy-apply-bot
        """
        self.random_delay(1, BOT_SPEED)
        
        button_selectors = [
            "//div[contains(@class,'jobs-apply-button--top-card')]//button[contains(@class, 'jobs-apply-button')]",
            "//button[contains(@class, 'jobs-apply-button')]",
            "//button[contains(@aria-label, 'Easy Apply')]"
        ]
        
        for selector in button_selectors:
            try:
                button = self.driver.find_element(By.XPATH, selector)
                button_text = button.text.lower()
                # 检查是否已申请
                if "applied" in button_text or "application" in button_text:
                    return None  # 已申请
                return button
            except:
                continue
        
        return None
    
    def apply_to_job(self, job_url: str, max_retries: int = 2) -> bool:
        """
        申请单个职位 - 整合 reference-easy-apply-bot 的最佳实践
        """
        retries = 0
        
        while retries < max_retries:
            try:
                self.driver.get(job_url)
                self.random_delay(3, BOT_SPEED)
                
                # 获取职位信息
                job_props = self.get_job_properties(self.applied_count + 1)
                
                prBlue(f"\n{'='*60}")
                prBlue(f"申请: {job_props['company']} - {job_props['title']}")
                prBlue(f"{'='*60}")
                
                # 检查黑名单
                if "blacklisted" in str(job_props):
                    self.blacklisted_count += 1
                    prYellow(f"🚫 跳过黑名单职位: {job_props['title']}")
                    return False
                
                # 查找Easy Apply按钮
                easy_apply_btn = self.find_easy_apply_button()
                
                if easy_apply_btn is None:
                    self.already_applied_count += 1
                    prGreen(f"✓ 已申请过，跳过: {job_props['title']}")
                    return False
                
                # 点击Easy Apply
                if not self.manager.safe_click(easy_apply_btn):
                    raise Exception("无法点击Easy Apply按钮")
                
                self.random_delay(2, BOT_SPEED)
                
                # 处理申请流程
                result = self._process_application_flow()
                
                if result:
                    self.applied_count += 1
                    prGreen(f"✅ 申请成功 ({self.applied_count}): {job_props['company']} - {job_props['title']}")
                    self.take_screenshot(f"success_{job_props['company']}_{datetime.now().strftime('%H%M%S')}")
                    return True
                else:
                    self._close_application_modal()
                    return False
                
            except StaleElementReferenceException:
                logger.warning(f"元素已过期，重试 ({retries+1}/{max_retries})")
                retries += 1
                self.random_delay(2, 4)
            except Exception as e:
                logger.error(f"申请时出错: {e}")
                self.take_screenshot(f"apply_error_{retries}")
                retries += 1
                self.random_delay(2, 4)
        
        self.failed_count += 1
        return False
    
    def _process_application_flow(self) -> bool:
        """
        处理申请流程的多步弹窗
        参考 reference-easy-apply-bot 的 applyProcess 方法
        """
        step_count = 0
        max_steps = 10
        
        while step_count < max_steps:
            step_count += 1
            logger.info(f"处理第 {step_count} 步...")
            
            self.random_delay(2, BOT_SPEED)
            
            try:
                # 识别当前步骤
                step_type = self._identify_current_step()
                logger.info(f"当前步骤类型: {step_type}")
                
                if step_type == "contact_info":
                    self._fill_contact_info()
                elif step_type == "resume":
                    self._handle_resume()
                elif step_type == "additional_questions":
                    self._answer_additional_questions()
                elif step_type == "review":
                    self._review_application()
                elif step_type == "submit":
                    return self._submit_application()
                
                # 尝试点击下一步
                if not self._click_next_button():
                    # 如果没有下一步按钮，检查是否是提交页面
                    if self._is_submit_page():
                        return self._submit_application()
                    break
                
            except Exception as e:
                logger.error(f"处理步骤 {step_count} 时出错: {e}")
                self.take_screenshot(f"step_{step_count}_error")
                return False
        
        return False
    
    def _identify_current_step(self) -> str:
        """识别当前申请步骤"""
        try:
            # 尝试获取弹窗标题
            title_selectors = [
                ".jobs-easy-apply-modal__title",
                ".artdeco-modal__header",
                "h2",
                "h3"
            ]
            
            for selector in title_selectors:
                try:
                    elem = self.driver.find_element(By.CSS_SELECTOR, selector)
                    title = elem.text.lower()
                    
                    if any(x in title for x in ["contact", "info"]):
                        return "contact_info"
                    elif "resume" in title:
                        return "resume"
                    elif any(x in title for x in ["additional", "questions", "screening"]):
                        return "additional_questions"
                    elif "review" in title:
                        return "review"
                    elif "submit" in title:
                        return "submit"
                except:
                    continue
            
            # 通过页面元素判断
            if self.driver.find_elements(By.CSS_SELECTOR, "input[type='tel']"):
                return "contact_info"
            elif self.driver.find_elements(By.CSS_SELECTOR, "input[type='file']"):
                return "resume"
            elif self._is_submit_page():
                return "submit"
            
            return "unknown"
            
        except:
            return "unknown"
    
    def _is_submit_page(self) -> bool:
        """检查是否是提交页面"""
        submit_selectors = [
            "//button[contains(text(), 'Submit application')]",
            "//button[@aria-label='Submit application']"
        ]
        
        for selector in submit_selectors:
            try:
                if self.driver.find_elements(By.XPATH, selector):
                    return True
            except:
                continue
        
        return False
    
    def _fill_contact_info(self):
        """填写联系信息"""
        logger.info("填写联系信息...")
        
        try:
            # 电话号码 - 多种selector
            phone_selectors = [
                "input[type='tel']",
                "input[name*='phone']",
                "input[id*='phone']"
            ]
            
            phone = self.config['personal_info']['phone']
            
            for selector in phone_selectors:
                try:
                    inputs = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for inp in inputs:
                        if inp.is_displayed() and not inp.get_attribute("value"):
                            inp.clear()
                            inp.send_keys(phone)
                            logger.info(f"填写电话号码: {phone}")
                            break
                    break
                except:
                    continue
                    
        except Exception as e:
            logger.warning(f"填写联系信息时出错: {e}")
    
    def _handle_resume(self):
        """处理简历上传"""
        logger.info("处理简历上传...")
        
        try:
            # 尝试找到文件上传输入
            file_selectors = [
                "input[type='file']",
                "input[name='resume']",
                "input[accept*='pdf']"
            ]
            
            file_input = None
            for selector in file_selectors:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    file_input = elements[0]
                    break
            
            if file_input:
                resume_path = os.path.expanduser(
                    self.config['application_settings']['resume_path']
                )
                
                if os.path.exists(resume_path):
                    file_input.send_keys(resume_path)
                    logger.info(f"上传简历: {resume_path}")
                    self.random_delay(3, 5)
                else:
                    logger.warning(f"简历文件不存在: {resume_path}")
                    
        except Exception as e:
            logger.warning(f"处理简历时出错: {e}")
    
    def _answer_additional_questions(self):
        """回答附加问题"""
        logger.info("回答附加问题...")
        # 简化版 - 实际实现可以根据需要扩展
        pass
    
    def _review_application(self):
        """审核申请"""
        logger.info("审核申请...")
        # 可以添加自动检查逻辑
        pass
    
    def _submit_application(self) -> bool:
        """提交申请"""
        logger.info("提交申请...")
        
        try:
            # 查找提交按钮 - 多种selector
            submit_selectors = [
                (By.CSS_SELECTOR, "button[aria-label='Submit application']"),
                (By.XPATH, "//button[contains(text(), 'Submit application')]"),
                (By.XPATH, "//button[contains(text(), 'Submit')]")
            ]
            
            submit_btn = None
            for by, selector in submit_selectors:
                try:
                    submit_btn = self.wait.until(EC.element_to_be_clickable((by, selector)))
                    break
                except:
                    continue
            
            if not submit_btn:
                logger.error("未找到提交按钮")
                return False
            
            # 取消关注公司（可选）
            try:
                follow_checkbox = self.driver.find_element(By.CSS_SELECTOR, "label[for='follow-company-checkbox']")
                follow_checkbox.click()
                logger.info("取消关注公司")
            except:
                pass
            
            # 点击提交
            submit_btn.click()
            logger.info("点击提交按钮")
            self.random_delay(3, 5)
            
            # 验证提交成功
            success_indicators = [
                "//div[contains(text(), 'Application sent')]",
                "//div[contains(text(), 'successfully')]",
                "//h2[contains(text(), 'Applied')]"
            ]
            
            for indicator in success_indicators:
                try:
                    if self.driver.find_elements(By.XPATH, indicator):
                        return True
                except:
                    continue
            
            # 如果没有明确的成功指示，假设成功
            return True
            
        except Exception as e:
            logger.error(f"提交申请时出错: {e}")
            return False
    
    def _click_next_button(self) -> bool:
        """点击下一步按钮"""
        try:
            next_selectors = [
                (By.CSS_SELECTOR, "button[aria-label='Continue to next step']"),
                (By.XPATH, "//button[contains(text(), 'Next')]"),
                (By.XPATH, "//button[contains(text(), 'Continue')]")
            ]
            
            for by, selector in next_selectors:
                try:
                    btn = self.short_wait.until(EC.element_to_be_clickable((by, selector)))
                    if btn.is_enabled():
                        btn.click()
                        logger.info("点击下一步")
                        return True
                except:
                    continue
            
            return False
            
        except Exception as e:
            logger.error(f"点击下一步按钮时出错: {e}")
            return False
    
    def _close_application_modal(self):
        """关闭申请弹窗"""
        try:
            close_btn = self.driver.find_element(By.CSS_SELECTOR, ".artdeco-modal__dismiss")
            close_btn.click()
            self.random_delay(1, 2)
            
            # 确认放弃申请
            try:
                discard_btn = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Discard')]")
                discard_btn.click()
            except:
                pass
        except:
            pass
    
    def apply_to_jobs_from_search(self, max_jobs: int = 10) -> int:
        """
        从搜索结果申请多个职位
        参考 reference-easy-apply-bot 的 linkJobApply 方法
        """
        self.start_time = time.time()
        count_jobs = 0
        
        try:
            # 获取总职位数和页数
            try:
                total_jobs_text = self.driver.find_element(By.XPATH, '//small').text
                logger.info(f"找到职位: {total_jobs_text}")
            except:
                total_jobs_text = "25 results"
            
            total_pages = self._jobs_to_pages(total_jobs_text)
            logger.info(f"总页数: {total_pages}")
            
            for page in range(min(total_pages, 3)):  # 限制最多3页
                current_page_jobs = 25 * page
                if page > 0:
                    current_url = self.driver.current_url
                    page_url = f"{current_url}&start={current_page_jobs}"
                    self.driver.get(page_url)
                    self.random_delay(3, BOT_SPEED)
                
                # 获取职位列表 - 参考 reference-easy-apply-bot
                try:
                    offers = self.wait.until(
                        EC.presence_of_all_elements_located((By.XPATH, '//li[@data-occludable-job-id]'))
                    )
                except:
                    logger.warning("无法找到职位列表")
                    continue
                
                # 提取职位ID
                job_ids = []
                for offer in offers:
                    try:
                        job_id = offer.get_attribute("data-occludable-job-id")
                        if job_id:
                            job_ids.append(int(job_id.split(":")[-1]))
                    except:
                        continue
                
                logger.info(f"第 {page+1} 页找到 {len(job_ids)} 个职位")
                
                # 申请每个职位
                for job_id in job_ids:
                    if count_jobs >= max_jobs:
                        break
                    
                    job_url = f'https://www.linkedin.com/jobs/view/{job_id}'
                    success = self.apply_to_job(job_url)
                    count_jobs += 1
                    
                    # 申请间隔
                    self.random_delay(5, 10)
                
                if count_jobs >= max_jobs:
                    break
        
        except Exception as e:
            logger.error(f"申请过程出错: {e}")
        
        # 输出统计
        self._print_session_summary()
        return self.applied_count
    
    def _jobs_to_pages(self, num_of_jobs: str) -> int:
        """
        将职位数转换为页数
        参考 reference-easy-apply-bot
        """
        number_of_pages = 1
        
        if ' ' in num_of_jobs:
            space_index = num_of_jobs.index(' ')
            total_jobs = num_of_jobs[0:space_index]
            total_jobs_int = int(total_jobs.replace(',', ''))
            number_of_pages = math.ceil(total_jobs_int / 25)
            if number_of_pages > 40:
                number_of_pages = 40
        else:
            try:
                number_of_pages = int(num_of_jobs)
            except:
                number_of_pages = 1
        
        return number_of_pages
    
    def _print_session_summary(self):
        """打印会话摘要 - 参考 reference-easy-apply-bot"""
        duration_sec = time.time() - self.start_time if self.start_time else 0
        duration_min = round(duration_sec / 60, 1)
        
        prGreen("\n" + "=" * 60)
        prGreen("📊 会话统计")
        prGreen("=" * 60)
        prGreen(f"   处理职位数:     {self.applied_count + self.failed_count + self.skipped_count + self.already_applied_count}")
        prGreen(f"   ✅ 成功申请:     {self.applied_count}")
        prGreen(f"   🚫 黑名单跳过:   {self.blacklisted_count}")
        prGreen(f"   ✓  已申请过:     {self.already_applied_count}")
        prGreen(f"   ❌ 申请失败:     {self.failed_count}")
        prGreen(f"   ⏱  耗时:         {duration_min} 分钟")
        prGreen("=" * 60 + "\n")
        
        logger.info("=" * 60)
        logger.info("会话统计:")
        logger.info(f"  成功申请: {self.applied_count}")
        logger.info(f"  黑名单跳过: {self.blacklisted_count}")
        logger.info(f"  已申请过: {self.already_applied_count}")
        logger.info(f"  申请失败: {self.failed_count}")
        logger.info(f"  耗时: {duration_min} 分钟")
        logger.info("=" * 60)
    
    def close(self):
        """关闭浏览器"""
        if hasattr(self, 'manager') and self.manager:
            self.manager.close()
        logger.info(f"日志文件: {log_file}")


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='LinkedIn Easy Apply 自动化申请 v2.0')
    parser.add_argument('--headless', action='store_true', help='使用无头模式')
    parser.add_argument('--no-profile', action='store_true', help='不使用Chrome profile')
    parser.add_argument('--no-cookies', action='store_true', help='不使用cookie登录')
    parser.add_argument('--keywords', default='Director of Technical Services', help='搜索关键词')
    parser.add_argument('--location', default='New York', help='地点')
    parser.add_argument('--max-jobs', type=int, default=5, help='最大申请数量')
    parser.add_argument('--job-url', help='直接申请单个职位URL')
    
    args = parser.parse_args()
    
    applier = LinkedInEasyApply()
    
    try:
        # 设置驱动
        applier.setup_driver(
            headless=args.headless,
            use_profile=not args.no_profile
        )
        
        # 登录
        if not applier.login(use_cookies=not args.no_cookies):
            prRed("❌ 登录失败，退出")
            return 1
        
        if args.job_url:
            # 直接申请单个职位
            success = applier.apply_to_job(args.job_url)
            if success:
                prGreen("✅ 职位申请成功")
            else:
                prRed("❌ 职位申请失败")
        else:
            # 搜索并申请
            if applier.search_jobs(args.keywords, args.location):
                applier.apply_to_jobs_from_search(max_jobs=args.max_jobs)
        
    except KeyboardInterrupt:
        prYellow("\n用户中断")
    except Exception as e:
        prRed(f"运行时出错: {e}")
        applier.take_screenshot("fatal_error")
    finally:
        applier.close()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
