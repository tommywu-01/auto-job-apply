#!/usr/bin/env python3
"""
LinkedIn Easy Apply - AI 增强版 v5.0
结合已验证的稳定流程 + AI 智能回答问题
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
    profile = yaml.safe_load(f)

PERSONAL = profile.get('personal_info', {})

# AI 知识库 - 问题类型到答案的映射
AI_ANSWERS = {
    # 基本信息
    'first name': PERSONAL.get('first_name', 'Tommy'),
    'last name': PERSONAL.get('last_name', 'Wu'),
    'email': PERSONAL.get('email', 'tommy.wu@nyu.edu'),
    'phone': PERSONAL.get('phone', '917-742-4303'),
    
    # 经验类
    'photo shoot': '5',
    'years of experience': '5',
    'creative director': '5',
    'virtual production': '4',
    'led wall': '3',
    
    # 签证/工作授权
    'sponsorship': 'Yes',
    'visa': 'Yes',
    'work authorization': 'Yes',
    'h1b': 'Yes',
    
    # 薪资
    'salary': '150000',
    'compensation': '150000',
    'pay': '150000',
    
    # 到岗时间
    'notice': '2 weeks',
    'start': 'Immediately',
    'available': 'Immediately',
    
    # 工作方式
    'remote': 'Yes',
    'hybrid': 'Yes',
    'relocation': 'No',
    'travel': 'Yes',
    
    # 默认
    'default': '5'
}

def setup_driver():
    options = Options()
    options.add_argument('--no-sandbox')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('--disable-gpu')
    options.add_argument('--disable-extensions')
    
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=options)

def ai_analyze_and_fill(driver):
    """
    AI 分析表单并填写
    1. 检测所有输入字段
    2. 分析问题类型
    3. 从知识库获取答案
    4. 填写
    """
    print("\n🤖 AI 分析表单...")
    
    filled = driver.execute_script("""
        var filled = [];
        
        // 查找所有输入框
        var inputs = document.querySelectorAll('.artdeco-modal input[type="text"], 
                                              .artdeco-modal input[type="number"], 
                                              .artdeco-modal textarea,
                                              .artdeco-modal select');
        
        inputs.forEach(function(input) {
            if (!input.offsetParent) return; // 跳过不可见元素
            
            // 获取问题文本
            var questionText = '';
            var label = document.querySelector('label[for="' + input.id + '"]');
            if (label) {
                questionText = label.textContent.toLowerCase();
            } else {
                var parent = input.closest('.jobs-easy-apply-form-element, .artdeco-text-input--container');
                if (parent) {
                    var labelEl = parent.querySelector('label, .jobs-easy-apply-form-element__label');
                    if (labelEl) questionText = labelEl.textContent.toLowerCase();
                }
            }
            
            // AI 匹配答案
            var answer = '';
            var matchedKey = '';
            
            // 关键词匹配
            var keywords = {
                'photo': 'photo shoot',
                'shoot': 'photo shoot',
                'years': 'years of experience',
                'experience': 'years of experience',
                'sponsor': 'sponsorship',
                'visa': 'visa',
                'authorization': 'work authorization',
                'salary': 'salary',
                'compensation': 'compensation',
                'pay': 'pay',
                'notice': 'notice',
                'start': 'start',
                'remote': 'remote',
                'hybrid': 'hybrid',
                'relocation': 'relocation',
                'travel': 'travel',
                'first name': 'first name',
                'last name': 'last name',
                'email': 'email',
                'phone': 'phone'
            };
            
            for (var kw in keywords) {
                if (questionText.includes(kw)) {
                    matchedKey = keywords[kw];
                    break;
                }
            }
            
            // 从 AI_ANSWERS 获取答案 (Python 会注入这个变量)
            if (matchedKey && AI_ANSWERS[matchedKey]) {
                answer = AI_ANSWERS[matchedKey];
            }
            
            // 填写
            if (answer && !input.value) {
                if (input.tagName === 'SELECT') {
                    // 处理下拉框
                    var options = input.querySelectorAll('option');
                    for (var opt of options) {
                        if (opt.textContent.toLowerCase().includes(answer.toLowerCase()) ||
                            opt.value.toLowerCase().includes(answer.toLowerCase())) {
                            input.value = opt.value;
                            input.dispatchEvent(new Event('change', { bubbles: true }));
                            filled.push(questionText.substring(0, 30) + ' = ' + answer);
                            break;
                        }
                    }
                } else {
                    // 文本输入
                    input.value = answer;
                    input.dispatchEvent(new Event('input', { bubbles: true }));
                    input.dispatchEvent(new Event('change', { bubbles: true }));
                    filled.push(questionText.substring(0, 30) + ' = ' + answer);
                }
            }
        });
        
        return filled;
    """)
    
    for f in filled:
        print(f"   ✅ {f}")
    
    return len(filled)

def click_easy_apply(driver):
    """点击 Easy Apply"""
    print("\n🖱️ 点击 Easy Apply...")
    driver.execute_script("document.getElementById('jobs-apply-button-id').click()")
    time.sleep(5)

def click_button(driver, text):
    """点击按钮"""
    result = driver.execute_script("""
        var buttons = document.querySelectorAll('.artdeco-modal button');
        for (var btn of buttons) {
            if (btn.textContent.toLowerCase().includes('""" + text + """') && !btn.disabled) {
                btn.click();
                return 'Clicked: ' + btn.textContent.trim();
            }
        }
        return 'Not found';
    """)
    print(f"   {result}")
    time.sleep(3)
    return 'Not found' not in result

def is_complete(driver):
    """检查是否完成"""
    return driver.execute_script("""
        return document.body.textContent.includes('Application sent') ||
               document.querySelector('.jobs-easy-apply-content__success') !== null;
    """)

def main():
    print("="*60)
    print("🚀 LinkedIn Easy Apply - AI 增强版 v5.0")
    print("="*60)
    
    driver = setup_driver()
    
    try:
        # 登录
        print("\n🔐 登录...")
        driver.get("https://www.linkedin.com/login")
        time.sleep(2)
        driver.find_element(By.ID, "username").send_keys("wuyuehao2001@outlook.com")
        driver.find_element(By.ID, "password").send_keys("Tommy12345#")
        driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        time.sleep(3)
        print("✅ 登录成功")
        
        # 访问职位
        print("\n📋 访问职位...")
        driver.get("https://www.linkedin.com/jobs/view/4361442478")
        time.sleep(5)
        
        # 点击 Easy Apply
        click_easy_apply(driver)
        
        # 多步骤处理
        for step in range(8):
            print(f"\n--- Step {step + 1} ---")
            
            # AI 填写表单
            ai_analyze_and_fill(driver)
            
            # 点击按钮
            for btn in ['next', 'review', 'submit']:
                if click_button(driver, btn):
                    break
            
            # 检查完成
            if is_complete(driver):
                print("\n🎉 申请成功！")
                break
        
        driver.save_screenshot("ai_result.png")
        print("\n📸 截图: ai_result.png")
        
        print("\n" + "="*60)
        print("✅ 完成")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        driver.save_screenshot("error.png")
    
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
