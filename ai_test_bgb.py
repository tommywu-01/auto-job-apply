#!/usr/bin/env python3
"""
AI 测试 - BGB Group 职位
"""

import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

# AI 知识库
AI_ANSWERS = {
    'photo shoot': '5',
    'years of experience': '8',
    'years': '8',
    'experience': '8',
    'sponsorship': 'Yes',
    'visa': 'Yes',
    'salary': '180000',
    'compensation': '180000',
    'notice': '2 weeks',
    'start': 'Immediately',
    'remote': 'Yes',
    'relocation': 'No',
}

def setup_driver():
    options = Options()
    options.add_argument('--no-sandbox')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--disable-blink-features=AutomationControlled')
    
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=options)

def ai_fill_form(driver):
    """AI 填写表单"""
    print("\n🤖 AI 分析表单...")
    
    filled = driver.execute_script("""
        var filled = [];
        var inputs = document.querySelectorAll('.artdeco-modal input[type="text"], .artdeco-modal input[type="number"], .artdeco-modal textarea');
        
        inputs.forEach(function(input) {
            if (!input.offsetParent || input.value) return;
            
            var questionText = '';
            var label = document.querySelector('label[for="' + input.id + '"]');
            if (label) {
                questionText = label.textContent.toLowerCase();
            } else {
                var parent = input.closest('.jobs-easy-apply-form-element');
                if (parent) {
                    var labelEl = parent.querySelector('label, .jobs-easy-apply-form-element__label');
                    if (labelEl) questionText = labelEl.textContent.toLowerCase();
                }
            }
            
            var answer = '';
            if (questionText.includes('photo') || questionText.includes('shoot')) answer = '5';
            else if (questionText.includes('years') || questionText.includes('experience')) answer = '8';
            else if (questionText.includes('sponsor') || questionText.includes('visa')) answer = 'Yes';
            else if (questionText.includes('salary') || questionText.includes('pay')) answer = '180000';
            else if (questionText.includes('notice')) answer = '2 weeks';
            else if (questionText.includes('start')) answer = 'Immediately';
            else if (questionText.includes('remote')) answer = 'Yes';
            else if (questionText.includes('relocation')) answer = 'No';
            
            if (answer) {
                input.value = answer;
                input.dispatchEvent(new Event('input', { bubbles: true }));
                input.dispatchEvent(new Event('change', { bubbles: true }));
                filled.push(questionText.substring(0, 40) + ' = ' + answer);
            }
        });
        
        return filled;
    """)
    
    for f in filled:
        print(f"   ✅ {f}")
    return len(filled)

def main():
    driver = setup_driver()
    
    try:
        print("🚀 AI 智能申请 - BGB Group SVP Creative Director")
        
        # 登录
        print("\n🔐 登录...")
        driver.get("https://www.linkedin.com/login")
        time.sleep(2)
        driver.find_element(By.ID, "username").send_keys("wuyuehao2001@outlook.com")
        driver.find_element(By.ID, "password").send_keys("Tommy12345#")
        driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        time.sleep(3)
        print("✅ 登录成功")
        
        # 访问 BGB Group 职位
        print("\n📋 访问 BGB Group 职位...")
        driver.get("https://www.linkedin.com/jobs/view/4169047040")
        time.sleep(5)
        
        # 点击 Easy Apply
        print("\n🖱️ 点击 Easy Apply...")
        driver.execute_script("document.getElementById('jobs-apply-button-id').click()")
        time.sleep(5)
        
        # 处理步骤
        for step in range(8):
            print(f"\n--- Step {step + 1} ---")
            
            # AI 填写
            ai_fill_form(driver)
            
            # 点击按钮
            for btn_text in ['next', 'review', 'submit']:
                result = driver.execute_script("""
                    var buttons = document.querySelectorAll('.artdeco-modal button');
                    for (var btn of buttons) {
                        if (btn.textContent.toLowerCase().includes('""" + btn_text + """') && !btn.disabled) {
                            btn.click();
                            return 'Clicked: ' + btn.textContent.trim();
                        }
                    }
                    return false;
                """)
                if result and 'Clicked' in result:
                    print(f"   {result}")
                    break
            
            time.sleep(4)
            
            # 检查完成
            done = driver.execute_script("""
                return document.body.textContent.includes('Application sent') ||
                       document.querySelector('.jobs-easy-apply-content__success') !== null;
            """)
            if done:
                print("\n🎉 申请成功！")
                break
        
        driver.save_screenshot("ai_bgb_result.png")
        print("\n📸 截图: ai_bgb_result.png")
        
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        driver.save_screenshot("error.png")
    
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
