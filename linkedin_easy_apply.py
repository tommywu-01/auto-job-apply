#!/usr/bin/env python3
"""
LinkedIn Easy Apply 完全自动化申请脚本
处理多步弹窗 (通常3-5步) 并自动提交

功能:
1. 自动登录LinkedIn
2. 搜索目标职位
3. 自动填写Easy Apply表单
4. 处理多步弹窗 (Contact Info → Resume → Additional Questions → Review → Submit)
5. 自动提交申请
"""

import os
import sys
import time
import yaml
import json
import logging
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('linkedin_auto_apply.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class LinkedInEasyApply:
    """LinkedIn Easy Apply 自动化申请器"""
    
    def __init__(self, config_path: str = "config/profile.yaml"):
        self.config = self._load_config(config_path)
        self.driver = None
        self.wait = None
        self.applied_count = 0
        
    def _load_config(self, path: str) -> dict:
        """加载配置文件"""
        with open(path, 'r') as f:
            return yaml.safe_load(f)
    
    def setup_driver(self, headless: bool = False):
        """设置Chrome浏览器驱动"""
        logger.info("设置Chrome驱动...")
        
        chrome_options = Options()
        
        if headless:
            chrome_options.add_argument("--headless")
        
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # 添加用户代理
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        self.driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=chrome_options
        )
        
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        self.wait = WebDriverWait(self.driver, 10)
        logger.info("Chrome驱动设置完成")
    
    def login(self):
        """登录LinkedIn"""
        logger.info("正在登录LinkedIn...")
        
        email = self.config['personal_info']['email']
        password = os.environ.get('LINKEDIN_PASSWORD', '')  # 从环境变量获取密码
        
        if not password:
            logger.error("请设置LINKEDIN_PASSWORD环境变量")
            return False
        
        self.driver.get("https://www.linkedin.com/login")
        time.sleep(2)
        
        # 填写邮箱
        email_field = self.wait.until(
            EC.presence_of_element_located((By.ID, "username"))
        )
        email_field.send_keys(email)
        
        # 填写密码
        password_field = self.driver.find_element(By.ID, "password")
        password_field.send_keys(password)
        
        # 点击登录
        login_button = self.driver.find_element(By.XPATH, "//button[@type='submit']")
        login_button.click()
        
        time.sleep(3)
        
        # 检查是否登录成功
        if "feed" in self.driver.current_url or "mynetwork" in self.driver.current_url:
            logger.info("LinkedIn登录成功")
            return True
        else:
            logger.error("LinkedIn登录失败")
            return False
    
    def search_jobs(self, keywords: str, location: str = "United States"):
        """搜索职位"""
        logger.info(f"搜索职位: {keywords}")
        
        search_url = f"https://www.linkedin.com/jobs/search/?keywords={keywords.replace(' ', '%20')}"
        if location:
            search_url += f"&location={location.replace(' ', '%20')}"
        
        self.driver.get(search_url)
        time.sleep(3)
        
        logger.info("职位搜索完成")
    
    def find_easy_apply_jobs(self):
        """查找Easy Apply职位"""
        logger.info("查找Easy Apply职位...")
        
        try:
            # 筛选Easy Apply
            easy_apply_filter = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Easy Apply')]"))
            )
            easy_apply_filter.click()
            time.sleep(2)
            
            # 获取职位列表
            job_cards = self.driver.find_elements(
                By.CSS_SELECTOR, ".jobs-search-results__list-item"
            )
            
            logger.info(f"找到 {len(job_cards)} 个职位")
            return job_cards
            
        except Exception as e:
            logger.error(f"查找Easy Apply职位时出错: {e}")
            return []
    
    def apply_to_job(self, job_card) -> bool:
        """
        申请单个职位 - 处理多步弹窗
        
        Easy Apply 流程通常包括:
        1. Contact Info (联系信息)
        2. Resume (简历)
        3. Additional Questions (附加问题)
        4. Work Authorization (工作授权)
        5. Review (审核)
        6. Submit (提交)
        """
        try:
            # 点击职位卡片
            job_card.click()
            time.sleep(2)
            
            # 点击Easy Apply按钮
            easy_apply_btn = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(@class, 'jobs-apply-button')]"))
            )
            
            # 检查是否已经是已申请状态
            button_text = easy_apply_btn.text.lower()
            if "applied" in button_text or "application" in button_text:
                logger.info("职位已申请，跳过")
                return False
            
            easy_apply_btn.click()
            logger.info("开始Easy Apply申请流程")
            time.sleep(2)
            
            # 处理多步表单
            step_count = 0
            max_steps = 10  # 防止无限循环
            
            while step_count < max_steps:
                step_count += 1
                logger.info(f"处理第 {step_count} 步...")
                
                # 识别当前步骤
                current_step = self._identify_current_step()
                logger.info(f"当前步骤: {current_step}")
                
                # 根据步骤类型处理
                if current_step == "contact_info":
                    self._fill_contact_info()
                elif current_step == "resume":
                    self._handle_resume()
                elif current_step == "additional_questions":
                    self._answer_additional_questions()
                elif current_step == "work_authorization":
                    self._fill_work_authorization()
                elif current_step == "review":
                    self._review_application()
                elif current_step == "submit":
                    return self._submit_application()
                else:
                    logger.warning(f"未知步骤: {current_step}")
                
                # 点击下一步/继续
                if not self._click_next_button():
                    break
                
                time.sleep(2)
            
            return False
            
        except Exception as e:
            logger.error(f"申请职位时出错: {e}")
            return False
    
    def _identify_current_step(self) -> str:
        """识别当前申请步骤"""
        try:
            # 获取弹窗标题
            modal_title = self.driver.find_element(
                By.CSS_SELECTOR, ".jobs-easy-apply-modal__title"
            ).text.lower()
            
            if "contact" in modal_title or "info" in modal_title:
                return "contact_info"
            elif "resume" in modal_title:
                return "resume"
            elif "additional" in modal_title or "questions" in modal_title:
                return "additional_questions"
            elif "work" in modal_title or "authorization" in modal_title:
                return "work_authorization"
            elif "review" in modal_title:
                return "review"
            elif "submit" in modal_title:
                return "submit"
            else:
                # 通过页面内容判断
                if self.driver.find_elements(By.CSS_SELECTOR, "input[type='tel']"):
                    return "contact_info"
                elif self.driver.find_elements(By.CSS_SELECTOR, "input[type='file']"):
                    return "resume"
                else:
                    return "unknown"
                    
        except:
            return "unknown"
    
    def _fill_contact_info(self):
        """填写联系信息"""
        logger.info("填写联系信息...")
        
        try:
            # 电话号码（如果需要）
            phone_inputs = self.driver.find_elements(
                By.CSS_SELECTOR, "input[type='tel']"
            )
            if phone_inputs:
                phone = self.config['personal_info']['phone']
                phone_inputs[0].clear()
                phone_inputs[0].send_keys(phone)
                logger.info("填写电话号码")
                
        except Exception as e:
            logger.warning(f"填写联系信息时出错: {e}")
    
    def _handle_resume(self):
        """处理简历上传"""
        logger.info("处理简历...")
        
        try:
            # 检查是否有简历上传输入
            file_inputs = self.driver.find_elements(
                By.CSS_SELECTOR, "input[type='file']"
            )
            
            if file_inputs:
                resume_path = os.path.expanduser(
                    self.config['application_settings']['resume_path']
                )
                
                if os.path.exists(resume_path):
                    file_inputs[0].send_keys(resume_path)
                    logger.info(f"上传简历: {resume_path}")
                    time.sleep(2)
                else:
                    logger.warning(f"简历文件不存在: {resume_path}")
            else:
                logger.info("使用LinkedIn默认简历")
                
        except Exception as e:
            logger.warning(f"处理简历时出错: {e}")
    
    def _answer_additional_questions(self):
        """回答附加问题"""
        logger.info("回答附加问题...")
        
        try:
            # 查找所有文本输入
            text_inputs = self.driver.find_elements(
                By.CSS_SELECTOR, ".jobs-easy-apply-form-section__question input[type='text']"
            )
            
            for input_field in text_inputs:
                # 获取问题标签
                try:
                    label = input_field.find_element(
                        By.XPATH, "../label"
                    ).text.lower()
                except:
                    label = ""
                
                # 根据问题类型填写答案
                answer = self._get_answer_for_question(label)
                if answer:
                    input_field.clear()
                    input_field.send_keys(answer)
                    logger.info(f"回答问题: {label}")
            
            # 处理下拉选择
            selects = self.driver.find_elements(
                By.CSS_SELECTOR, "select"
            )
            for select in selects:
                # 获取问题文本
                try:
                    label = select.find_element(
                        By.XPATH, "../label"
                    ).text.lower()
                except:
                    label = ""
                
                # 选择适当选项
                self._handle_select_question(select, label)
                
            # 处理单选按钮
            radio_groups = self.driver.find_elements(
                By.CSS_SELECTOR, ".jobs-easy-apply-form-section__question fieldset"
            )
            for group in radio_groups:
                try:
                    question = group.find_element(By.TAG_NAME, "legend").text.lower()
                    answer = self._get_radio_answer(question)
                    
                    if answer:
                        radio = group.find_element(
                            By.XPATH, f".//input[@value='{answer}']"
                        )
                        radio.click()
                        logger.info(f"选择单选答案: {question}")
                except:
                    pass
                    
        except Exception as e:
            logger.warning(f"回答附加问题时出错: {e}")
    
    def _get_answer_for_question(self, question: str) -> str:
        """根据问题获取答案"""
        question_lower = question.lower()
        
        # 常见问题和答案映射
        answers = {
            "experience": self.config['application_settings']['years_of_experience'],
            "salary": str(self.config['application_settings']['desired_salary']),
            "website": self.config['personal_info']['website'],
            "linkedin": self.config['personal_info']['linkedin'],
            "portfolio": self.config['personal_info']['portfolio'],
            "notice": str(self.config['application_settings']['notice_period_days']),
            "sponsorship": "Yes",
        }
        
        for key, answer in answers.items():
            if key in question_lower:
                return answer
        
        return ""
    
    def _handle_select_question(self, select, label: str):
        """处理下拉选择问题"""
        try:
            # 点击打开下拉菜单
            select.click()
            time.sleep(1)
            
            # 根据标签选择
            label_lower = label.lower()
            
            if "gender" in label_lower:
                option_text = self.config['equal_opportunity']['gender']
            elif "ethnicity" in label_lower or "race" in label_lower:
                option_text = self.config['equal_opportunity']['ethnicity']
            elif "veteran" in label_lower:
                option_text = "No"
            elif "disability" in label_lower:
                option_text = "No"
            else:
                option_text = ""
            
            if option_text:
                # 选择对应选项
                options = select.find_elements(By.TAG_NAME, "option")
                for option in options:
                    if option_text.lower() in option.text.lower():
                        option.click()
                        logger.info(f"选择: {option_text}")
                        break
                        
        except Exception as e:
            logger.warning(f"处理下拉选择时出错: {e}")
    
    def _get_radio_answer(self, question: str) -> str:
        """获取单选答案"""
        question_lower = question.lower()
        
        if "sponsorship" in question_lower or "visa" in question_lower:
            return "Yes"
        elif "authorized" in question_lower or "legally" in question_lower:
            return "No"
        elif "relocate" in question_lower:
            return "No"
        else:
            return ""
    
    def _fill_work_authorization(self):
        """填写工作授权信息"""
        logger.info("填写工作授权信息...")
        
        # 工作授权信息通常在附加问题中处理
        # 这里可以添加特定的逻辑
        pass
    
    def _review_application(self):
        """审核申请"""
        logger.info("审核申请...")
        
        # 在实际运行中，可以添加自动检查逻辑
        # 目前直接继续
        pass
    
    def _submit_application(self) -> bool:
        """提交申请"""
        logger.info("提交申请...")
        
        try:
            # 查找提交按钮
            submit_btn = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Submit')]"))
            )
            
            # 点击提交
            submit_btn.click()
            logger.info("申请已提交！")
            
            time.sleep(2)
            
            self.applied_count += 1
            return True
            
        except Exception as e:
            logger.error(f"提交申请时出错: {e}")
            return False
    
    def _click_next_button(self) -> bool:
        """点击下一步按钮"""
        try:
            # 查找下一步/继续/审核按钮
            next_btn = self.driver.find_element(
                By.XPATH, 
                "//button[contains(text(), 'Next') or contains(text(), 'Continue') or contains(text(), 'Review')]"
            )
            
            # 检查按钮是否可用
            if next_btn.is_enabled():
                next_btn.click()
                return True
            else:
                logger.warning("下一步按钮不可用")
                return False
                
        except Exception as e:
            logger.error(f"点击下一步按钮时出错: {e}")
            return False
    
    def close(self):
        """关闭浏览器"""
        if self.driver:
            logger.info(f"申请完成。共申请 {self.applied_count} 个职位")
            self.driver.quit()


def main():
    """主函数"""
    # 初始化
    applier = LinkedInEasyApply()
    
    try:
        # 设置驱动
        applier.setup_driver(headless=False)
        
        # 登录
        if not applier.login():
            logger.error("登录失败，退出")
            return
        
        # 搜索目标职位
        applier.search_jobs("Director of Technical Services", "New York")
        
        # 查找Easy Apply职位
        jobs = applier.find_easy_apply_jobs()
        
        # 申请职位
        for i, job in enumerate(jobs[:5]):  # 限制申请数量
            logger.info(f"申请第 {i+1} 个职位...")
            success = applier.apply_to_job(job)
            
            if success:
                logger.info(f"第 {i+1} 个职位申请成功")
            else:
                logger.warning(f"第 {i+1} 个职位申请失败或跳过")
            
            # 申请间隔
            time.sleep(5)
        
    except Exception as e:
        logger.error(f"运行时出错: {e}")
        
    finally:
        applier.close()


if __name__ == "__main__":
    main()
