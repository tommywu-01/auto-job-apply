#!/usr/bin/env python3
"""
Greenhouse ATS 完全自动化申请脚本
支持自动填写所有表单字段并提交
"""

import os
import time
import yaml
import logging
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class GreenhouseAutoApply:
    """Greenhouse ATS 自动化申请器"""
    
    def __init__(self, config_path: str = "config/profile.yaml"):
        self.config = self._load_config(config_path)
        self.driver = None
        self.wait = None
        
    def _load_config(self, path: str) -> dict:
        with open(path, 'r') as f:
            return yaml.safe_load(f)
    
    def setup_driver(self, headless: bool = False):
        """设置Chrome驱动"""
        logger.info("设置Chrome驱动...")
        
        chrome_options = Options()
        if headless:
            chrome_options.add_argument("--headless")
        
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--window-size=1920,1080")
        
        self.driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=chrome_options
        )
        self.wait = WebDriverWait(self.driver, 15)
        logger.info("驱动设置完成")
    
    def apply(self, job_url: str) -> bool:
        """
        申请Greenhouse职位
        
        自动填写:
        - 基本信息 (姓名、邮箱、电话)
        - 简历上传
        - 求职信 (可选)
        - 自定义问题
        - 多元化信息 (可选)
        """
        try:
            logger.info(f"访问职位页面: {job_url}")
            self.driver.get(job_url)
            time.sleep(3)
            
            # 填写基本信息
            self._fill_basic_info()
            
            # 上传简历
            self._upload_resume()
            
            # 填写求职信 (如果有)
            self._fill_cover_letter()
            
            # 回答自定义问题
            self._answer_custom_questions()
            
            # 填写多元化信息 (如果页面有)
            self._fill_demographic_info()
            
            # 提交申请
            return self._submit_application()
            
        except Exception as e:
            logger.error(f"申请过程出错: {e}")
            return False
    
    def _fill_basic_info(self):
        """填写基本信息"""
        logger.info("填写基本信息...")
        
        personal = self.config['personal_info']
        
        # 名字
        try:
            first_name_field = self.wait.until(
                EC.presence_of_element_located((By.ID, "first_name"))
            )
            first_name_field.send_keys(personal['first_name'])
        except:
            pass
        
        # 姓氏
        try:
            last_name_field = self.driver.find_element(By.ID, "last_name")
            last_name_field.send_keys(personal['last_name'])
        except:
            pass
        
        # 邮箱
        try:
            email_field = self.driver.find_element(By.ID, "email")
            email_field.send_keys(personal['email'])
        except:
            pass
        
        # 电话
        try:
            phone_field = self.driver.find_element(By.ID, "phone")
            phone_field.send_keys(personal['phone'])
        except:
            pass
        
        # LinkedIn (如果有)
        try:
            linkedin_field = self.driver.find_element(
                By.CSS_SELECTOR, "input[placeholder*='LinkedIn']"
            )
            linkedin_field.send_keys(personal['linkedin'])
        except:
            pass
        
        # 个人网站 (如果有)
        try:
            website_field = self.driver.find_element(
                By.CSS_SELECTOR, "input[placeholder*='website' i]"
            )
            website_field.send_keys(personal['website'])
        except:
            pass
        
        logger.info("基本信息填写完成")
    
    def _upload_resume(self):
        """上传简历"""
        logger.info("上传简历...")
        
        try:
            resume_path = os.path.expanduser(
                self.config['application_settings']['resume_path']
            )
            
            if not os.path.exists(resume_path):
                logger.warning(f"简历文件不存在: {resume_path}")
                return
            
            # 查找文件上传输入
            file_input = self.driver.find_element(By.ID, "resume")
            file_input.send_keys(resume_path)
            
            logger.info("简历上传完成")
            time.sleep(2)
            
        except Exception as e:
            logger.warning(f"上传简历时出错: {e}")
    
    def _fill_cover_letter(self):
        """填写求职信"""
        logger.info("检查求职信字段...")
        
        try:
            # 查找求职信文本框
            cover_letter_fields = self.driver.find_elements(
                By.CSS_SELECTOR, "textarea[placeholder*='cover letter' i]"
            )
            
            if cover_letter_fields:
                # 使用配置中的求职信
                cover_letter = self.config['application_settings'].get('cover_letter', '')
                if not cover_letter:
                    cover_letter = """Dear Hiring Manager,

I am writing to express my interest in this position. With my background in creative technology and virtual production, I believe I would be a valuable addition to your team.

My experience includes leading technical teams, managing LED wall productions, and delivering innovative projects for major brands like Mercedes-Benz, Sony Music, and NASA.

I look forward to discussing how my skills and experience align with your needs.

Best regards,
Tommy Wu"""
                
                cover_letter_fields[0].send_keys(cover_letter)
                logger.info("求职信填写完成")
                
        except Exception as e:
            logger.warning(f"填写求职信时出错: {e}")
    
    def _answer_custom_questions(self):
        """回答自定义问题"""
        logger.info("回答自定义问题...")
        
        # 查找所有自定义问题
        questions = self.driver.find_elements(
            By.CSS_SELECTOR, ".application-question"
        )
        
        for question in questions:
            try:
                # 获取问题文本
                question_text = question.text.lower()
                
                # 查找输入字段
                text_inputs = question.find_elements(By.CSS_SELECTOR, "input[type='text']")
                textareas = question.find_elements(By.TAG_NAME, "textarea")
                selects = question.find_elements(By.TAG_NAME, "select")
                radios = question.find_elements(By.CSS_SELECTOR, "input[type='radio']")
                
                if text_inputs:
                    answer = self._get_answer_for_question(question_text)
                    if answer:
                        text_inputs[0].send_keys(answer)
                        
                elif textareas:
                    answer = self._get_answer_for_question(question_text)
                    if answer:
                        textareas[0].send_keys(answer)
                        
                elif selects:
                    self._handle_select_question(selects[0], question_text)
                    
                elif radios:
                    self._handle_radio_question(radios, question_text)
                    
            except Exception as e:
                logger.warning(f"回答问题时出错: {e}")
                continue
        
        logger.info("自定义问题回答完成")
    
    def _get_answer_for_question(self, question: str) -> str:
        """根据问题文本获取答案"""
        answers = self.config.get('common_questions', {})
        
        # 常见问题匹配
        if any(word in question for word in ['experience', 'years']):
            return self.config['application_settings']['years_of_experience']
        
        elif any(word in question for word in ['salary', 'compensation', 'pay']):
            return str(self.config['application_settings']['desired_salary'])
        
        elif any(word in question for word in ['notice', 'available', 'start']):
            return f"{self.config['application_settings']['notice_period_days']} days"
        
        elif any(word in question for word in ['linkedin', 'profile']):
            return self.config['personal_info']['linkedin']
        
        elif any(word in question for word in ['website', 'portfolio']):
            return self.config['personal_info']['website']
        
        elif 'sponsorship' in question or 'visa' in question:
            return "Yes"
        
        elif 'authorized' in question or 'legally' in question:
            return "No"
        
        elif 'relocate' in question:
            return "No"
        
        elif 'remote' in question:
            return "Yes"
        
        else:
            return ""
    
    def _handle_select_question(self, select, question_text: str):
        """处理下拉选择问题"""
        try:
            dropdown = Select(select)
            
            if 'gender' in question_text:
                value = self.config['equal_opportunity']['gender']
                dropdown.select_by_visible_text(value)
                
            elif any(word in question_text for word in ['race', 'ethnicity']):
                value = self.config['equal_opportunity']['ethnicity']
                dropdown.select_by_visible_text(value)
                
            elif 'veteran' in question_text:
                dropdown.select_by_visible_text("I am not a protected veteran")
                
            elif 'disability' in question_text:
                dropdown.select_by_visible_text("No, I don't have a disability")
                
        except Exception as e:
            logger.warning(f"处理下拉选择时出错: {e}")
    
    def _handle_radio_question(self, radios, question_text: str):
        """处理单选按钮问题"""
        try:
            if 'sponsorship' in question_text or 'visa' in question_text:
                # 选择Yes
                for radio in radios:
                    if radio.get_attribute('value').lower() in ['yes', 'true']:
                        radio.click()
                        break
                        
            elif 'authorized' in question_text or 'legally' in question_text:
                # 选择No
                for radio in radios:
                    if radio.get_attribute('value').lower() in ['no', 'false']:
                        radio.click()
                        break
                        
            elif 'relocate' in question_text:
                # 选择No
                for radio in radios:
                    if radio.get_attribute('value').lower() in ['no', 'false']:
                        radio.click()
                        break
                        
        except Exception as e:
            logger.warning(f"处理单选问题时出错: {e}")
    
    def _fill_demographic_info(self):
        """填写多元化/人口统计信息"""
        logger.info("填写多元化信息...")
        
        try:
            # 这些信息通常在单独的页面或部分
            demo_section = self.driver.find_elements(
                By.CSS_SELECTOR, "#demographic-section"
            )
            
            if demo_section:
                # 性别
                try:
                    gender_select = Select(self.driver.find_element(By.ID, "gender"))
                    gender_select.select_by_visible_text(
                        self.config['equal_opportunity']['gender']
                    )
                except:
                    pass
                
                # 种族/族裔
                try:
                    race_select = Select(self.driver.find_element(By.ID, "race"))
                    race_select.select_by_visible_text(
                        self.config['equal_opportunity']['ethnicity']
                    )
                except:
                    pass
                
                logger.info("多元化信息填写完成")
                
        except Exception as e:
            logger.warning(f"填写多元化信息时出错: {e}")
    
    def _submit_application(self) -> bool:
        """提交申请"""
        logger.info("提交申请...")
        
        try:
            # 查找提交按钮
            submit_btn = self.wait.until(
                EC.element_to_be_clickable((By.ID, "submit"))
            )
            
            # 检查是否可点击
            if submit_btn.is_enabled():
                submit_btn.click()
                logger.info("申请已提交！")
                
                # 等待确认页面
                time.sleep(3)
                
                # 检查是否成功
                if "thank" in self.driver.current_url.lower() or \
                   self.driver.find_elements(By.CSS_SELECTOR, ".thank-you-message"):
                    logger.info("申请提交成功确认")
                    return True
            else:
                logger.warning("提交按钮不可用，可能有必填字段未填写")
                return False
                
        except Exception as e:
            logger.error(f"提交申请时出错: {e}")
            return False
        
        return False
    
    def close(self):
        """关闭浏览器"""
        if self.driver:
            self.driver.quit()


def main():
    """主函数 - 申请Eyeline Studios职位"""
    applier = GreenhouseAutoApply()
    
    try:
        applier.setup_driver(headless=False)
        
        # Eyeline Studios 示例URL (需要替换为实际URL)
        job_url = "https://boards.greenhouse.io/eyelinestudios/jobs/example"
        
        success = applier.apply(job_url)
        
        if success:
            logger.info("申请成功！")
        else:
            logger.error("申请失败")
            
    finally:
        applier.close()


if __name__ == "__main__":
    main()
