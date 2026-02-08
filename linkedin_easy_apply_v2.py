#!/usr/bin/env python3
"""
LinkedIn Easy Apply - 完整多步骤自动申请 v2.0
支持多步骤流程，自动处理简历和提交
"""

import time
import yaml
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

# 加载配置
config_path = Path("config/profile.yaml")
with open(config_path) as f:
    config = yaml.safe_load(f)

personal = config.get('personal_info', {})

PROFILE = {
    'first_name': personal.get('first_name', 'Tommy'),
    'last_name': personal.get('last_name', 'Wu'),
    'email': personal.get('email', 'tommy.wu@nyu.edu'),
    'phone': personal.get('phone', '917-742-4303'),
}

RESUME_FILENAME = "TOMMY WU Resume Dec 2025.pdf"

def setup_driver():
    options = Options()
    options.add_argument('--no-sandbox')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('--disable-gpu')
    options.add_argument('--disable-extensions')
    
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=options)

def login(driver):
    """登录 LinkedIn"""
    print("\n🔐 登录 LinkedIn...")
    driver.get("https://www.linkedin.com/login")
    time.sleep(2)
    driver.find_element(By.ID, "username").send_keys("wuyuehao2001@outlook.com")
    driver.find_element(By.ID, "password").send_keys("Tommy12345#")
    driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
    time.sleep(3)
    print("✅ 登录成功")

def click_easy_apply_js(driver):
    """使用 JavaScript 点击 Easy Apply"""
    print("\n🖱️ 点击 Easy Apply...")
    result = driver.execute_script("""
        var btn = document.getElementById('jobs-apply-button-id');
        if (btn) {
            btn.click();
            return 'Clicked';
        }
        return 'Not found';
    """)
    print(f"   {result}")
    time.sleep(5)

def get_step_info(driver):
    """获取当前步骤信息"""
    return driver.execute_script("""
        var progress = document.querySelector('.artdeco-modal .jobs-easy-apply-content__progress');
        var title = document.querySelector('.artdeco-modal h2, .artdeco-modal h3');
        return {
            progress: progress ? progress.textContent.trim() : '',
            title: title ? title.textContent.trim() : ''
        };
    """)

def handle_current_step(driver):
    """处理当前步骤"""
    step_info = get_step_info(driver)
    print(f"\n📄 当前步骤: {step_info.get('title', 'Unknown')}")
    print(f"   进度: {step_info.get('progress', 'N/A')}")
    
    # 根据步骤类型处理
    title = step_info.get('title', '').lower()
    
    if 'contact' in title or 'info' in title:
        return handle_contact_step(driver)
    elif 'resume' in title or 'cv' in title:
        return handle_resume_step(driver)
    elif 'experience' in title or 'work' in title:
        return handle_experience_step(driver)
    elif 'review' in title:
        return handle_review_step(driver)
    elif 'question' in title or 'additional' in title:
        return handle_questions_step(driver)
    else:
        # 通用处理 - 尝试点击 Next
        return click_next_js(driver)

def handle_contact_step(driver):
    """处理联系信息步骤"""
    print("   处理联系信息...")
    # LinkedIn 通常自动填充，直接点击 Next
    return click_next_js(driver)

def handle_resume_step(driver):
    """处理简历步骤"""
    print("   处理简历...")
    # 选择指定简历
    result = driver.execute_script("""
        var resumeCards = document.querySelectorAll('.jobs-resume-picker__resume-card');
        for (var card of resumeCards) {
            var title = card.textContent;
            if (title.includes('""" + RESUME_FILENAME.replace("'", "\\'") + """')) {
                var radio = card.querySelector('input[type="radio"]');
                if (radio && !radio.checked) {
                    radio.click();
                    return 'Selected resume: """ + RESUME_FILENAME.replace("'", "\\'") + """';
                }
                return 'Resume already selected';
            }
        }
        return 'Resume not found, using default';
    """)
    print(f"   {result}")
    return click_next_js(driver)

def handle_experience_step(driver):
    """处理工作经验步骤"""
    print("   处理工作经验...")
    # 通常 LinkedIn 从 profile 自动填充
    return click_next_js(driver)

def handle_questions_step(driver):
    """处理附加问题步骤"""
    print("   处理附加问题...")
    # 这里可以添加 AI 回答逻辑
    return click_next_js(driver)

def handle_review_step(driver):
    """处理审核步骤 - 提交申请"""
    print("   审核并提交...")
    return click_submit_js(driver)

def click_next_js(driver):
    """使用 JavaScript 点击 Next"""
    result = driver.execute_script("""
        // 查找 Next/Continue/Review 按钮
        var buttons = document.querySelectorAll('.artdeco-modal button');
        for (var btn of buttons) {
            var text = btn.textContent.toLowerCase();
            if ((text.includes('next') || text.includes('continue') || text.includes('review')) 
                && !text.includes('back') && !btn.disabled) {
                btn.click();
                return 'Clicked: ' + btn.textContent.trim();
            }
        }
        return 'Next button not found';
    """)
    print(f"   {result}")
    time.sleep(4)
    return 'next' in result.lower() or 'continue' in result.lower() or 'review' in result.lower()

def click_submit_js(driver):
    """使用 JavaScript 点击 Submit"""
    result = driver.execute_script("""
        var buttons = document.querySelectorAll('.artdeco-modal button');
        for (var btn of buttons) {
            var text = btn.textContent.toLowerCase();
            if ((text.includes('submit') || text.includes('send')) && !btn.disabled) {
                btn.click();
                return 'Clicked: ' + btn.textContent.trim();
            }
        }
        return 'Submit button not found';
    """)
    print(f"   {result}")
    time.sleep(4)
    return 'submit' in result.lower()

def is_application_complete(driver):
    """检查申请是否完成"""
    return driver.execute_script("""
        var success = document.querySelector('.artdeco-modal .jobs-easy-apply-content__success, .jobs-easy-apply-content__confirmation');
        var doneText = document.body.textContent;
        return !!(success || doneText.includes('Application sent') || doneText.includes('Successfully'));
    """)

def main():
    print("="*60)
    print("🚀 LinkedIn Easy Apply - 完整自动申请 v2.0")
    print("="*60)
    
    driver = setup_driver()
    
    try:
        # 登录
        login(driver)
        
        # 访问职位
        print("\n📋 访问职位...")
        driver.get("https://www.linkedin.com/jobs/view/4361442478")
        time.sleep(5)
        
        # 点击 Easy Apply
        click_easy_apply_js(driver)
        
        # 处理多步骤申请
        max_steps = 10
        for step in range(max_steps):
            print(f"\n--- Step {step + 1} ---")
            
            # 检查是否完成
            if is_application_complete(driver):
                print("\n🎉 申请已成功提交！")
                break
            
            # 处理当前步骤
            can_continue = handle_current_step(driver)
            
            if not can_continue:
                print("\n⚠️ 无法继续，可能需要人工处理")
                break
        
        # 保存最终截图
        driver.save_screenshot("final_submission.png")
        print("\n📸 截图: final_submission.png")
        
        print("\n" + "="*60)
        print("✅ 流程结束")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        driver.save_screenshot("error.png")
    
    finally:
        time.sleep(3)
        driver.quit()

if __name__ == "__main__":
    main()
