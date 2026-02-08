#!/usr/bin/env python3
"""
Greenhouse ATS 自动化申请脚本 - 增强版 v2.0
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
from typing import List, Optional, Dict, Tuple

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
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
log_file = log_dir / f"greenhouse_apply_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 目录设置
COOKIES_DIR = Path("cookies")
COOKIES_DIR.mkdir(exist_ok=True)
SCREENSHOTS_DIR = Path("screenshots")
SCREENSHOTS_DIR.mkdir(exist_ok=True)

# Bot 速度设置 (参考 reference-easy-apply-bot)
FAST = 2
MEDIUM = 3
SLOW = 5
BOT_SPEED = SLOW


class GreenhouseAutoApply:
    """
    Greenhouse ATS 增强版自动化申请器
    整合 reference-easy-apply-bot 的最佳实践
    """
    
    def __init__(self, config_path: str = "config/profile.yaml"):
        self.config = self._load_config(config_path)
        self.driver = None
        self.wait = None
        self.short_wait = None
        self.headless = False
        self.cookies_path = None
        self.start_time = None
        self.applied_count = 0
        self.failed_count = 0
        
    def _load_config(self, path: str) -> dict:
        """加载配置文件"""
        try:
            possible_paths = [
                Path(path),
                Path(__file__).parent / path,
                Path.home() / ".openclaw" / "workspace" / "auto-job-apply" / path
            ]
            
            for config_path in possible_paths:
                if config_path.exists():
                    with open(config_path, 'r') as f:
                        return yaml.safe_load(f)
            
            logger.warning(f"配置文件未找到: {path}，使用默认配置")
            return self._get_default_config()
            
        except Exception as e:
            logger.error(f"加载配置文件失败: {e}")
            return self._get_default_config()
    
    def _get_default_config(self) -> dict:
        """获取默认配置"""
        return {
            'personal_info': {
                'first_name': 'Tommy',
                'last_name': 'Wu',
                'email': os.environ.get('EMAIL', 'tommy.wu@nyu.edu'),
                'phone': os.environ.get('PHONE', '917-742-4303'),
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
            'equal_opportunity': {
                'gender': 'Male',
                'ethnicity': 'Asian',
                'veteran_status': 'No',
                'disability_status': 'No'
            }
        }
    
    def get_hash(self, string: str) -> str:
        """生成MD5哈希"""
        return hashlib.md5(string.encode('utf-8')).hexdigest()
    
    def setup_driver(self, headless: bool = False):
        """
        设置Chrome浏览器驱动 - 整合 stealth 配置
        """
        logger.info(f"设置Chrome驱动... (headless={headless})")
        self.headless = headless
        
        self.manager = StealthDriverManager(
            headless=headless,
            bot_speed=BOT_SPEED,
            cookies_dir=COOKIES_DIR,
            screenshots_dir=SCREENSHOTS_DIR
        )
        
        self.driver = self.manager.setup_driver()
        
        # 设置等待时间
        self.wait = WebDriverWait(self.driver, 20)
        self.short_wait = WebDriverWait(self.driver, 5)
        
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
        return self.manager.take_screenshot(name, subdirectory="greenhouse")
    
    def apply(self, job_url: str, max_retries: int = 2) -> bool:
        """
        申请Greenhouse职位 - 整合最佳实践
        
        Args:
            job_url: 职位申请页面URL
            max_retries: 最大重试次数
        
        Returns:
            bool: 是否申请成功
        """
        self.start_time = time.time()
        retries = 0
        
        while retries < max_retries:
            try:
                prBlue(f"\n{'='*60}")
                prBlue(f"申请职位: {job_url}")
                prBlue(f"{'='*60}")
                
                self.driver.get(job_url)
                self.random_delay(5, 7)
                
                # 截图初始状态
                self.take_screenshot(f"page_loaded_{retries}")
                
                # 验证页面是否正确加载
                if not self._verify_page_loaded():
                    logger.error("页面加载失败")
                    retries += 1
                    self.random_delay(3, 5)
                    continue
                
                # 填写基本信息
                self._fill_basic_info()
                self.random_delay(1, BOT_SPEED)
                
                # 上传简历
                self._upload_resume()
                self.random_delay(2, BOT_SPEED)
                
                # 填写求职信
                self._fill_cover_letter()
                self.random_delay(1, BOT_SPEED)
                
                # 回答自定义问题
                self._answer_custom_questions()
                self.random_delay(1, BOT_SPEED)
                
                # 填写多元化信息
                self._fill_demographic_info()
                self.random_delay(1, BOT_SPEED)
                
                # 提交申请
                success = self._submit_application()
                
                if success:
                    self.applied_count += 1
                    duration = round((time.time() - self.start_time) / 60, 1)
                    prGreen(f"✅ 申请成功！耗时: {duration} 分钟")
                    self.take_screenshot("success")
                    return True
                else:
                    prRed("❌ 申请提交失败")
                    self.take_screenshot("submit_failed")
                    return False
                
            except StaleElementReferenceException:
                logger.warning(f"元素过期，重试 ({retries+1}/{max_retries})")
                retries += 1
                self.random_delay(3, 5)
            except Exception as e:
                logger.error(f"申请过程出错: {e}")
                self.take_screenshot(f"error_{retries}")
                retries += 1
                self.random_delay(3, 5)
        
        self.failed_count += 1
        logger.error(f"申请失败，已重试 {max_retries} 次")
        prRed(f"❌ 申请失败，已重试 {max_retries} 次")
        return False
    
    def _verify_page_loaded(self) -> bool:
        """验证页面是否正确加载 - 多种selector fallback"""
        try:
            # 检查是否有表单元素
            form_selectors = [
                "#application-form",
                "form[action*='greenhouse']",
                "#first_name",
                ".application-form",
                "form#job_application",
                "[data-qa='application-form']"
            ]
            
            for selector in form_selectors:
                try:
                    if self.driver.find_elements(By.CSS_SELECTOR, selector):
                        logger.info("✅ 页面加载成功")
                        return True
                except:
                    continue
            
            # 检查是否404
            page_title = self.driver.title.lower()
            page_source = self.driver.page_source.lower()
            
            if "404" in page_title or "not found" in page_source:
                logger.error("❌ 页面不存在(404)")
                return False
            
            # 尝试找到任何输入框
            inputs = self.driver.find_elements(By.TAG_NAME, "input")
            if inputs:
                logger.info("✅ 页面可能有表单")
                return True
            
            logger.warning("⚠️ 无法确认页面加载状态，继续尝试")
            return True
            
        except Exception as e:
            logger.error(f"验证页面时出错: {e}")
            return False
    
    def _fill_basic_info(self):
        """填写基本信息 - 多种selector fallback"""
        logger.info("填写基本信息...")
        prYellow("📝 填写基本信息...")
        
        personal = self.config['personal_info']
        
        # 字段映射 - 多种可能的ID/名称
        field_mappings = {
            'first_name': [
                ("#first_name", By.CSS_SELECTOR),
                ("input[name='job_application[first_name]'", By.CSS_SELECTOR),
                ("input[name='first_name]'", By.CSS_SELECTOR),
                ("input[placeholder*='First' i]", By.CSS_SELECTOR),
                ("//input[@placeholder='First Name']", By.XPATH),
                ("//input[contains(@placeholder, 'First')]", By.XPATH)
            ],
            'last_name': [
                ("#last_name", By.CSS_SELECTOR),
                ("input[name='job_application[last_name]'", By.CSS_SELECTOR),
                ("input[name='last_name]'", By.CSS_SELECTOR),
                ("input[placeholder*='Last' i]", By.CSS_SELECTOR),
                ("//input[@placeholder='Last Name']", By.XPATH)
            ],
            'email': [
                ("#email", By.CSS_SELECTOR),
                ("input[name='job_application[email]'", By.CSS_SELECTOR),
                ("input[name='email]'", By.CSS_SELECTOR),
                ("input[type='email']", By.CSS_SELECTOR),
                ("//input[@type='email']", By.XPATH)
            ],
            'phone': [
                ("#phone", By.CSS_SELECTOR),
                ("input[name='job_application[phone]'", By.CSS_SELECTOR),
                ("input[name='phone]'", By.CSS_SELECTOR),
                ("input[type='tel']", By.CSS_SELECTOR),
                ("//input[@type='tel']", By.XPATH)
            ],
            'linkedin': [
                ("#job_application_answers_attributes_0_text_value", By.CSS_SELECTOR),
                ("input[placeholder*='LinkedIn' i]", By.CSS_SELECTOR),
                ("input[name*='linkedin' i]", By.CSS_SELECTOR),
                ("//input[contains(@placeholder, 'LinkedIn')]", By.XPATH)
            ],
            'website': [
                ("#job_application_answers_attributes_1_text_value", By.CSS_SELECTOR),
                ("input[placeholder*='website' i]", By.CSS_SELECTOR),
                ("input[name*='website' i]", By.CSS_SELECTOR),
                ("input[name*='portfolio' i]", By.CSS_SELECTOR)
            ]
        }
        
        for field_name, selectors in field_mappings.items():
            value = personal.get(field_name, '')
            if not value:
                continue
            
            filled = False
            for selector, by in selectors:
                try:
                    if by == By.CSS_SELECTOR:
                        element = self.short_wait.until(
                            EC.presence_of_element_located((by, selector))
                        )
                    else:
                        element = self.driver.find_element(by, selector)
                    
                    if element.is_displayed():
                        element.clear()
                        self.random_delay(0.3, 0.8)
                        element.send_keys(value)
                        self.random_delay(0.5, 1)
                        logger.info(f"✅ 填写 {field_name}: {value[:30]}...")
                        filled = True
                        break
                except:
                    continue
            
            if not filled:
                logger.debug(f"无法填写 {field_name}")
    
    def _upload_resume(self):
        """上传简历 - 支持多种选择器"""
        logger.info("上传简历...")
        prYellow("📄 上传简历...")
        
        try:
            resume_path = os.path.expanduser(
                self.config['application_settings']['resume_path']
            )
            
            if not os.path.exists(resume_path):
                logger.warning(f"⚠️ 简历文件不存在: {resume_path}")
                return
            
            # 多种简历上传字段选择器 - 参考 reference-easy-apply-bot 的灵活策略
            resume_selectors = [
                # 标准Greenhouse
                ("#resume", By.CSS_SELECTOR),
                ("input[name='resume']", By.CSS_SELECTOR),
                ("input[name='job_application[resume]']", By.CSS_SELECTOR),
                ("input[name='job_application[resume_text]']", By.CSS_SELECTOR),
                ("input[type='file'][accept*='pdf']", By.CSS_SELECTOR),
                ("input[type='file'][name*='resume']", By.CSS_SELECTOR),
                # 更通用的选择器
                ("input[data-qa='resume-input']", By.CSS_SELECTOR),
                ("input[aria-label*='resume' i]", By.CSS_SELECTOR),
                ("input[aria-label*='CV' i]", By.CSS_SELECTOR),
                (".file-upload input[type='file']", By.CSS_SELECTOR),
                (".resume-upload input[type='file']", By.CSS_SELECTOR)
            ]
            
            file_input = None
            used_selector = None
            
            for selector, by in resume_selectors:
                try:
                    elements = self.driver.find_elements(by, selector)
                    for elem in elements:
                        if elem.is_displayed() or elem.is_enabled():
                            file_input = elem
                            used_selector = selector
                            break
                    if file_input:
                        break
                except:
                    continue
            
            if file_input:
                # 确保元素可见
                self.driver.execute_script("arguments[0].style.display = 'block';", file_input)
                self.driver.execute_script("arguments[0].style.visibility = 'visible';", file_input)
                
                # 上传文件
                file_input.send_keys(resume_path)
                logger.info(f"✅ 简历已上传: {os.path.basename(resume_path)}")
                prGreen(f"✅ 简历已上传: {os.path.basename(resume_path)}")
                
                # 等待上传完成
                self.random_delay(4, 6)
                
                # 验证上传成功
                if self._verify_upload_success():
                    logger.info("✅ 简历上传验证成功")
                else:
                    logger.warning("⚠️ 无法验证简历上传状态")
            else:
                logger.warning("⚠️ 未找到简历上传字段")
                
        except Exception as e:
            logger.error(f"上传简历时出错: {e}")
            self.take_screenshot("resume_upload_error")
    
    def _verify_upload_success(self) -> bool:
        """验证简历是否上传成功 - 多种indicator"""
        success_indicators = [
            (".file-upload-complete", By.CSS_SELECTOR),
            (".upload-complete", By.CSS_SELECTOR),
            (".file-name", By.CSS_SELECTOR),
            ("[data-qa='uploaded-file-name']", By.CSS_SELECTOR),
            ("//span[contains(text(), '.pdf')]", By.XPATH),
            ("//span[contains(text(), 'resume')]", By.XPATH),
            ("//div[contains(@class, 'attachment')]", By.XPATH)
        ]
        
        for selector, by in success_indicators:
            try:
                if by == By.XPATH:
                    elements = self.driver.find_elements(by, selector)
                else:
                    elements = self.driver.find_elements(by, selector)
                
                if elements and any(elem.is_displayed() for elem in elements if elem):
                    return True
            except:
                continue
        
        return False
    
    def _fill_cover_letter(self):
        """填写求职信"""
        logger.info("填写求职信...")
        
        try:
            # 查找求职信字段 - 多种selector
            cover_letter_selectors = [
                ("textarea[name='job_application[cover_letter]']", By.CSS_SELECTOR),
                ("textarea[name='cover_letter']", By.CSS_SELECTOR),
                ("textarea[placeholder*='cover letter' i]", By.CSS_SELECTOR),
                ("#cover_letter", By.CSS_SELECTOR),
                ("textarea[data-qa='cover-letter']", By.CSS_SELECTOR),
                ("//textarea[contains(@placeholder, 'cover')]", By.XPATH)
            ]
            
            cover_letter = self.config['application_settings'].get('cover_letter', '')
            if not cover_letter:
                cover_letter = self._generate_default_cover_letter()
            
            for selector, by in cover_letter_selectors:
                try:
                    element = self.short_wait.until(
                        EC.presence_of_element_located((by, selector))
                    )
                    element.clear()
                    self.random_delay(0.5, 1)
                    element.send_keys(cover_letter)
                    logger.info("✅ 求职信填写完成")
                    return
                except:
                    continue
            
            logger.info("- 未找到求职信字段")
                
        except Exception as e:
            logger.warning(f"填写求职信时出错: {e}")
    
    def _generate_default_cover_letter(self) -> str:
        """生成默认求职信"""
        return """Dear Hiring Manager,

I am writing to express my strong interest in this position. With my background in creative technology, virtual production, and technical leadership, I believe I would be a valuable addition to your team.

As the former Director of Creative Technology at Madwell (following the acquisition of WLab Innovations where I was Co-Founder & CCO), I led a 25-person XR unit delivering award-winning projects for major brands including Mercedes-Benz, Sony Music, e.l.f. Cosmetics, and NASA. My expertise spans virtual production, LED wall technology, Unreal Engine, motion capture, and real-time rendering pipelines.

Key highlights:
- Directed virtual production projects generating 1.5B+ impressions and winning Webby Awards
- Built and managed LED wall infrastructure for major clients
- Pioneered motion capture in microgravity environments for NASA research
- Led cross-functional teams spanning engineering, creative, and production

I am excited about the opportunity to bring my technical expertise and creative vision to your team. I look forward to discussing how my skills align with your needs.

Best regards,
Tommy Wu
https://www.linkedin.com/in/tommywu/
"""
    
    def _answer_custom_questions(self):
        """回答自定义问题 - 智能匹配"""
        logger.info("回答自定义问题...")
        prYellow("💬 回答自定义问题...")
        
        try:
            # 查找所有问题
            question_selectors = [
                ".application-question",
                ".field",
                ".question",
                "[data-qa='application-question']",
                ".job-application-question"
            ]
            
            questions = []
            for selector in question_selectors:
                questions.extend(self.driver.find_elements(By.CSS_SELECTOR, selector))
            
            # 去重
            seen = set()
            unique_questions = []
            for q in questions:
                try:
                    q_id = q.get_attribute('id') or q.get_attribute('class')
                    if q_id and q_id not in seen:
                        seen.add(q_id)
                        unique_questions.append(q)
                except:
                    unique_questions.append(q)
            
            logger.info(f"找到 {len(unique_questions)} 个问题")
            
            for question in unique_questions:
                try:
                    self._process_question(question)
                except Exception as e:
                    logger.debug(f"处理问题出错: {e}")
                    continue
                    
        except Exception as e:
            logger.warning(f"回答自定义问题时出错: {e}")
    
    def _process_question(self, question_element):
        """处理单个问题"""
        try:
            # 获取问题文本 - 多种方式
            question_text = ""
            label_selectors = ["label", ".label", ".question-label", "legend", ".field-label"]
            
            for selector in label_selectors:
                try:
                    label = question_element.find_element(By.CSS_SELECTOR, selector)
                    question_text = label.text.lower()
                    break
                except:
                    continue
            
            if not question_text:
                question_text = question_element.text.lower()[:100]
            
            # 查找输入元素
            text_inputs = question_element.find_elements(By.CSS_SELECTOR, "input[type='text']")
            textareas = question_element.find_elements(By.TAG_NAME, "textarea")
            selects = question_element.find_elements(By.TAG_NAME, "select")
            radios = question_element.find_elements(By.CSS_SELECTOR, "input[type='radio']")
            checkboxes = question_element.find_elements(By.CSS_SELECTOR, "input[type='checkbox']")
            
            # 根据输入类型处理
            if text_inputs:
                answer = self._get_answer_for_question(question_text)
                if answer:
                    text_inputs[0].clear()
                    self.random_delay(0.3, 0.8)
                    text_inputs[0].send_keys(answer)
                    logger.info(f"回答: {question_text[:40]}... -> {answer[:30]}")
                    
            elif textareas:
                answer = self._get_answer_for_question(question_text)
                if answer:
                    textareas[0].clear()
                    self.random_delay(0.3, 0.8)
                    textareas[0].send_keys(answer)
                    logger.info(f"回答: {question_text[:40]}... -> {answer[:30]}")
                    
            elif selects:
                self._handle_select_question(selects[0], question_text)
                
            elif radios:
                self._handle_radio_question(question_element, question_text)
                
            elif checkboxes:
                self._handle_checkbox_question(question_element, question_text)
                
        except Exception as e:
            logger.debug(f"处理问题元素出错: {e}")
    
    def _get_answer_for_question(self, question: str) -> str:
        """根据问题获取答案 - 智能匹配"""
        question_lower = question.lower()
        
        # 经验年限
        if any(word in question_lower for word in ['experience', 'years', 'how long']):
            return self.config['application_settings']['years_of_experience']
        
        # 薪资期望
        elif any(word in question_lower for word in ['salary', 'compensation', 'pay', 'expectation']):
            return str(self.config['application_settings']['desired_salary'])
        
        # 入职时间
        elif any(word in question_lower for word in ['notice', 'available', 'start', 'when can']):
            return f"{self.config['application_settings']['notice_period_days']} days"
        
        # LinkedIn
        elif any(word in question_lower for word in ['linkedin', 'profile']):
            return self.config['personal_info']['linkedin']
        
        # 网站/作品集
        elif any(word in question_lower for word in ['website', 'portfolio', 'github']):
            return self.config['personal_info']['website']
        
        # 工作授权/签证
        elif any(word in question_lower for word in ['sponsorship', 'visa']):
            return "Yes"
        elif any(word in question_lower for word in ['authorized', 'legally', 'eligible to work']):
            return "Yes"
        
        # 远程工作
        elif 'remote' in question_lower:
            return "Yes"
        
        # 搬迁
        elif 'relocate' in question_lower:
            return "No"
        
        else:
            return ""
    
    def _handle_select_question(self, select, question_text: str):
        """处理下拉选择问题"""
        try:
            dropdown = Select(select)
            question_lower = question_text.lower()
            
            if 'gender' in question_lower:
                value = self.config['equal_opportunity']['gender']
                try:
                    dropdown.select_by_visible_text(value)
                    logger.info(f"选择性别: {value}")
                except:
                    # 尝试部分匹配
                    options = [opt.text for opt in dropdown.options]
                    for opt in options:
                        if value.lower() in opt.lower():
                            dropdown.select_by_visible_text(opt)
                            break
                
            elif any(word in question_lower for word in ['race', 'ethnicity']):
                value = self.config['equal_opportunity']['ethnicity']
                try:
                    dropdown.select_by_visible_text(value)
                    logger.info(f"选择种族/族裔: {value}")
                except:
                    options = [opt.text for opt in dropdown.options]
                    for opt in options:
                        if 'asian' in opt.lower() or value.lower() in opt.lower():
                            dropdown.select_by_visible_text(opt)
                            break
                            
            elif 'veteran' in question_lower:
                options = dropdown.options
                for opt in options:
                    if 'not' in opt.text.lower() or 'no' in opt.text.lower() or 'decline' in opt.text.lower():
                        dropdown.select_by_visible_text(opt.text)
                        logger.info(f"选择退伍军人状态: {opt.text}")
                        break
                        
            elif 'disability' in question_lower:
                options = dropdown.options
                for opt in options:
                    if 'no' in opt.text.lower() or 'not' in opt.text.lower() or 'decline' in opt.text.lower():
                        dropdown.select_by_visible_text(opt.text)
                        logger.info(f"选择残疾状态: {opt.text}")
                        break
                        
        except Exception as e:
            logger.debug(f"处理下拉选择时出错: {e}")
    
    def _handle_radio_question(self, group, question_text: str):
        """处理单选按钮问题"""
        try:
            question_lower = question_text.lower()
            radios = group.find_elements(By.CSS_SELECTOR, "input[type='radio']")
            
            if not radios:
                return
            
            select_value = None
            
            if any(word in question_lower for word in ['sponsorship', 'visa']):
                select_value = 'yes'
            elif any(word in question_lower for word in ['authorized', 'legally', 'eligible']):
                select_value = 'yes'
            elif 'relocate' in question_lower:
                select_value = 'no'
            elif 'remote' in question_lower:
                select_value = 'yes'
            
            if select_value:
                for radio in radios:
                    value = radio.get_attribute('value').lower()
                    label_text = ""
                    try:
                        label_id = radio.get_attribute('id')
                        if label_id:
                            label = group.find_element(By.CSS_SELECTOR, f"label[for='{label_id}']")
                            label_text = label.text.lower()
                    except:
                        pass
                    
                    if select_value in value or select_value in label_text:
                        radio.click()
                        logger.info(f"选择单选: {label_text or value}")
                        break
                        
        except Exception as e:
            logger.debug(f"处理单选问题时出错: {e}")
    
    def _handle_checkbox_question(self, group, question_text: str):
        """处理复选框问题"""
        try:
            question_lower = question_text.lower()
            checkboxes = group.find_elements(By.CSS_SELECTOR, "input[type='checkbox']")
            
            # 通常是同意条款
            if any(word in question_lower for word in ['agree', 'confirm', 'acknowledge', 'accept']):
                for checkbox in checkboxes:
                    if not checkbox.is_selected():
                        checkbox.click()
                        logger.info("勾选同意选项")
                        break
                        
        except Exception as e:
            logger.debug(f"处理复选框问题时出错: {e}")
    
    def _fill_demographic_info(self):
        """填写多元化/人口统计信息"""
        logger.info("填写多元化信息...")
        
        try:
            # 查找多元化信息部分
            demo_selectors = [
                "#demographic-section",
                "[data-qa='demographic-section']",
                ".demographic-section",
                ".eeo-section"
            ]
            
            demo_section = None
            for selector in demo_selectors:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    demo_section = elements[0]
                    break
            
            if not demo_section:
                logger.info("- 未找到多元化信息部分")
                return
            
            # 性别
            gender_selectors = [
                ("#gender", By.CSS_SELECTOR),
                ("select[name='gender']", By.CSS_SELECTOR),
                ("//select[contains(@name, 'gender')]", By.XPATH)
            ]
            
            for selector, by in gender_selectors:
                try:
                    gender_select = Select(self.driver.find_element(by, selector))
                    gender_select.select_by_visible_text(
                        self.config['equal_opportunity']['gender']
                    )
                    logger.info("选择性别")
                    break
                except:
                    pass
            
            # 种族/族裔
            race_selectors = [
                ("#race", By.CSS_SELECTOR),
                ("select[name='race']", By.CSS_SELECTOR),
                ("select[name='ethnicity']", By.CSS_SELECTOR),
                ("//select[contains(@name, 'race')]", By.XPATH)
            ]
            
            for selector, by in race_selectors:
                try:
                    race_select = Select(self.driver.find_element(by, selector))
                    race_select.select_by_visible_text(
                        self.config['equal_opportunity']['ethnicity']
                    )
                    logger.info("选择种族/族裔")
                    break
                except:
                    pass
            
        except Exception as e:
            logger.debug(f"填写多元化信息时出错: {e}")
    
    def _submit_application(self) -> bool:
        """提交申请 - 多种selector fallback"""
        logger.info("提交申请...")
        prYellow("📤 提交申请...")
        
        try:
            # 查找提交按钮 - 多种选择器
            submit_selectors = [
                ("#submit", By.CSS_SELECTOR),
                ("input[type='submit']", By.CSS_SELECTOR),
                ("button[type='submit']", By.CSS_SELECTOR),
                ("[data-qa='submit-application']", By.CSS_SELECTOR),
                ("button.primary", By.CSS_SELECTOR),
                ("input[value*='Submit' i]", By.CSS_SELECTOR),
                ("input[value*='Apply' i]", By.CSS_SELECTOR),
                ("//button[contains(text(), 'Submit')]", By.XPATH),
                ("//button[contains(text(), 'Apply')]", By.XPATH),
                ("//input[@value='Submit Application']", By.XPATH)
            ]
            
            submit_btn = None
            for selector, by in submit_selectors:
                try:
                    if by == By.XPATH:
                        submit_btn = self.driver.find_element(by, selector)
                    else:
                        submit_btn = self.short_wait.until(
                            EC.element_to_be_clickable((by, selector))
                        )
                    
                    if submit_btn and submit_btn.is_displayed():
                        break
                except:
                    continue
            
            if not submit_btn:
                logger.error("未找到提交按钮")
                prRed("❌ 未找到提交按钮")
                return False
            
            # 检查按钮是否可用
            if not submit_btn.is_enabled():
                logger.error("提交按钮不可用，可能有必填字段未填写")
                prRed("❌ 提交按钮不可用，可能有必填字段未填写")
                self.take_screenshot("submit_disabled")
                return False
            
            # 截图提交前状态
            self.take_screenshot("before_submit")
            
            # 点击提交
            submit_btn.click()
            logger.info("点击提交按钮")
            prYellow("🖱️ 点击提交按钮...")
            
            # 等待结果
            self.random_delay(5, 7)
            
            # 验证提交成功
            return self._verify_submission_success()
            
        except Exception as e:
            logger.error(f"提交申请时出错: {e}")
            prRed(f"❌ 提交申请时出错: {str(e)[:80]}")
            return False
    
    def _verify_submission_success(self) -> bool:
        """验证申请是否提交成功 - 多种indicator"""
        success_indicators = [
            # URL变化
            lambda: "thank" in self.driver.current_url.lower() or "confirmation" in self.driver.current_url.lower(),
            # 成功消息
            lambda: len(self.driver.find_elements(By.XPATH, "//*[contains(text(), 'Thank you')]")) > 0,
            lambda: len(self.driver.find_elements(By.XPATH, "//*[contains(text(), 'successfully')]")) > 0,
            lambda: len(self.driver.find_elements(By.XPATH, "//*[contains(text(), 'Application submitted')]")) > 0,
            lambda: len(self.driver.find_elements(By.XPATH, "//*[contains(text(), 'received your application')]")) > 0,
            lambda: len(self.driver.find_elements(By.CSS_SELECTOR, ".thank-you-message")) > 0,
            lambda: len(self.driver.find_elements(By.CSS_SELECTOR, ".application-submitted")) > 0,
            lambda: len(self.driver.find_elements(By.CSS_SELECTOR, "[data-qa='application-submitted']")) > 0,
            lambda: len(self.driver.find_elements(By.CSS_SELECTOR, ".confirmation-message")) > 0
        ]
        
        for indicator in success_indicators:
            try:
                if indicator():
                    logger.info("✅ 申请提交成功确认")
                    prGreen("✅ 申请提交成功！")
                    return True
            except:
                pass
        
        # 检查页面标题
        if "thank" in self.driver.title.lower() or "confirmation" in self.driver.title.lower():
            prGreen("✅ 申请提交成功！(通过页面标题确认)")
            return True
        
        logger.warning("无法确认申请提交状态")
        prYellow("⚠️ 无法确认申请提交状态")
        return False
    
    def close(self):
        """关闭浏览器"""
        if hasattr(self, 'manager') and self.manager:
            self.manager.close()
        logger.info(f"日志文件: {log_file}")


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Greenhouse ATS 自动化申请 v2.0')
    parser.add_argument('--url', required=True, help='职位申请页面URL')
    parser.add_argument('--headless', action='store_true', help='使用无头模式')
    parser.add_argument('--retries', type=int, default=2, help='最大重试次数')
    
    args = parser.parse_args()
    
    applier = GreenhouseAutoApply()
    
    try:
        applier.setup_driver(headless=args.headless)
        success = applier.apply(args.url, max_retries=args.retries)
        
        if success:
            prGreen("\n" + "="*60)
            prGreen("✓ 申请成功完成！")
            prGreen("="*60)
        else:
            prRed("\n" + "="*60)
            prRed("✗ 申请失败")
            prRed("="*60)
            
    except KeyboardInterrupt:
        prYellow("\n用户中断")
    except Exception as e:
        prRed(f"运行时出错: {e}")
    finally:
        applier.close()
        logger.info(f"日志文件: {log_file}")


if __name__ == "__main__":
    main()
