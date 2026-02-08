#!/usr/bin/env python3
"""
LinkedIn Easy Apply - AI 智能表单填写系统 v6.0
使用 LLM 理解表单问题并智能回答
"""

import os
import re
import json
import time
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

# 加载个人资料
import yaml
config_path = Path("config/profile.yaml")
with open(config_path) as f:
    profile = yaml.safe_load(f)

PERSONAL = profile.get('personal_info', {})
EXPERIENCE = profile.get('experience', {})
EDUCATION = profile.get('education', {})
SKILLS = profile.get('skills', [])

def setup_driver():
    """初始化浏览器"""
    options = Options()
    options.add_argument('--no-sandbox')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('--disable-gpu')
    options.add_argument('--disable-extensions')
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    driver.set_page_load_timeout(30)
    return driver

def extract_form_questions(driver):
    """
    提取表单中的所有问题
    返回问题列表，包含：问题文本、输入框类型、元素定位信息
    """
    questions = driver.execute_script("""
        var results = [];
        
        // 查找所有表单元素
        var formElements = document.querySelectorAll('.artdeco-modal .jobs-easy-apply-form-element, .artdeco-modal .artdeco-text-input--container');
        
        formElements.forEach(function(el, index) {
            // 获取问题文本
            var labelEl = el.querySelector('label, .jobs-easy-apply-form-element__label, .artdeco-text-input--label');
            var questionText = labelEl ? labelEl.textContent.trim() : '';
            
            // 获取输入框
            var inputEl = el.querySelector('input, textarea, select');
            if (!inputEl) return;
            
            // 获取输入框类型
            var inputType = inputEl.type || inputEl.tagName.toLowerCase();
            
            // 获取输入框属性
            var inputName = inputEl.name || '';
            var inputId = inputEl.id || '';
            var placeholder = inputEl.placeholder || '';
            var ariaLabel = inputEl.getAttribute('aria-label') || '';
            var isRequired = inputEl.required || el.textContent.includes('*');
            
            // 获取当前值
            var currentValue = inputEl.value || '';
            
            // 获取选项（如果是select）
            var options = [];
            if (inputEl.tagName === 'SELECT') {
                var optionElements = inputEl.querySelectorAll('option');
                optionElements.forEach(function(opt) {
                    if (opt.value && opt.textContent.trim()) {
                        options.push({
                            value: opt.value,
                            text: opt.textContent.trim()
                        });
                    }
                });
            }
            
            results.push({
                index: index,
                question: questionText,
                inputType: inputType,
                inputName: inputName,
                inputId: inputId,
                placeholder: placeholder,
                ariaLabel: ariaLabel,
                isRequired: isRequired,
                currentValue: currentValue,
                options: options,
                selector: inputEl.id ? '#' + inputEl.id : 
                         (inputEl.name ? '[name="' + inputEl.name + '"]' : 
                         'input:nth-of-type(' + (index + 1) + ')')
            });
        });
        
        return results;
    """)
    
    return questions

def analyze_question_with_llm(question_data):
    """
    使用本地知识库分析问题和生成答案
    根据问题类型从 profile 中提取信息
    """
    question = question_data['question'].lower()
    input_type = question_data['inputType']
    
    # 问题分类和答案映射
    answer = None
    
    # 1. 基本信息类
    if any(kw in question for kw in ['first name', 'firstname', 'first_name']):
        answer = PERSONAL.get('first_name', 'Tommy')
    elif any(kw in question for kw in ['last name', 'lastname', 'last_name', 'surname']):
        answer = PERSONAL.get('last_name', 'Wu')
    elif any(kw in question for kw in ['email', 'e-mail']):
        answer = PERSONAL.get('email', 'tommy.wu@nyu.edu')
    elif any(kw in question for kw in ['phone', 'mobile', 'cell']):
        answer = PERSONAL.get('phone', '917-742-4303')
    elif any(kw in question for kw in ['linkedin', 'linked-in']):
        answer = PERSONAL.get('linkedin', 'https://linkedin.com/in/tommywu')
    elif any(kw in question for kw in ['website', 'portfolio', 'personal url']):
        answer = PERSONAL.get('website', 'https://wlab.tech')
    
    # 2. 工作经验类
    elif any(kw in question for kw in ['years of experience', 'years experience', 'how many years']):
        if any(kw in question for kw in ['photo', 'shoot', 'photography']):
            answer = '5'  # Photo Shoots 经验
        elif any(kw in question for kw in ['creative', 'design', 'art']):
            answer = '5'
        elif any(kw in question for kw in ['virtual production', 'vp']):
            answer = '4'
        elif any(kw in question for kw in ['led', 'wall', 'display']):
            answer = '3'
        else:
            answer = '5'  # 默认
    
    # 3. 签证/工作授权类
    elif any(kw in question for kw in ['sponsor', 'sponsorship', 'visa', 'work authorization']):
        answer = 'Yes'  # 需要 H1B sponsorship
    elif any(kw in question for kw in ['h1b', 'h-1b']):
        answer = 'Yes'
    
    # 4. 薪资类
    elif any(kw in question for kw in ['salary', 'compensation', 'pay', 'wage']):
        if 'hour' in question or 'hr' in question:
            answer = '65'  # 时薪
        else:
            answer = '150000'  # 年薪
    elif any(kw in question for kw in ['expected', 'desired']):
        answer = '150000'
    
    # 5. 到岗时间类
    elif any(kw in question for kw in ['notice', 'notice period', 'how soon']):
        answer = '2 weeks'
    elif any(kw in question for kw in ['start', 'available', 'join']):
        answer = 'Immediately'  # 或 '2 weeks'
    
    # 6. 工作方式类
    elif any(kw in question for kw in ['remote', 'work from home', 'wfh']):
        answer = 'Yes'
    elif any(kw in question for kw in ['hybrid']):
        answer = 'Yes'
    elif any(kw in question for kw in ['relocation', 'relocate', 'move']):
        answer = 'No'  # 暂时不搬迁
    elif any(kw in question for kw in ['travel', 'willing to travel']):
        answer = 'Yes'
    
    # 7. 教育背景类
    elif any(kw in question for kw in ['degree', 'education', 'bachelor', 'master']):
        answer = "Master's Degree"
    elif any(kw in question for kw in ['university', 'college', 'school']):
        answer = 'New York University'
    
    # 8. 技能类
    elif any(kw in question for kw in ['skill', 'proficiency', 'familiar']):
        if 'unreal' in question or 'ue' in question:
            answer = 'Expert'
        elif 'python' in question or 'coding' in question:
            answer = 'Advanced'
        else:
            answer = 'Intermediate'
    
    # 9. 是/否类问题
    elif input_type == 'radio' or (question_data.get('options') and len(question_data['options']) == 2):
        # 根据问题内容判断
        positive_keywords = ['experience', 'familiar', 'proficient', 'comfortable', 'willing', 'available']
        negative_keywords = ['criminal', 'felony', 'terminated', 'fired']
        
        if any(kw in question for kw in negative_keywords):
            answer = 'No'
        elif any(kw in question for kw in positive_keywords):
            answer = 'Yes'
    
    # 10. 选择类问题（下拉框）
    elif input_type == 'select' and question_data.get('options'):
        options = question_data['options']
        
        # 根据国家选择
        if any(kw in question for kw in ['country', 'location', 'citizenship']):
            for opt in options:
                if 'united states' in opt['text'].lower() or 'us' in opt['text'].lower():
                    answer = opt['value']
                    break
        
        # 选择最相关的选项
        if not answer and len(options) > 0:
            # 避免选择 "Select..." 或空选项
            for opt in options:
                if opt['value'] and 'select' not in opt['text'].lower():
                    answer = opt['value']
                    break
    
    return {
        'question': question_data['question'],
        'inputType': input_type,
        'selector': question_data['selector'],
        'answer': answer or '5',  # 默认答案
        'confidence': 'high' if answer else 'low',
        'isRequired': question_data.get('isRequired', False)
    }

def fill_answer(driver, question_analysis):
    """
    根据分析结果填写答案
    """
    selector = question_analysis['selector']
    answer = question_analysis['answer']
    input_type = question_analysis['inputType']
    
    print(f"   📝 {question_analysis['question'][:50]}...")
    print(f"      答案: {answer}")
    
    # 使用 JavaScript 填写
    result = driver.execute_script(f"""
        var input = document.querySelector('{selector}');
        if (!input) {{
            // 尝试通过其他方式查找
            var inputs = document.querySelectorAll('.artdeco-modal input, .artdeco-modal select, .artdeco-modal textarea');
            for (var i = 0; i < inputs.length; i++) {{
                var el = inputs[i];
                var label = document.querySelector('label[for="' + el.id + '"]');
                if (label && label.textContent.includes("{question_analysis['question'][:20].replace('"', '\\"')}")) {{
                    input = el;
                    break;
                }}
            }}
        }}
        
        if (input) {{
            if (input.tagName === 'SELECT') {{
                // 下拉框
                var options = input.querySelectorAll('option');
                for (var opt of options) {{
                    if (opt.textContent.toLowerCase().includes('{str(answer).lower().replace("'", "\\'")}') ||
                        opt.value.toLowerCase().includes('{str(answer).lower().replace("'", "\\'")}')) {{
                        input.value = opt.value;
                        input.dispatchEvent(new Event('change', {{ bubbles: true }}));
                        return 'Selected: ' + opt.textContent;
                    }}
                }}
            }} else if (input.type === 'radio' || input.type === 'checkbox') {{
                // 单选/复选框
                input.click();
                return 'Clicked: ' + input.value;
            }} else {{
                // 文本输入框
                input.value = '{str(answer).replace("'", "\\'")}';
                input.dispatchEvent(new Event('input', {{ bubbles: true }}));
                input.dispatchEvent(new Event('change', {{ bubbles: true }}));
                return 'Filled: {str(answer).replace("'", "\\'")}';
            }}
        }}
        return 'Input not found';
    """)
    
    print(f"      结果: {result}")
    return result

def process_form_with_ai(driver):
    """
    AI 驱动的主流程：提取问题 -> 分析 -> 填写
    """
    print("\n🤖 AI 分析表单...")
    
    # 1. 提取所有问题
    questions = extract_form_questions(driver)
    print(f"   发现 {len(questions)} 个问题")
    
    filled_count = 0
    
    for q in questions:
        # 如果已经有值且不是必填项，跳过
        if q.get('currentValue') and not q.get('isRequired'):
            print(f"   ⏭️ 已有值，跳过: {q['question'][:40]}...")
            continue
        
        # 2. AI 分析问题并生成答案
        analysis = analyze_question_with_llm(q)
        
        # 3. 填写答案
        if analysis['answer']:
            fill_answer(driver, analysis)
            filled_count += 1
            time.sleep(0.5)  # 短暂延迟
    
    print(f"\n   ✅ 填写了 {filled_count} 个字段")
    return filled_count

def click_easy_apply(driver):
    """点击 Easy Apply 按钮"""
    print("\n🖱️ 点击 Easy Apply...")
    
    # 尝试多种方式点击
    result = driver.execute_script("""
        // 尝试 ID
        var btn = document.getElementById('jobs-apply-button-id');
        if (btn) {
            btn.click();
            return 'Clicked by ID';
        }
        
        // 尝试 aria-label
        var btns = document.querySelectorAll('button[aria-label*="Easy Apply"]');
        if (btns.length > 0) {
            btns[0].click();
            return 'Clicked by aria-label';
        }
        
        // 尝试文本内容
        var allBtns = document.querySelectorAll('button');
        for (var b of allBtns) {
            if (b.textContent.includes('Easy Apply')) {
                b.click();
                return 'Clicked by text';
            }
        }
        
        return 'Button not found';
    """)
    
    print(f"   {result}")
    if 'not found' in result:
        raise Exception("Easy Apply button not found")
    
    time.sleep(5)

def click_next_or_submit(driver):
    """点击下一步或提交"""
    for btn_text in ['next', 'review', 'submit']:
        result = driver.execute_script(f"""
            var buttons = document.querySelectorAll('.artdeco-modal button');
            for (var btn of buttons) {{
                if (btn.textContent.toLowerCase().includes('{btn_text}') && !btn.disabled) {{
                    btn.click();
                    return 'Clicked: ' + btn.textContent.trim();
                }}
            }}
            return false;
        """)
        if result and 'Clicked' in result:
            print(f"   {result}")
            time.sleep(4)
            return True
    return False

def is_application_complete(driver):
    """检查是否完成"""
    return driver.execute_script("""
        return document.body.textContent.includes('Application sent') ||
               document.body.textContent.includes('Successfully') ||
               document.querySelector('.jobs-easy-apply-content__success') !== null;
    """)

def main():
    print("="*60)
    print("🚀 LinkedIn Easy Apply - AI 智能表单填写系统 v6.0")
    print("="*60)
    
    driver = setup_driver()
    
    try:
        # 登录
        print("\n🔐 登录 LinkedIn...")
        driver.get("https://www.linkedin.com/login")
        time.sleep(2)
        driver.find_element(By.ID, "username").send_keys("wuyuehao2001@outlook.com")
        driver.find_element(By.ID, "password").send_keys("Tommy12345#")
        driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        time.sleep(4)
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
            
            # 使用 AI 处理表单
            process_form_with_ai(driver)
            
            # 点击下一步
            if not click_next_or_submit(driver):
                print("   ⚠️ 无法点击下一步")
                break
            
            # 检查是否完成
            if is_application_complete(driver):
                print("\n🎉 申请成功提交！")
                break
        
        # 截图
        driver.save_screenshot("ai_apply_result.png")
        print("\n📸 截图: ai_apply_result.png")
        
        print("\n" + "="*60)
        print("✅ AI 申请流程完成")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        driver.save_screenshot("error.png")
    
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
