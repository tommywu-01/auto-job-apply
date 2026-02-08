#!/usr/bin/env python3
"""
LinkedIn Easy Apply - 带故障救援的版本 v5.0
集成 Rescue System，卡住时自动召唤 Botty
"""

import time
import yaml
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from rescue_system import RescueSystem, check_mission_control_messages

# 加载配置
config_path = Path("config/profile.yaml")
with open(config_path) as f:
    profile = yaml.safe_load(f)

PERSONAL = profile.get('personal_info', {})

class LinkedInEasyApplyWithRescue:
    def __init__(self):
        self.driver = None
        self.rescue = RescueSystem()
        self.context = {'step': 'init', 'job_url': ''}
        self.last_progress_time = time.time()
        
    def setup_driver(self):
        options = Options()
        options.add_argument('--no-sandbox')
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-extensions')
        
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=options)
        self.driver.set_page_load_timeout(30)
    
    def record_progress(self, step, message):
        """记录进度"""
        self.context['step'] = step
        self.last_progress_time = self.rescue.record_progress(step, message)
        print(f"   📍 {step}: {message}")
    
    def check_stuck(self):
        """检查是否卡住"""
        if self.rescue.is_stuck(self.last_progress_time, timeout=300):  # 5分钟
            print("\n🚨 检测到卡住（5分钟无进展）")
            self.rescue.send_mission_control_alert(
                error_type='STUCK',
                details=self.context,
                screenshot_path=self.take_screenshot()
            )
            return True
        return False
    
    def handle_error(self, error):
        """处理错误"""
        result = self.rescue.handle_error(error, self.context, self.driver)
        
        if result == 'RESCUE_REQUESTED':
            print("\n🆘 救援信号已发送给 Botty")
            print("   等待救援中...")
            self.wait_for_rescue()
        
        return result
    
    def wait_for_rescue(self, timeout=600):
        """等待救援（最多10分钟）"""
        print(f"\n⏳ 等待 Botty 救援（最多10分钟）...")
        
        for i in range(timeout // 10):
            time.sleep(10)
            
            # 检查 Mission Control 是否有回复
            message = check_mission_control_messages()
            if message:
                print(f"\n📨 收到救援指令: {message.get('instruction', 'unknown')}")
                return message
            
            # 打印等待提示
            if i % 6 == 0:  # 每分钟打印一次
                print(f"   已等待 {(i+1)*10} 秒...")
        
        print("\n⚠️ 等待超时，退出")
        return None
    
    def take_screenshot(self):
        """截图"""
        try:
            from datetime import datetime
            path = Path(f'logs/screenshot_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png')
            path.parent.mkdir(exist_ok=True)
            self.driver.save_screenshot(str(path))
            return path
        except:
            return None
    
    def login(self):
        """登录"""
        try:
            self.record_progress('login', '开始登录')
            self.driver.get("https://www.linkedin.com/login")
            time.sleep(2)
            self.driver.find_element(By.ID, "username").send_keys("wuyuehao2001@outlook.com")
            self.driver.find_element(By.ID, "password").send_keys("Tommy12345#")
            self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
            time.sleep(4)
            self.record_progress('login', '登录成功')
            return True
        except Exception as e:
            self.handle_error(e)
            return False
    
    def apply_to_job(self, job_url):
        """申请单个职位"""
        self.context['job_url'] = job_url
        
        try:
            # 访问职位
            self.record_progress('visit_job', f'访问 {job_url}')
            self.driver.get(job_url)
            time.sleep(5)
            
            # 检查是否卡住
            if self.check_stuck():
                return False
            
            # 点击 Easy Apply
            self.record_progress('click_easy_apply', '点击 Easy Apply')
            self.driver.execute_script("document.getElementById('jobs-apply-button-id').click()")
            time.sleep(5)
            
            # 处理多步骤
            for step in range(8):
                self.record_progress(f'step_{step+1}', f'处理第 {step+1} 步')
                
                # AI 填写表单
                self.ai_fill_form()
                
                # 点击按钮
                for btn in ['next', 'review', 'submit']:
                    result = self.driver.execute_script(f"""
                        var buttons = document.querySelectorAll('.artdeco-modal button');
                        for (var btn of buttons) {{
                            if (btn.textContent.toLowerCase().includes('{btn}') && !btn.disabled) {{
                                btn.click();
                                return 'Clicked';
                            }}
                        }}
                        return false;
                    """)
                    if result:
                        break
                
                time.sleep(4)
                
                # 检查是否完成
                if self.is_complete():
                    self.record_progress('completed', '申请成功提交')
                    self.rescue.reset_error_count()
                    return True
                
                # 检查是否卡住
                if self.check_stuck():
                    return False
            
            return False
            
        except Exception as e:
            self.handle_error(e)
            return False
    
    def ai_fill_form(self):
        """AI 填写表单"""
        self.driver.execute_script("""
            var inputs = document.querySelectorAll('.artdeco-modal input[type="text"], .artdeco-modal input[type="number"]');
            inputs.forEach(function(input) {
                if (!input.value && input.offsetParent) {
                    var label = document.querySelector('label[for="' + input.id + '"]');
                    var question = label ? label.textContent.toLowerCase() : '';
                    
                    var answer = '';
                    if (question.includes('photo') || question.includes('shoot')) answer = '5';
                    else if (question.includes('years') || question.includes('experience')) answer = '5';
                    else if (question.includes('sponsor') || question.includes('visa')) answer = 'Yes';
                    else if (question.includes('salary')) answer = '150000';
                    else answer = '5';
                    
                    if (answer) {
                        input.value = answer;
                        input.dispatchEvent(new Event('input', { bubbles: true }));
                    }
                }
            });
        """)
    
    def is_complete(self):
        """检查是否完成"""
        return self.driver.execute_script("""
            return document.body.textContent.includes('Application sent') ||
                   document.querySelector('.jobs-easy-apply-content__success') !== null;
        """)
    
    def run(self, job_url="https://www.linkedin.com/jobs/view/4361442478"):
        """主流程"""
        print("="*60)
        print("🚀 LinkedIn Easy Apply - 带故障救援版本 v5.0")
        print("="*60)
        
        try:
            self.setup_driver()
            
            # 检查 Mission Control 是否有暂停指令
            message = check_mission_control_messages()
            if message and message.get('instruction') == 'PAUSE':
                print("\n⏸️ 收到暂停指令，暂停申请")
                return
            
            # 登录
            if not self.login():
                return
            
            # 申请职位
            success = self.apply_to_job(job_url)
            
            if success:
                print("\n🎉 申请成功！")
            else:
                print("\n⚠️ 申请未完成")
            
            # 截图
            self.take_screenshot()
            
        except Exception as e:
            print(f"\n❌ 严重错误: {e}")
            self.handle_error(e)
        
        finally:
            if self.driver:
                self.driver.quit()
            
            print("\n" + "="*60)
            print("✅ 流程结束")
            print("="*60)

if __name__ == "__main__":
    bot = LinkedInEasyApplyWithRescue()
    bot.run()
