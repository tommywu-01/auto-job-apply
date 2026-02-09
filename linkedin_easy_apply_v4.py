#!/usr/bin/env python3
"""
LinkedIn Easy Apply - 最终稳定版 v4.0
使用更直接的方法填写表单
"""

import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

# 预设答案
ANSWERS = {
    'photo shoot': '5',
    'years of experience': '5',
    'sponsorship': 'Yes',
    'visa': 'Yes',
    'salary': '150000',
    'notice': '2 weeks',
}

def setup_driver():
    options = Options()
    options.add_argument('--no-sandbox')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('--disable-gpu')
    options.add_argument('--disable-extensions')
    
    # 使用持久化用户数据目录保持登录状态
    from pathlib import Path
    user_data_dir = Path.home() / '.linkedin_automation_profile'
    user_data_dir.mkdir(exist_ok=True)
    options.add_argument(f'--user-data-dir={user_data_dir}')
    
    # 禁用自动化检测
    options.add_experimental_option('excludeSwitches', ['enable-automation'])
    options.add_experimental_option('useAutomationExtension', False)
    
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=options)

def fill_all_inputs(driver):
    """填写所有空输入框"""
    return driver.execute_script("""
        var filled = [];
        var inputs = document.querySelectorAll('.artdeco-modal input[type="text"], .artdeco-modal input[type="number"], .artdeco-modal textarea');
        
        inputs.forEach(function(input) {
            if (!input.value && input.offsetParent !== null) {
                // 获取问题文本
                var label = document.querySelector('label[for="' + input.id + '"]');
                var questionText = '';
                
                if (label) {
                    questionText = label.textContent.toLowerCase();
                } else {
                    // 尝试从父元素获取
                    var parent = input.closest('.jobs-easy-apply-form-element, .artdeco-text-input--container');
                    if (parent) {
                        var labelEl = parent.querySelector('label, .jobs-easy-apply-form-element__label');
                        if (labelEl) questionText = labelEl.textContent.toLowerCase();
                    }
                }
                
                // 根据问题确定答案
                var answer = '';
                if (questionText.includes('photo') || questionText.includes('shoot')) {
                    answer = '5';
                } else if (questionText.includes('year') && questionText.includes('experience')) {
                    answer = '5';
                } else if (questionText.includes('sponsor') || questionText.includes('visa')) {
                    answer = 'Yes';
                } else if (questionText.includes('salary') || questionText.includes('pay')) {
                    answer = '150000';
                } else if (questionText.includes('notice') || questionText.includes('start')) {
                    answer = '2 weeks';
                } else {
                    answer = '5';  // 默认值
                }
                
                if (answer) {
                    input.value = answer;
                    input.dispatchEvent(new Event('input', { bubbles: true }));
                    input.dispatchEvent(new Event('change', { bubbles: true }));
                    filled.push(questionText.substring(0, 40) + '... = ' + answer);
                }
            }
        });
        
        return filled;
    """)

def click_button(driver, text):
    """点击按钮"""
    return driver.execute_script("""
        var buttons = document.querySelectorAll('.artdeco-modal button');
        for (var btn of buttons) {
            if (btn.textContent.toLowerCase().includes('""" + text + """') && !btn.disabled) {
                btn.click();
                return 'Clicked: ' + btn.textContent.trim();
            }
        }
        return 'Not found';
    """)

def is_logged_in(driver):
    """检查是否已登录"""
    try:
        driver.get("https://www.linkedin.com/feed")
        time.sleep(2)
        current_url = driver.current_url
        if "feed" in current_url or "linkedin.com/in/" in current_url:
            return True
        login_elements = driver.find_elements(By.ID, "username")
        if len(login_elements) == 0:
            return True
        return False
    except:
        return False

def smart_login(driver):
    """智能登录 - 检查状态避免重复登录"""
    print("\n🔐 检查登录状态...")
    
    if is_logged_in(driver):
        print("✅ 已登录，使用现有会话")
        return
    
    print("🔐 需要登录...")
    driver.get("https://www.linkedin.com/login")
    time.sleep(2)
    driver.find_element(By.ID, "username").send_keys("wuyuehao2001@outlook.com")
    driver.find_element(By.ID, "password").send_keys("Tommy12345#")
    driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
    time.sleep(3)
    print("✅ 登录成功")

def main():
    print("🚀 LinkedIn Easy Apply - 最终稳定版 v4.0 (持久化登录)")
    driver = setup_driver()
    
    try:
        # 智能登录（避免重复）
        smart_login(driver)
        
        # 访问职位
        print("\n📋 访问职位...")
        driver.get("https://www.linkedin.com/jobs/view/4361442478")
        time.sleep(5)
        
        # 点击 Easy Apply
        print("\n🖱️ 点击 Easy Apply...")
        driver.execute_script("document.getElementById('jobs-apply-button-id').click()")
        time.sleep(5)
        
        # 循环处理步骤
        for step in range(8):
            print(f"\n--- Step {step + 1} ---")
            
            # 填写所有输入框
            filled = fill_all_inputs(driver)
            for f in filled:
                print(f"   ✅ {f}")
            
            # 尝试点击按钮
            for btn_text in ['next', 'review', 'submit']:
                result = click_button(driver, btn_text)
                if 'Clicked' in result:
                    print(f"   {result}")
                    break
            
            time.sleep(3)
            
            # 检查是否完成
            done = driver.execute_script("""
                return document.body.textContent.includes('Application sent') ||
                       document.querySelector('.jobs-easy-apply-content__success') !== null;
            """)
            if done:
                print("\n🎉 申请成功！")
                break
        
        driver.save_screenshot("final_v4.png")
        print("\n📸 截图: final_v4.png")
        
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        driver.save_screenshot("error_v4.png")
    
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
