#!/usr/bin/env python3
"""
LinkedIn Easy Apply - 完整自动化表单填写
自动检测并填写所有表单字段
"""

import os
import time
import yaml
import random
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from webdriver_manager.chrome import ChromeDriverManager

# 加载配置
config_path = Path("config/profile.yaml")
with open(config_path) as f:
    config = yaml.safe_load(f)

personal = config.get('personal_info', {})
education = config.get('education', [{}])[0]
work = config.get('work_experience', [{}])[0]

# 个人信息
PROFILE = {
    'first_name': personal.get('first_name', 'Tommy'),
    'last_name': personal.get('last_name', 'Wu'),
    'email': personal.get('email', 'tommy.wu@nyu.edu'),
    'phone': personal.get('phone', '917-742-4303'),
    'linkedin': personal.get('linkedin', 'https://linkedin.com/in/tommywu'),
    'website': personal.get('website', 'https://wlab.tech'),
    'resume_path': os.path.expanduser('~/Downloads/TOMMY WU Resume Dec 2025.pdf'),
    'school': education.get('school', 'NYU Tandon School of Engineering'),
    'degree': education.get('degree', 'M.S.'),
    'field_of_study': education.get('field_of_study', 'Integrated Design & Media'),
    'company': work.get('company', 'WLab Innovations Inc.'),
    'job_title': work.get('job_title', 'Creative Director'),
    'years_experience': '5',
    'visa_required': 'Yes',
}

def random_delay(min_sec=0.5, max_sec=2):
    time.sleep(random.uniform(min_sec, max_sec))

def setup_driver():
    options = Options()
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    options.add_argument('--disable-gpu')
    options.add_argument('--disable-extensions')
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    driver.set_page_load_timeout(30)
    return driver

def safe_find(driver, by, value, timeout=10):
    try:
        return WebDriverWait(driver, timeout).until(EC.presence_of_element_located((by, value)))
    except:
        return None

def find_field_by_label(driver, label_text):
    """通过标签文本查找字段"""
    # 尝试多种方式
    selectors = [
        f"//label[contains(text(), '{label_text}')]/following::input[1]",
        f"//label[contains(text(), '{label_text}')]/following::textarea[1]",
        f"//label[contains(text(), '{label_text}')]/following::select[1]",
        f"//*[contains(@aria-label, '{label_text}')]",
    ]
    
    for selector in selectors:
        try:
            if selector.startswith('//'):
                elem = driver.find_element(By.XPATH, selector)
            else:
                elem = driver.find_element(By.CSS_SELECTOR, selector)
            if elem:
                return elem
        except:
            continue
    return None

def fill_input_field(field, value):
    """安全填写输入字段"""
    try:
        if field.tag_name == 'select':
            select = Select(field)
            # 尝试选择包含值的选项
            options = [opt.text for opt in select.options]
            for opt in options:
                if value.lower() in opt.lower() or opt.lower() in value.lower():
                    select.select_by_visible_text(opt)
                    return True
            # 默认选第一个非空选项
            for opt in options:
                if opt.strip():
                    select.select_by_visible_text(opt)
                    return True
        else:
            field.clear()
            field.send_keys(value)
            return True
    except Exception as e:
        print(f"    ⚠️ 填写失败: {e}")
        return False

def detect_and_fill_form(driver):
    """智能检测并填写表单"""
    print("\n🤖 智能分析表单...")
    
    # 查找所有表单元素
    form_elements = driver.find_elements(By.CSS_SELECTOR, 
        "input:not([type='hidden']):not([type='submit']), textarea, select")
    
    print(f"  找到 {len(form_elements)} 个表单元素")
    
    filled_count = 0
    
    for elem in form_elements:
        try:
            # 获取字段信息
            elem_type = elem.get_attribute("type") or "text"
            elem_name = elem.get_attribute("name") or ""
            elem_id = elem.get_attribute("id") or ""
            elem_placeholder = elem.get_attribute("placeholder") or ""
            aria_label = elem.get_attribute("aria-label") or ""
            
            # 组合所有可能的标识
            identifiers = f"{elem_name} {elem_id} {elem_placeholder} {aria_label}".lower()
            
            value_to_fill = None
            
            # 根据标识匹配填写内容
            if 'first' in identifiers and 'name' in identifiers:
                value_to_fill = PROFILE['first_name']
            elif 'last' in identifiers and 'name' in identifiers:
                value_to_fill = PROFILE['last_name']
            elif 'email' in identifiers:
                value_to_fill = PROFILE['email']
            elif 'phone' in identifiers or 'mobile' in identifiers:
                value_to_fill = PROFILE['phone']
            elif 'linkedin' in identifiers or 'linked' in identifiers:
                value_to_fill = PROFILE['linkedin']
            elif 'website' in identifiers or 'portfolio' in identifiers:
                value_to_fill = PROFILE['website']
            elif 'school' in identifiers or 'university' in identifiers or 'college' in identifiers:
                value_to_fill = PROFILE['school']
            elif 'degree' in identifiers:
                value_to_fill = PROFILE['degree']
            elif 'field' in identifiers and 'study' in identifiers:
                value_to_fill = PROFILE['field_of_study']
            elif 'company' in identifiers or 'employer' in identifiers:
                value_to_fill = PROFILE['company']
            elif 'title' in identifiers and 'job' in identifiers:
                value_to_fill = PROFILE['job_title']
            elif 'experience' in identifiers and 'year' in identifiers:
                value_to_fill = PROFILE['years_experience']
            elif 'visa' in identifiers or 'sponsorship' in identifiers:
                value_to_fill = PROFILE['visa_required']
            
            if value_to_fill:
                if fill_input_field(elem, value_to_fill):
                    print(f"  ✅ {elem_name or elem_id or elem_placeholder}: {value_to_fill}")
                    filled_count += 1
                    random_delay(0.3, 0.8)
            
        except Exception as e:
            continue
    
    return filled_count

def upload_resume(driver, file_path):
    """上传简历"""
    try:
        # 查找文件上传输入
        file_inputs = driver.find_elements(By.CSS_SELECTOR, "input[type='file']")
        
        for file_input in file_inputs:
            if file_input.is_displayed():
                file_input.send_keys(file_path)
                print(f"  ✅ 已上传简历: {os.path.basename(file_path)}")
                random_delay(2, 3)
                return True
        
        return False
    except Exception as e:
        print(f"  ⚠️ 简历上传失败: {e}")
        return False

def find_and_click_next(driver):
    """查找并点击下一步/提交按钮"""
    button_selectors = [
        "button[aria-label='Submit application']",
        "button[aria-label='Next']",
        "button[aria-label='Review']",
        "button[type='submit']",
        ".artdeco-button--primary",
    ]
    
    for selector in button_selectors:
        btn = safe_find(driver, By.CSS_SELECTOR, selector, timeout=2)
        if btn and btn.is_displayed():
            btn_text = btn.text.strip().lower()
            if any(x in btn_text for x in ['submit', 'next', 'review', 'continue', 'save']):
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn)
                random_delay(0.5, 1)
                btn.click()
                print(f"  ✅ 点击按钮: {btn.text}")
                return True
    
    return False

def main():
    print("="*60)
    print("🚀 LinkedIn Easy Apply 全自动表单填写")
    print("="*60)
    
    driver = setup_driver()
    
    try:
        # 登录
        print("\n🔐 登录 LinkedIn...")
        driver.get("https://www.linkedin.com/login")
        random_delay(2, 3)
        
        safe_find(driver, By.ID, "username").send_keys("wuyuehao2001@outlook.com")
        random_delay(0.5, 1)
        safe_find(driver, By.ID, "password").send_keys("Tommy12345#")
        random_delay(0.5, 1)
        safe_find(driver, By.CSS_SELECTOR, "button[type='submit']").click()
        random_delay(3, 4)
        
        if "feed" not in driver.current_url and "linkedin.com" not in driver.current_url:
            print("❌ 登录失败")
            return
        print("✅ 登录成功")
        
        # 搜索 Easy Apply 职位
        print("\n🔍 搜索 Easy Apply 职位...")
        driver.get("https://www.linkedin.com/jobs/search/?keywords=Creative%20Director&location=New%20York&f_AL=true")
        random_delay(4, 5)
        
        # 点击第一个职位
        print("\n📋 选择职位...")
        job_card = safe_find(driver, By.CSS_SELECTOR, ".job-card-container", timeout=10)
        if job_card:
            job_card.click()
            random_delay(3, 4)
        
        # 点击 Easy Apply
        print("\n🖱️ 点击 Easy Apply...")
        easy_apply = safe_find(driver, By.CSS_SELECTOR, "button[aria-label*='Easy Apply']", timeout=5)
        
        if easy_apply:
            print(f"  ✅ 找到 Easy Apply 按钮")
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", easy_apply)
            random_delay(1, 2)
            easy_apply.click()
            random_delay(4, 5)
            
            # 多轮表单填写（处理多步骤申请）
            max_steps = 5
            for step in range(max_steps):
                print(f"\n📄 步骤 {step + 1}:")
                
                # 填写表单
                filled = detect_and_fill_form(driver)
                print(f"  填写了 {filled} 个字段")
                
                # 尝试上传简历
                if os.path.exists(PROFILE['resume_path']):
                    upload_resume(driver, PROFILE['resume_path'])
                
                # 查找并点击下一步
                if find_and_click_next(driver):
                    random_delay(3, 4)
                    
                    # 检查是否完成
                    if "application" in driver.current_url or driver.find_elements(By.XPATH, "//*[contains(text(), 'Application sent')]"):
                        print("\n🎉 申请已提交！")
                        break
                else:
                    print("  ⚠️ 未找到下一步按钮，可能已完成")
                    break
        else:
            print("❌ 未找到 Easy Apply 按钮")
        
        # 保存最终截图
        driver.save_screenshot("final_result.png")
        print("\n📸 已保存最终截图: final_result.png")
        
        print("\n" + "="*60)
        print("✅ 自动化申请流程完成！")
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
