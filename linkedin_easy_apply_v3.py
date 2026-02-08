#!/usr/bin/env python3
"""
LinkedIn Easy Apply - 智能回答问题版 v3.0
自动检测并回答申请表单问题
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
experience = config.get('experience', {})

PROFILE = {
    'first_name': personal.get('first_name', 'Tommy'),
    'last_name': personal.get('last_name', 'Wu'),
    'email': personal.get('email', 'tommy.wu@nyu.edu'),
    'phone': personal.get('phone', '917-742-4303'),
    'years_experience': 5,  # 默认值
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
    print("\n🔐 登录...")
    driver.get("https://www.linkedin.com/login")
    time.sleep(2)
    driver.find_element(By.ID, "username").send_keys("wuyuehao2001@outlook.com")
    driver.find_element(By.ID, "password").send_keys("Tommy12345#")
    driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
    time.sleep(3)
    print("✅ 登录成功")

def click_easy_apply_js(driver):
    """点击 Easy Apply"""
    print("\n🖱️ 点击 Easy Apply...")
    driver.execute_script("document.getElementById('jobs-apply-button-id').click()")
    time.sleep(5)

def detect_and_answer_questions(driver):
    """检测并回答问题"""
    print("\n🤔 检测问题...")
    
    questions = driver.execute_script("""
        var results = [];
        var questions = document.querySelectorAll('.artdeco-modal .jobs-easy-apply-form-element');
        
        questions.forEach(function(q) {
            var label = q.querySelector('label, .jobs-easy-apply-form-element__label, .artdeco-text-input--label');
            var input = q.querySelector('input, textarea, select');
            
            if (label && input) {
                results.push({
                    question: label.textContent.trim(),
                    inputType: input.type || input.tagName.toLowerCase(),
                    inputName: input.name || '',
                    required: input.required
                });
            }
        });
        
        return results;
    """)
    
    print(f"   发现 {len(questions)} 个问题")
    
    for q in questions:
        question_text = q.get('question', '').lower()
        print(f"   Q: {q.get('question')}")
        
        # 根据问题类型回答
        answer = None
        
        if 'year' in question_text and 'experience' in question_text:
            if 'photo' in question_text or 'shoot' in question_text:
                answer = '3'  # Photo Shoots 经验
            else:
                answer = str(PROFILE['years_experience'])
        elif 'sponsor' in question_text or 'visa' in question_text:
            answer = 'Yes'  # 需要 H1B sponsorship
        elif 'salary' in question_text or 'compensation' in question_text:
            answer = '150000'  # 期望薪资
        elif 'notice' in question_text or 'start' in question_text:
            answer = '2 weeks'  # 两周通知期
        elif 'remote' in question_text or 'hybrid' in question_text:
            answer = 'Yes'
        elif 'relocation' in question_text:
            answer = 'No'  # 暂时不搬迁
        
        if answer:
            print(f"   A: {answer}")
            # 填写答案
            driver.execute_script("""
                var questions = document.querySelectorAll('.artdeco-modal .jobs-easy-apply-form-element');
                questions.forEach(function(q) {
                    var label = q.querySelector('label, .jobs-easy-apply-form-element__label');
                    if (label && label.textContent.toLowerCase().includes('""" + question_text[:20].replace("'", "\\'") + """')) {
                        var input = q.querySelector('input, textarea, select');
                        if (input) {
                            input.value = '""" + str(answer).replace("'", "\\'") + """';
                            input.dispatchEvent(new Event('input', { bubbles: true }));
                            input.dispatchEvent(new Event('change', { bubbles: true }));
                        }
                    }
                });
            """)
    
    return len(questions)

def click_button_js(driver, button_text):
    """点击按钮"""
    result = driver.execute_script("""
        var buttons = document.querySelectorAll('.artdeco-modal button');
        for (var btn of buttons) {
            var text = btn.textContent.toLowerCase();
            if (text.includes('""" + button_text.lower() + """') && !btn.disabled) {
                btn.click();
                return 'Clicked: ' + btn.textContent.trim();
            }
        }
        return 'Button not found';
    """)
    print(f"   {result}")
    time.sleep(3)
    return 'not found' not in result.lower()

def check_errors(driver):
    """检查是否有错误"""
    errors = driver.execute_script("""
        var errorElements = document.querySelectorAll('.artdeco-inline-feedback__message, .jobs-easy-apply-form-element__error');
        return Array.from(errorElements).map(e => e.textContent.trim()).filter(t => t.length > 0);
    """)
    return errors

def main():
    print("="*60)
    print("🚀 LinkedIn Easy Apply - 智能回答问题版 v3.0")
    print("="*60)
    
    driver = setup_driver()
    
    try:
        login(driver)
        
        print("\n📋 访问职位...")
        driver.get("https://www.linkedin.com/jobs/view/4361442478")
        time.sleep(5)
        
        click_easy_apply_js(driver)
        
        # 多步骤处理
        for step in range(10):
            print(f"\n--- Step {step + 1} ---")
            
            # 获取当前步骤标题
            title = driver.execute_script("""
                var h = document.querySelector('.artdeco-modal h2, .artdeco-modal h3');
                return h ? h.textContent.trim() : 'Unknown';
            """)
            print(f"📄 {title}")
            
            # 回答问题
            question_count = detect_and_answer_questions(driver)
            
            # 检查错误
            errors = check_errors(driver)
            if errors:
                print(f"   ⚠️ 错误: {errors}")
            
            # 尝试点击 Next/Review/Submit
            for btn_text in ['next', 'review', 'submit', 'send']:
                if click_button_js(driver, btn_text):
                    break
            
            # 检查是否完成
            done = driver.execute_script("""
                return document.body.textContent.includes('Application sent') ||
                       document.body.textContent.includes('Successfully') ||
                       document.querySelector('.jobs-easy-apply-content__success') !== null;
            """)
            
            if done:
                print("\n🎉 申请成功提交！")
                break
        
        driver.save_screenshot("smart_apply_result.png")
        print("\n📸 截图: smart_apply_result.png")
        
        print("\n" + "="*60)
        print("✅ 流程完成")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        driver.save_screenshot("error.png")
    
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
