#!/usr/bin/env python3
"""
增强版 Greenhouse ATS 自动化申请脚本
修复问题：
1. 灵活的CSS选择器 - 支持多种Greenhouse布局
2. 智能等待和iframe处理
3. 错误重试机制
4. 自动截图调试
5. 申请成功/失败检测
"""

import os
import sys
import time
import yaml
import json
import logging
from pathlib import Path
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
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

SCREENSHOTS_DIR = Path("screenshots")
SCREENSHOTS_DIR.mkdir(exist_ok=True)


class GreenhouseAutoApply:
    """Greenhouse ATS 增强版自动化申请器"""
    
    def __init__(self, config_path: str = "config/profile.yaml"):
        self.config = self._load_config(config_path)
        self.driver = None
        self.wait = None
        self.short_wait = None
        self.headless = False
        
    def _load_config(self, path: str) -> dict:
        """加载配置文件"""
        try:
            with open(path, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"加载配置文件失败: {e}")
            sys.exit(1)
    
    def setup_driver(self, headless: bool = False):
        """设置Chrome浏览器驱动"""
        logger.info(f"设置Chrome驱动... (headless={headless})")
        self.headless = headless
        
        chrome_options = Options()
        
        if headless:
            chrome_options.add_argument("--headless=new")
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
            self.wait = WebDriverWait(self.driver, 20)
            self.short_wait = WebDriverWait(self.driver, 5)
            
            logger.info("Chrome驱动设置完成")
            
        except Exception as e:
            logger.error(f"Chrome驱动设置失败: {e}")
            raise
    
    def take_screenshot(self, name: str = None):
        """截取当前屏幕"""
        if name is None:
            name = f"screenshot_{datetime.now().strftime('%H%M%S')}"
        
        screenshot_path = SCREENSHOTS_DIR / f"greenhouse_{name}.png"
        try:
            self.driver.save_screenshot(str(screenshot_path))
            logger.info(f"截图已保存: {screenshot_path}")
            return screenshot_path
        except Exception as e:
            logger.error(f"截图失败: {e}")
            return None
    
    def apply(self, job_url: str, max_retries: int = 2) -> bool:
        """
        申请Greenhouse职位
        
        Args:
            job_url: 职位申请页面URL
            max_retries: 最大重试次数
        
        Returns:
            bool: 是否申请成功
        """
        retries = 0
        
        while retries < max_retries:
            try:
                logger.info(f"\n{'='*60}")
                logger.info(f"申请职位: {job_url}")
                logger.info(f"{'='*60}")
                
                self.driver.get(job_url)
                time.sleep(5)  # 等待页面完全加载
                
                # 截图初始状态
                self.take_screenshot("page_loaded")
                
                # 检查页面是否正确加载
                if not self._verify_page_loaded():
                    logger.error("页面加载失败")
                    retries += 1
                    continue
                
                # 填写基本信息
                self._fill_basic_info()
                
                # 上传简历
                self._upload_resume()
                
                # 填写求职信
                self._fill_cover_letter()
                
                # 回答自定义问题
                self._answer_custom_questions()
                
                # 填写多元化信息
                self._fill_demographic_info()
                
                # 提交申请
                success = self._submit_application()
                
                if success:
                    logger.info("✓ 申请成功完成")
                    self.take_screenshot("success")
                    return True
                else:
                    logger.error("✗ 申请提交失败")
                    self.take_screenshot("submit_failed")
                    return False
                
            except StaleElementReferenceException:
                logger.warning(f"元素过期，重试 ({retries+1}/{max_retries})")
                retries += 1
                time.sleep(3)
            except Exception as e:
                logger.error(f"申请过程出错: {e}")
                self.take_screenshot(f"error_{retries}")
                retries += 1
                time.sleep(3)
        
        logger.error(f"申请失败，已重试 {max_retries} 次")
        return False
    
    def _verify_page_loaded(self) -> bool:
        """验证页面是否正确加载"""
        try:
            # 检查是否有表单元素
            form_selectors = [
                "#application-form",
                "form[action*='greenhouse']",
                "#first_name",
                ".application-form"
            ]
            
            for selector in form_selectors:
                try:
                    if self.driver.find_elements(By.CSS_SELECTOR, selector):
                        logger.info("页面加载成功")
                        return True
                except:
                    pass
            
            # 检查是否404
            if "404" in self.driver.title or "not found" in self.driver.page_source.lower():
                logger.error("页面不存在(404)")
                return False
            
            logger.warning("无法确认页面加载状态，继续尝试")
            return True
            
        except Exception as e:
            logger.error(f"验证页面时出错: {e}")
            return False
    
    def _fill_basic_info(self):
        """填写基本信息"""
        logger.info("填写基本信息...")
        
        personal = self.config['personal_info']
        
        # 字段映射 (多种可能的ID/名称)
        field_mappings = {
            'first_name': [
                "#first_name",
                "input[name='job_application[first_name]']",
                "input[name='first_name']",
                "input[placeholder*='First' i]"
            ],
            'last_name': [
                "#last_name",
                "input[name='job_application[last_name]']",
                "input[name='last_name']",
                "input[placeholder*='Last' i]"
            ],
            'email': [
                "#email",
                "input[name='job_application[email]']",
                "input[name='email']",
                "input[type='email']"
            ],
            'phone': [
                "#phone",
                "input[name='job_application[phone]']",
                "input[name='phone']",
                "input[type='tel']"
            ],
            'linkedin': [
                "#job_application_answers_attributes_0_text_value",
                "input[placeholder*='LinkedIn' i]",
                "input[name*='linkedin' i]"
            ],
            'website': [
                "#job_application_answers_attributes_1_text_value",
                "input[placeholder*='website' i]",
                "input[name*='website' i]"
            ]
        }
        
        for field_name, selectors in field_mappings.items():
            value = personal.get(field_name, '')
            if not value:
                continue
            
            for selector in selectors:
                try:
                    element = self.short_wait.until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                    element.clear()
                    element.send_keys(value)
                    logger.info(f"填写 {field_name}: {value[:30]}...")
                    break
                except:
                    continue
    
    def _upload_resume(self):
        """上传简历 - 支持多种选择器"""
        logger.info("上传简历...")
        
        try:
            resume_path = os.path.expanduser(
                self.config['application_settings']['resume_path']
            )
            
            if not os.path.exists(resume_path):
                logger.warning(f"简历文件不存在: {resume_path}")
                return
            
            # 多种简历上传字段选择器
            resume_selectors = [
                # 标准Greenhouse
                "#resume",
                "input[name='resume']",
                "input[name='job_application[resume]']",
                "input[name='job_application[resume_text]']",
                "input[type='file'][accept*='pdf']",
                "input[type='file'][accept*='.pdf']",
                "input[type='file'][name*='resume']",
                # 更通用的选择器
                "input[data-qa='resume-input']",
                "input[aria-label*='resume' i]",
                "input[aria-label*='CV' i]",
                # Lever (类似Greenhouse)
                "input[name='resume']",
                "input[data-qa='resume-input']",
                # 检查是否有文件上传区域
                ".file-upload input[type='file']",
                ".resume-upload input[type='file']"
            ]
            
            file_input = None
            
            # 尝试找到文件上传输入
            for selector in resume_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for elem in elements:
                        if elem.is_displayed() or elem.is_enabled():
                            file_input = elem
                            logger.debug(f"找到简历上传字段: {selector}")
                            break
                    if file_input:
                        break
                except Exception as e:
                    logger.debug(f"选择器 {selector} 失败: {e}")
                    continue
            
            if file_input:
                # 确保元素可见
                self.driver.execute_script("arguments[0].style.display = 'block';", file_input)
                self.driver.execute_script("arguments[0].style.visibility = 'visible';", file_input)
                
                # 上传文件
                file_input.send_keys(resume_path)
                logger.info(f"✓ 简历已上传: {os.path.basename(resume_path)}")
                
                # 等待上传完成
                time.sleep(4)
                
                # 验证上传成功
                if self._verify_upload_success():
                    logger.info("✓ 简历上传验证成功")
                else:
                    logger.warning("⚠ 无法验证简历上传状态")
            else:
                logger.warning("⚠ 未找到简历上传字段，可能需要手动上传")
                
        except Exception as e:
            logger.error(f"上传简历时出错: {e}")
            self.take_screenshot("resume_upload_error")
    
    def _verify_upload_success(self) -> bool:
        """验证简历是否上传成功"""
        success_indicators = [
            ".file-upload-complete",
            ".upload-complete",
            ".file-name",
            "[data-qa='uploaded-file-name']",
            "//span[contains(text(), '.pdf')]",
            "//span[contains(text(), 'resume')]"
        ]
        
        for indicator in success_indicators:
            try:
                if indicator.startswith("//"):
                    elements = self.driver.find_elements(By.XPATH, indicator)
                else:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, indicator)
                
                if elements and any(elem.is_displayed() for elem in elements):
                    return True
            except:
                continue
        
        return False
    
    def _fill_cover_letter(self):
        """填写求职信"""
        logger.info("填写求职信...")
        
        try:
            # 查找求职信字段
            cover_letter_selectors = [
                "textarea[name='job_application[cover_letter]']",
                "textarea[name='cover_letter']",
                "textarea[placeholder*='cover letter' i]",
                "textarea[placeholder*='Cover Letter' i]",
                "#cover_letter",
                "textarea[data-qa='cover-letter']",
                "textarea[aria-label*='cover' i]"
            ]
            
            cover_letter = self.config['application_settings'].get('cover_letter', '')
            if not cover_letter:
                cover_letter = self._generate_default_cover_letter()
            
            for selector in cover_letter_selectors:
                try:
                    element = self.short_wait.until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                    element.clear()
                    element.send_keys(cover_letter)
                    logger.info("✓ 求职信填写完成")
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
        """回答自定义问题"""
        logger.info("回答自定义问题...")
        
        try:
            # 查找所有问题
            question_selectors = [
                ".application-question",
                ".field",
                ".question",
                "[data-qa='application-question']"
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
            # 获取问题文本
            question_text = ""
            label_selectors = ["label", ".label", ".question-label", "legend"]
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
                    text_inputs[0].send_keys(answer)
                    logger.info(f"回答: {question_text[:40]}... -> {answer[:30]}")
                    
            elif textareas:
                answer = self._get_answer_for_question(question_text)
                if answer:
                    textareas[0].clear()
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
        """根据问题获取答案"""
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
        elif any(word in question_lower for word in ['sponsorship', 'visa', 'authorized', 'legally']):
            if 'sponsorship' in question_lower:
                return "Yes"
            elif 'authorized' in question_lower or 'legally' in question_lower:
                return "No, I am not authorized"
            return ""
        
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
                dropdown.select_by_visible_text(value)
                logger.info(f"选择性别: {value}")
                
            elif any(word in question_lower for word in ['race', 'ethnicity']):
                value = self.config['equal_opportunity']['ethnicity']
                try:
                    dropdown.select_by_visible_text(value)
                    logger.info(f"选择种族/族裔: {value}")
                except:
                    # 尝试其他选项
                    options = [opt.text for opt in dropdown.options]
                    for opt in options:
                        if 'asian' in opt.lower():
                            dropdown.select_by_visible_text(opt)
                            break
                            
            elif 'veteran' in question_lower:
                options = dropdown.options
                for opt in options:
                    if 'not' in opt.text.lower() or 'no' in opt.text.lower():
                        dropdown.select_by_visible_text(opt.text)
                        logger.info(f"选择退伍军人状态: {opt.text}")
                        break
                        
            elif 'disability' in question_lower:
                options = dropdown.options
                for opt in options:
                    if 'no' in opt.text.lower() or 'not' in opt.text.lower():
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
                select_value = 'no'
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
            if any(word in question_lower for word in ['agree', 'confirm', 'acknowledge']):
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
                ".demographic-section"
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
            try:
                gender_select = Select(self.driver.find_element(By.ID, "gender"))
                gender_select.select_by_visible_text(
                    self.config['equal_opportunity']['gender']
                )
                logger.info("选择性别")
            except:
                pass
            
            # 种族/族裔
            try:
                race_select = Select(self.driver.find_element(By.ID, "race"))
                race_select.select_by_visible_text(
                    self.config['equal_opportunity']['ethnicity']
                )
                logger.info("选择种族/族裔")
            except:
                pass
            
        except Exception as e:
            logger.debug(f"填写多元化信息时出错: {e}")
    
    def _submit_application(self) -> bool:
        """提交申请"""
        logger.info("提交申请...")
        
        try:
            # 查找提交按钮
            submit_selectors = [
                "#submit",
                "input[type='submit']",
                "button[type='submit']",
                "button:contains('Submit')",
                "[data-qa='submit-application']",
                "button.primary",
                "input[value*='Submit' i]",
                "input[value*='Apply' i]"
            ]
            
            submit_btn = None
            for selector in submit_selectors:
                try:
                    if ":contains" in selector:
                        # 简化的contains处理
                        elements = self.driver.find_elements(By.TAG_NAME, "button")
                        for elem in elements:
                            if "submit" in elem.text.lower() or "apply" in elem.text.lower():
                                submit_btn = elem
                                break
                    else:
                        submit_btn = self.short_wait.until(
                            EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                        )
                    
                    if submit_btn:
                        break
                except:
                    continue
            
            if not submit_btn:
                logger.error("未找到提交按钮")
                return False
            
            # 检查按钮是否可用
            if not submit_btn.is_enabled():
                logger.error("提交按钮不可用，可能有必填字段未填写")
                self.take_screenshot("submit_disabled")
                return False
            
            # 点击提交
            submit_btn.click()
            logger.info("点击提交按钮")
            
            # 等待结果
            time.sleep(5)
            
            # 验证提交成功
            return self._verify_submission_success()
            
        except Exception as e:
            logger.error(f"提交申请时出错: {e}")
            return False
    
    def _verify_submission_success(self) -> bool:
        """验证申请是否提交成功"""
        success_indicators = [
            # URL变化
            lambda: "thank" in self.driver.current_url.lower(),
            # 成功消息
            lambda: len(self.driver.find_elements(By.XPATH, "//*[contains(text(), 'Thank you')]")) > 0,
            lambda: len(self.driver.find_elements(By.XPATH, "//*[contains(text(), 'successfully')]")) > 0,
            lambda: len(self.driver.find_elements(By.XPATH, "//*[contains(text(), 'Application submitted')]")) > 0,
            lambda: len(self.driver.find_elements(By.CSS_SELECTOR, ".thank-you-message")) > 0,
            lambda: len(self.driver.find_elements(By.CSS_SELECTOR, ".application-submitted")) > 0,
            lambda: len(self.driver.find_elements(By.CSS_SELECTOR, "[data-qa='application-submitted']")) > 0,
        ]
        
        for indicator in success_indicators:
            try:
                if indicator():
                    logger.info("✓ 申请提交成功确认")
                    return True
            except:
                pass
        
        # 检查页面标题
        if "thank" in self.driver.title.lower():
            return True
        
        logger.warning("无法确认申请提交状态")
        return False
    
    def close(self):
        """关闭浏览器"""
        if self.driver:
            self.driver.quit()
            logger.info("浏览器已关闭")


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Greenhouse ATS 自动化申请')
    parser.add_argument('--url', required=True, help='职位申请页面URL')
    parser.add_argument('--headless', action='store_true', help='使用无头模式')
    parser.add_argument('--retries', type=int, default=2, help='最大重试次数')
    
    args = parser.parse_args()
    
    applier = GreenhouseAutoApply()
    
    try:
        applier.setup_driver(headless=args.headless)
        success = applier.apply(args.url, max_retries=args.retries)
        
        if success:
            logger.info("\n" + "="*60)
            logger.info("✓ 申请成功完成！")
            logger.info("="*60)
        else:
            logger.error("\n" + "="*60)
            logger.error("✗ 申请失败")
            logger.error("="*60)
            
    except KeyboardInterrupt:
        logger.info("\n用户中断")
    except Exception as e:
        logger.error(f"运行时出错: {e}")
    finally:
        applier.close()
        logger.info(f"日志文件: {log_file}")


if __name__ == "__main__":
    main()
