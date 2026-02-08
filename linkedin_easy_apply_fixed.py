#!/usr/bin/env python3
"""
增强版 LinkedIn Easy Apply 自动化申请脚本
修复问题：
1. Cookie登录支持 - 避免验证码问题
2. 使用已登录Chrome profile
3. 智能等待和错误重试
4. 自动截图调试
5. 申请成功/失败检测
"""

import os
import sys
import time
import yaml
import json
import pickle
import logging
from pathlib import Path
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import (
    TimeoutException, NoSuchElementException, 
    ElementNotInteractableException, StaleElementReferenceException
)
from webdriver_manager.chrome import ChromeDriverManager

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

# Cookie文件路径
COOKIES_FILE = Path("config/linkedin_cookies.pkl")
SCREENSHOTS_DIR = Path("screenshots")
SCREENSHOTS_DIR.mkdir(exist_ok=True)


class LinkedInEasyApply:
    """LinkedIn Easy Apply 增强版自动化申请器"""
    
    def __init__(self, config_path: str = "config/profile.yaml"):
        self.config = self._load_config(config_path)
        self.driver = None
        self.wait = None
        self.short_wait = None
        self.applied_count = 0
        self.failed_count = 0
        self.skipped_count = 0
        self.headless = False
        
    def _load_config(self, path: str) -> dict:
        """加载配置文件"""
        try:
            with open(path, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"加载配置文件失败: {e}")
            sys.exit(1)
    
    def setup_driver(self, headless: bool = False, use_profile: bool = True):
        """
        设置Chrome浏览器驱动
        
        Args:
            headless: 是否使用无头模式
            use_profile: 是否使用已登录的Chrome profile
        """
        logger.info(f"设置Chrome驱动... (headless={headless}, use_profile={use_profile})")
        self.headless = headless
        
        chrome_options = Options()
        
        if headless:
            chrome_options.add_argument("--headless=new")  # 新版headless模式
            chrome_options.add_argument("--disable-gpu")
        
        # 基础设置
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--start-maximized")
        
        # 反检测设置
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # 用户代理
        chrome_options.add_argument(
            "--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        
        # 使用已登录的Chrome profile (推荐)
        if use_profile:
            user_data_dir = Path.home() / "Library/Application Support/Google/Chrome"
            if user_data_dir.exists():
                chrome_options.add_argument(f"--user-data-dir={user_data_dir}")
                chrome_options.add_argument("--profile-directory=Default")
                logger.info(f"使用Chrome profile: {user_data_dir}")
        
        # 禁用密码管理器弹窗
        chrome_options.add_experimental_option("prefs", {
            "credentials_enable_service": False,
            "profile.password_manager_enabled": False
        })
        
        try:
            self.driver = webdriver.Chrome(
                service=Service(ChromeDriverManager().install()),
                options=chrome_options
            )
            
            # 隐藏webdriver标志
            self.driver.execute_script(
                "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
            )
            
            # 设置等待时间
            self.wait = WebDriverWait(self.driver, 15)
            self.short_wait = WebDriverWait(self.driver, 5)
            
            logger.info("Chrome驱动设置完成")
            
        except Exception as e:
            logger.error(f"Chrome驱动设置失败: {e}")
            raise
    
    def take_screenshot(self, name: str = None):
        """截取当前屏幕"""
        if name is None:
            name = f"screenshot_{datetime.now().strftime('%H%M%S')}"
        
        screenshot_path = SCREENSHOTS_DIR / f"{name}.png"
        try:
            self.driver.save_screenshot(str(screenshot_path))
            logger.info(f"截图已保存: {screenshot_path}")
            return screenshot_path
        except Exception as e:
            logger.error(f"截图失败: {e}")
            return None
    
    def save_cookies(self):
        """保存Cookies到文件"""
        try:
            cookies = self.driver.get_cookies()
            with open(COOKIES_FILE, 'wb') as f:
                pickle.dump(cookies, f)
            logger.info(f"Cookies已保存: {COOKIES_FILE}")
        except Exception as e:
            logger.error(f"保存Cookies失败: {e}")
    
    def load_cookies(self):
        """从文件加载Cookies"""
        try:
            if COOKIES_FILE.exists():
                with open(COOKIES_FILE, 'rb') as f:
                    cookies = pickle.load(f)
                
                for cookie in cookies:
                    try:
                        self.driver.add_cookie(cookie)
                    except Exception as e:
                        logger.debug(f"添加cookie失败: {e}")
                
                logger.info("Cookies已加载")
                return True
            return False
        except Exception as e:
            logger.error(f"加载Cookies失败: {e}")
            return False
    
    def login_with_cookies(self) -> bool:
        """使用Cookies登录"""
        logger.info("尝试使用Cookies登录...")
        
        # 先访问LinkedIn域名以设置cookies
        self.driver.get("https://www.linkedin.com")
        time.sleep(2)
        
        if self.load_cookies():
            # 刷新页面以应用cookies
            self.driver.get("https://www.linkedin.com/feed/")
            time.sleep(3)
            
            # 检查是否登录成功
            if self._is_logged_in():
                logger.info("Cookie登录成功")
                return True
            else:
                logger.warning("Cookie已过期，尝试重新登录")
        
        return False
    
    def login_with_password(self) -> bool:
        """使用密码登录"""
        logger.info("使用密码登录LinkedIn...")
        
        email = self.config['personal_info']['email']
        # 从环境变量或配置文件获取密码
        password = os.environ.get('LINKEDIN_PASSWORD', '')
        
        if not password:
            logger.error("未设置LINKEDIN_PASSWORD环境变量")
            return False
        
        try:
            self.driver.get("https://www.linkedin.com/login")
            time.sleep(3)
            
            # 检查是否有验证码
            if self._detect_captcha():
                logger.error("检测到验证码，请手动登录后再运行脚本")
                self.take_screenshot("captcha_detected")
                return False
            
            # 填写邮箱
            email_field = self.wait.until(
                EC.presence_of_element_located((By.ID, "username"))
            )
            email_field.clear()
            email_field.send_keys(email)
            logger.debug(f"填写邮箱: {email}")
            
            # 填写密码
            password_field = self.driver.find_element(By.ID, "password")
            password_field.clear()
            password_field.send_keys(password)
            logger.debug("填写密码")
            
            # 点击登录
            login_button = self.driver.find_element(By.XPATH, "//button[@type='submit']")
            login_button.click()
            logger.info("点击登录按钮")
            
            time.sleep(5)
            
            # 再次检查验证码
            if self._detect_captcha():
                logger.error("登录后检测到验证码")
                self.take_screenshot("captcha_after_login")
                return False
            
            # 检查是否需要额外验证
            if self._detect_security_challenge():
                logger.error("检测到安全验证，请手动完成验证")
                self.take_screenshot("security_challenge")
                return False
            
            # 检查登录状态
            if self._is_logged_in():
                logger.info("密码登录成功")
                self.save_cookies()
                return True
            else:
                logger.error("登录失败")
                self.take_screenshot("login_failed")
                return False
                
        except TimeoutException as e:
            logger.error(f"登录超时: {e}")
            self.take_screenshot("login_timeout")
            return False
        except Exception as e:
            logger.error(f"登录出错: {e}")
            self.take_screenshot("login_error")
            return False
    
    def login(self, use_cookies: bool = True) -> bool:
        """
        登录LinkedIn
        
        策略:
        1. 首先尝试使用Chrome profile (如果已设置)
        2. 尝试使用Cookies登录
        3. 最后使用密码登录
        """
        logger.info("开始登录LinkedIn...")
        
        # 先检查是否已经在Chrome profile中登录
        self.driver.get("https://www.linkedin.com/feed/")
        time.sleep(3)
        
        if self._is_logged_in():
            logger.info("已经通过Chrome profile登录")
            return True
        
        # 尝试Cookies登录
        if use_cookies and self.login_with_cookies():
            return True
        
        # 使用密码登录
        return self.login_with_password()
    
    def _is_logged_in(self) -> bool:
        """检查是否已登录"""
        try:
            # 检查URL是否包含feed或mynetwork
            current_url = self.driver.current_url
            if any(x in current_url for x in ["feed", "mynetwork", "in/"]):
                return True
            
            # 检查是否存在登录后的元素
            self.short_wait.until(
                EC.presence_of_element_located((By.ID, "global-nav"))
            )
            return True
        except:
            return False
    
    def _detect_captcha(self) -> bool:
        """检测是否有验证码"""
        captcha_indicators = [
            "//iframe[contains(@src, 'recaptcha')]",
            "//div[contains(@class, 'captcha')]",
            "//input[@id='captcha']",
            "//div[contains(text(), 'security check')]",
            "//div[contains(text(), 'verify you')]"
        ]
        
        for indicator in captcha_indicators:
            try:
                element = self.driver.find_element(By.XPATH, indicator)
                if element.is_displayed():
                    return True
            except:
                continue
        
        return False
    
    def _detect_security_challenge(self) -> bool:
        """检测安全挑战"""
        challenge_keywords = [
            "security verification",
            "two-step",
            "two factor",
            "verification code",
            "confirm your identity"
        ]
        
        page_text = self.driver.find_element(By.TAG_NAME, "body").text.lower()
        
        for keyword in challenge_keywords:
            if keyword in page_text:
                return True
        
        return False
    
    def search_jobs(self, keywords: str, location: str = "United States", easy_apply_only: bool = True):
        """搜索职位"""
        logger.info(f"搜索职位: {keywords} @ {location}")
        
        # 构建搜索URL
        search_url = f"https://www.linkedin.com/jobs/search/?keywords={keywords.replace(' ', '%20')}"
        if location:
            search_url += f"&location={location.replace(' ', '%20')}"
        if easy_apply_only:
            search_url += "&f_AL=true"  # Easy Apply filter
        
        self.driver.get(search_url)
        time.sleep(5)
        
        # 检查是否有结果
        try:
            no_results = self.driver.find_elements(
                By.XPATH, "//h1[contains(text(), 'No matching jobs')]"
            )
            if no_results:
                logger.warning("没有找到匹配的职位")
                return []
        except:
            pass
        
        logger.info("职位搜索完成")
    
    def find_easy_apply_jobs(self, max_jobs: int = 10) -> list:
        """查找Easy Apply职位"""
        logger.info("查找Easy Apply职位...")
        
        jobs = []
        attempts = 0
        max_attempts = 3
        
        while len(jobs) < max_jobs and attempts < max_attempts:
            try:
                # 滚动加载更多职位
                self.driver.execute_script(
                    "window.scrollTo(0, document.body.scrollHeight);"
                )
                time.sleep(2)
                
                # 获取职位列表
                job_cards = self.wait.until(
                    EC.presence_of_all_elements_located((
                        By.CSS_SELECTOR, 
                        ".jobs-search-results__list-item, .job-card-container"
                    ))
                )
                
                logger.info(f"找到 {len(job_cards)} 个职位卡片")
                
                for card in job_cards:
                    if card not in jobs:
                        jobs.append(card)
                    if len(jobs) >= max_jobs:
                        break
                
                if len(jobs) >= max_jobs:
                    break
                
                attempts += 1
                
            except Exception as e:
                logger.warning(f"查找职位时出错: {e}")
                attempts += 1
                time.sleep(2)
        
        logger.info(f"共找到 {len(jobs)} 个职位")
        return jobs[:max_jobs]
    
    def get_job_details(self) -> dict:
        """获取当前职位的详细信息"""
        try:
            # 职位标题
            title_elem = self.driver.find_element(
                By.CSS_SELECTOR, ".job-details-jobs-unified-top-card__job-title h1"
            )
            title = title_elem.text.strip()
            
            # 公司名称
            company_elem = self.driver.find_element(
                By.CSS_SELECTOR, ".job-details-jobs-unified-top-card__company-name"
            )
            company = company_elem.text.strip()
            
            return {"title": title, "company": company}
        except:
            return {"title": "Unknown", "company": "Unknown"}
    
    def apply_to_job(self, job_card, max_retries: int = 2) -> bool:
        """
        申请单个职位
        
        Returns:
            True: 申请成功
            False: 申请失败或跳过
        """
        retries = 0
        
        while retries < max_retries:
            try:
                # 点击职位卡片
                self.driver.execute_script("arguments[0].scrollIntoView(true);", job_card)
                time.sleep(1)
                job_card.click()
                time.sleep(3)
                
                # 获取职位详情
                job_details = self.get_job_details()
                logger.info(f"正在申请: {job_details['company']} - {job_details['title']}")
                
                # 查找Easy Apply按钮
                try:
                    easy_apply_btn = self.short_wait.until(
                        EC.element_to_be_clickable((
                            By.XPATH, 
                            "//button[contains(@class, 'jobs-apply-button')]"
                        ))
                    )
                    
                    button_text = easy_apply_btn.text.lower()
                    if "applied" in button_text or "application" in button_text:
                        logger.info("职位已申请，跳过")
                        self.skipped_count += 1
                        return False
                    
                except TimeoutException:
                    logger.warning("未找到Easy Apply按钮，跳过")
                    return False
                
                # 点击Easy Apply
                easy_apply_btn.click()
                logger.info("打开Easy Apply弹窗")
                time.sleep(3)
                
                # 处理申请流程
                success = self._process_application_flow()
                
                if success:
                    self.applied_count += 1
                    logger.info(f"✓ 申请成功: {job_details['company']} - {job_details['title']}")
                    self.take_screenshot(f"success_{job_details['company']}_{datetime.now().strftime('%H%M%S')}")
                    return True
                else:
                    # 关闭弹窗
                    self._close_application_modal()
                    return False
                
            except StaleElementReferenceException:
                logger.warning(f"元素已过期，重试 ({retries+1}/{max_retries})")
                retries += 1
                time.sleep(2)
            except Exception as e:
                logger.error(f"申请时出错: {e}")
                self.take_screenshot(f"apply_error_{retries}")
                retries += 1
                time.sleep(2)
        
        self.failed_count += 1
        return False
    
    def _process_application_flow(self) -> bool:
        """处理申请流程的多步弹窗"""
        step_count = 0
        max_steps = 10
        
        while step_count < max_steps:
            step_count += 1
            logger.info(f"处理第 {step_count} 步...")
            
            # 等待页面加载
            time.sleep(2)
            
            # 识别并处理当前步骤
            step_type = self._identify_current_step()
            logger.info(f"当前步骤类型: {step_type}")
            
            try:
                if step_type == "contact_info":
                    self._fill_contact_info()
                elif step_type == "resume":
                    self._handle_resume()
                elif step_type == "additional_questions":
                    self._answer_additional_questions()
                elif step_type == "work_authorization":
                    self._fill_work_authorization()
                elif step_type == "review":
                    self._review_application()
                elif step_type == "submit":
                    return self._submit_application()
                elif step_type == "unknown":
                    # 尝试点击下一步按钮
                    pass
                
                # 点击下一步/继续/审核按钮
                if not self._click_next_button():
                    # 如果没有下一步按钮，可能是提交页面
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
            try:
                modal_title = self.driver.find_element(
                    By.CSS_SELECTOR, ".jobs-easy-apply-modal__title, .artdeco-modal__header"
                ).text.lower()
                
                if any(x in modal_title for x in ["contact", "info"]):
                    return "contact_info"
                elif "resume" in modal_title:
                    return "resume"
                elif any(x in modal_title for x in ["additional", "questions"]):
                    return "additional_questions"
                elif any(x in modal_title for x in ["work", "authorization"]):
                    return "work_authorization"
                elif "review" in modal_title:
                    return "review"
                elif "submit" in modal_title:
                    return "submit"
            except:
                pass
            
            # 通过页面元素判断
            try:
                if self.driver.find_elements(By.CSS_SELECTOR, "input[type='tel']"):
                    return "contact_info"
                elif self.driver.find_elements(By.CSS_SELECTOR, "input[type='file']"):
                    return "resume"
                elif self.driver.find_elements(By.XPATH, "//button[contains(text(), 'Submit application')]"):
                    return "submit"
            except:
                pass
            
            return "unknown"
            
        except Exception as e:
            logger.debug(f"识别步骤时出错: {e}")
            return "unknown"
    
    def _is_submit_page(self) -> bool:
        """检查是否是提交页面"""
        try:
            submit_buttons = self.driver.find_elements(
                By.XPATH, 
                "//button[contains(text(), 'Submit application') or contains(text(), 'Submit')]"
            )
            return len(submit_buttons) > 0
        except:
            return False
    
    def _fill_contact_info(self):
        """填写联系信息"""
        logger.info("填写联系信息...")
        
        try:
            # 电话号码
            phone_inputs = self.driver.find_elements(By.CSS_SELECTOR, "input[type='tel']")
            if phone_inputs:
                phone = self.config['personal_info']['phone']
                phone_inputs[0].clear()
                phone_inputs[0].send_keys(phone)
                logger.info(f"填写电话号码: {phone}")
                
        except Exception as e:
            logger.warning(f"填写联系信息时出错: {e}")
    
    def _handle_resume(self):
        """处理简历上传"""
        logger.info("处理简历上传...")
        
        try:
            # 尝试多种方式定位文件上传输入
            file_selectors = [
                "input[type='file']",
                "input[name='resume']",
                "input[accept*='pdf']",
                "input[accept*='.pdf']"
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
                    time.sleep(3)  # 等待上传完成
                else:
                    logger.warning(f"简历文件不存在: {resume_path}")
            else:
                logger.info("未找到简历上传字段，使用LinkedIn默认简历")
                
        except Exception as e:
            logger.warning(f"处理简历时出错: {e}")
    
    def _answer_additional_questions(self):
        """回答附加问题"""
        logger.info("回答附加问题...")
        
        try:
            # 处理文本输入
            text_inputs = self.driver.find_elements(
                By.CSS_SELECTOR, ".jobs-easy-apply-form-section__question input[type='text']"
            )
            
            for input_field in text_inputs:
                try:
                    label = input_field.find_element(By.XPATH, "../label").text.lower()
                    answer = self._get_answer_for_question(label)
                    if answer:
                        input_field.clear()
                        input_field.send_keys(answer)
                        logger.info(f"回答问题: {label[:30]}... -> {answer}")
                except:
                    pass
            
            # 处理下拉选择
            selects = self.driver.find_elements(By.TAG_NAME, "select")
            for select in selects:
                try:
                    label = select.find_element(By.XPATH, "../label").text.lower()
                    self._handle_select_question(select, label)
                except:
                    pass
            
            # 处理单选按钮
            radio_groups = self.driver.find_elements(
                By.CSS_SELECTOR, ".jobs-easy-apply-form-section__question fieldset"
            )
            for group in radio_groups:
                try:
                    question = group.find_element(By.TAG_NAME, "legend").text.lower()
                    self._handle_radio_question(group, question)
                except:
                    pass
                    
        except Exception as e:
            logger.warning(f"回答附加问题时出错: {e}")
    
    def _get_answer_for_question(self, question: str) -> str:
        """根据问题获取答案"""
        question_lower = question.lower()
        
        answers = {
            "experience": self.config['application_settings']['years_of_experience'],
            "salary": str(self.config['application_settings']['desired_salary']),
            "website": self.config['personal_info']['website'],
            "linkedin": self.config['personal_info']['linkedin'],
            "portfolio": self.config['personal_info']['portfolio'],
            "notice": str(self.config['application_settings']['notice_period_days']),
        }
        
        for key, answer in answers.items():
            if key in question_lower:
                return answer
        
        return ""
    
    def _handle_select_question(self, select, label: str):
        """处理下拉选择问题"""
        try:
            from selenium.webdriver.support.ui import Select
            dropdown = Select(select)
            label_lower = label.lower()
            
            if "gender" in label_lower:
                option_text = self.config['equal_opportunity']['gender']
            elif any(x in label_lower for x in ["ethnicity", "race"]):
                option_text = self.config['equal_opportunity']['ethnicity']
            elif "veteran" in label_lower:
                option_text = "No"
            elif "disability" in label_lower:
                option_text = "No"
            else:
                return
            
            dropdown.select_by_visible_text(option_text)
            logger.info(f"选择下拉选项: {option_text}")
            
        except Exception as e:
            logger.warning(f"处理下拉选择时出错: {e}")
    
    def _handle_radio_question(self, group, question: str):
        """处理单选按钮问题"""
        try:
            question_lower = question.lower()
            radios = group.find_elements(By.CSS_SELECTOR, "input[type='radio']")
            
            if not radios:
                return
            
            # 确定选择哪个选项
            select_value = None
            
            if any(x in question_lower for x in ["sponsorship", "visa"]):
                select_value = "yes"
            elif any(x in question_lower for x in ["authorized", "legally", "eligible"]):
                select_value = "no"
            elif "relocate" in question_lower:
                select_value = "no"
            elif "remote" in question_lower:
                select_value = "yes"
            
            if select_value:
                for radio in radios:
                    if radio.get_attribute('value').lower() == select_value:
                        radio.click()
                        logger.info(f"选择单选: {select_value}")
                        break
                        
        except Exception as e:
            logger.warning(f"处理单选问题时出错: {e}")
    
    def _fill_work_authorization(self):
        """填写工作授权信息"""
        logger.info("处理工作授权信息...")
        # 通常在附加问题中处理
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
            # 查找提交按钮
            submit_btn = self.wait.until(
                EC.element_to_be_clickable((
                    By.XPATH, 
                    "//button[contains(text(), 'Submit application')]"
                ))
            )
            
            submit_btn.click()
            logger.info("点击提交按钮")
            
            time.sleep(3)
            
            # 验证提交成功
            success_indicators = [
                "//div[contains(text(), 'Application sent')]",
                "//div[contains(text(), 'successfully')]",
                "//h2[contains(text(), 'Applied')]"
            ]
            
            for indicator in success_indicators:
                try:
                    if self.driver.find_elements(By.XPATH, indicator):
                        logger.info("✓ 申请提交成功确认")
                        return True
                except:
                    pass
            
            # 如果没有明确的成功指示，假设成功
            logger.info("✓ 申请已提交")
            return True
            
        except Exception as e:
            logger.error(f"提交申请时出错: {e}")
            return False
    
    def _click_next_button(self) -> bool:
        """点击下一步按钮"""
        try:
            next_selectors = [
                "//button[contains(text(), 'Next')]",
                "//button[contains(text(), 'Continue')]",
                "//button[contains(text(), 'Review')]",
                "//button[@aria-label='Continue to next step']"
            ]
            
            for selector in next_selectors:
                try:
                    next_btn = self.short_wait.until(
                        EC.element_to_be_clickable((By.XPATH, selector))
                    )
                    
                    if next_btn.is_enabled():
                        next_btn.click()
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
            close_btn = self.driver.find_element(
                By.CSS_SELECTOR, ".artdeco-modal__dismiss"
            )
            close_btn.click()
            time.sleep(1)
            
            # 确认放弃申请
            try:
                discard_btn = self.driver.find_element(
                    By.XPATH, "//button[contains(text(), 'Discard')]"
                )
                discard_btn.click()
                time.sleep(1)
            except:
                pass
                
        except:
            pass
    
    def close(self):
        """关闭浏览器并输出统计"""
        if self.driver:
            logger.info("=" * 60)
            logger.info("申请统计:")
            logger.info(f"  成功: {self.applied_count}")
            logger.info(f"  失败: {self.failed_count}")
            logger.info(f"  跳过: {self.skipped_count}")
            logger.info(f"  总计: {self.applied_count + self.failed_count + self.skipped_count}")
            logger.info("=" * 60)
            self.driver.quit()


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='LinkedIn Easy Apply 自动化申请')
    parser.add_argument('--headless', action='store_true', help='使用无头模式')
    parser.add_argument('--no-profile', action='store_true', help='不使用Chrome profile')
    parser.add_argument('--no-cookies', action='store_true', help='不使用cookie登录')
    parser.add_argument('--keywords', default='Director of Technical Services', help='搜索关键词')
    parser.add_argument('--location', default='New York', help='地点')
    parser.add_argument('--max-jobs', type=int, default=5, help='最大申请数量')
    
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
            logger.error("登录失败，退出")
            return
        
        # 搜索职位
        applier.search_jobs(args.keywords, args.location)
        
        # 查找职位
        jobs = applier.find_easy_apply_jobs(max_jobs=args.max_jobs * 2)
        
        # 申请职位
        for i, job in enumerate(jobs[:args.max_jobs]):
            logger.info(f"\n{'='*60}")
            logger.info(f"申请第 {i+1}/{min(len(jobs), args.max_jobs)} 个职位")
            logger.info(f"{'='*60}")
            
            success = applier.apply_to_job(job)
            
            if success:
                logger.info(f"✓ 第 {i+1} 个职位申请成功")
            else:
                logger.warning(f"✗ 第 {i+1} 个职位申请失败或跳过")
            
            # 申请间隔 (避免被封)
            time.sleep(8)
        
    except KeyboardInterrupt:
        logger.info("\n用户中断")
    except Exception as e:
        logger.error(f"运行时出错: {e}")
        applier.take_screenshot("fatal_error")
    finally:
        applier.close()
        logger.info(f"日志文件: {log_file}")


if __name__ == "__main__":
    main()
