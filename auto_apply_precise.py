#!/usr/bin/env python3
"""
LinkedIn Easy Apply - 弹窗表单自动填写（精准版）
只处理 Easy Apply 弹窗内的表单元素
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

PROFILE = {
    'first_name': personal.get('first_name', 'Tommy'),
    'last_name': personal.get('last_name', 'Wu'),
    'email': personal.get('email', 'tommy.wu@nyu.edu'),
    'phone': personal.get('phone', '917-742-4303'),
    'linkedin': personal.get('linkedin', 'https://linkedin.com/in/tommywu'),
    'website': personal.get('website', 'https://wlab.tech'),
    'resume_path': os.path.expanduser('~/Downloads/TOMMY WU Resume Dec 2025.pdf'),
}

def random_delay(min_sec=0.5, max_sec=1.5):
    time.sleep(random.uniform(min_sec, max_sec))

def setup_driver():
    options = Options()
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    options.add_argument('--disable-gpu')
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    driver.set_page_load_timeout(30)
    return driver

def safe_find(driver, by, value, timeout=10):
    try:
        return WebDriverWait(driver, timeout).until(EC.presence_of_element_located((by, value)))
    except:
        return None

def get_field_info(elem):
    """提取字段信息"""
    info = {
        'tag': elem.tag_name,
        'type': elem.get_attribute('type') or 'text',
        'name': elem.get_attribute('name') or '',
        'id': elem.get_attribute('id') or '',
        'placeholder': elem.get_attribute('placeholder') or '',
        'aria_label': elem.get_attribute('aria-label') or '',
        'class': elem.get_attribute('class') or '',
    }
    return info

def get_field_identifier(info):
    """获取字段标识（用于匹配）"""
    identifiers = f"{info['name']} {info['id']} {info['placeholder']} {info['aria_label']}".lower()
    return identifiers

def get_value_for_field(identifiers):
    """根据标识获取应填写的值"""
    # 姓名字段
    if any(x in identifiers for x in ['first', 'fname', 'first_name']):
        return PROFILE['first_name']
    if any(x in identifiers for x in ['last', 'lname', 'last_name', 'surname']):
        return PROFILE['last_name']
    
    # 邮箱
    if 'email' in identifiers or 'e-mail' in identifiers:
        return PROFILE['email']
    
    # 电话
    if any(x in identifiers for x in ['phone', 'mobile', 'cell', 'tel']):
        return PROFILE['phone']
    
    # LinkedIn
    if 'linkedin' in identifiers or 'linked-in' in identifiers:
        return PROFILE['linkedin']
    
    # 网站/Portfolio
    if any(x in identifiers for x in ['website', 'portfolio', 'github', 'url']):
        return PROFILE['website']
    
    return None

def fill_field(elem, value):
    """安全填写字段"""
    try:
        # 确保元素可见且可交互
        if not elem.is_displayed():
            return False
        
        # 滚动到元素
        elem.location_once_scrolled_into_view
        random_delay(0.2, 0.5)
        
        tag = elem.tag_name
        
        if tag == 'select':
            select = Select(elem)
            options = [opt.text for opt in select.options]
            
            # 尝试匹配值
            for opt in options:
                if value.lower() in opt.lower():
                    select.select_by_visible_text(opt)
                    return True
            
            # 选择第一个非空选项
            for opt in options:
                if opt.strip() and opt.strip() != 'Select...':
                    select.select_by_visible_text(opt)
                    return True
        else:
            elem.clear()
            random_delay(0.1, 0.3)
            elem.send_keys(value)
            return True
            
    except Exception as e:
        return False

def find_easy_apply_modal(driver):
    """查找 Easy Apply 弹窗"""
    modal_selectors = [
        ".artdeco-modal",
        ".jobs-easy-apply-modal",
        ".artdeco-modal__content",
        "[role='dialog'] .jobs-easy-apply-content",
    ]
    
    for selector in modal_selectors:
        try:
            modal = driver.find_element(By.CSS_SELECTOR, selector)
            if modal.is_displayed():
                return modal
        except:
            continue
    return None

def fill_easy_apply_form(driver):
    """填写 Easy Apply 弹窗内的表单"""
    print("\n📝 查找 Easy Apply 弹窗...")
    
    # 等待弹窗出现
    modal = None
    for _ in range(5):
        modal = find_easy_apply_modal(driver)
        if modal:
            break
        random_delay(1, 2)
    
    if not modal:
        print("⚠️ 未找到 Easy Apply 弹窗")
        return 0
    
    print("✅ 找到 Easy Apply 弹窗")
    
    # 只查找弹窗内的表单元素
    form_elements = modal.find_elements(By.CSS_SELECTOR, 
        "input:not([type='hidden']):not([type='submit']):not([type='button']), textarea, select")
    
    print(f"  弹窗内有 {len(form_elements)} 个表单字段")
    
    filled_count = 0
    
    for elem in form_elements:
        try:
            info = get_field_info(elem)
            identifiers = get_field_identifier(info)
            
            value = get_value_for_field(identifiers)
            
            if value:
                if fill_field(elem, value):
                    field_name = info['name'] or info['id'] or info['placeholder'] or info['aria_label']
                    print(f"    ✅ {field_name[:40]}: {value}")
                    filled_count += 1
                    random_delay(0.3, 0.8)
        except:
            continue
    
    return filled_count

def click_next_or_submit(driver):
    """点击下一步或提交按钮"""
    button_patterns = [
        ("button[aria-label='Next']", "Next"),
        ("button[aria-label='Review']", "Review"),
        ("button[aria-label='Submit application']", "Submit"),
        (".artdeco-button--primary", None),
    ]
    
    for selector, expected_text in button_patterns:
        try:
            buttons = driver.find_elements(By.CSS_SELECTOR, selector)
            for btn in buttons:
                if btn.is_displayed():
                    btn_text = btn.text.strip().lower()
                    if expected_text is None or expected_text.lower() in btn_text:
                        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn)
                        random_delay(0.5, 1)
                        btn.click()
                        print(f"    ✅ 点击: {btn.text}")
                        return True
        except:
            continue
    
    return False

def main():
    print("="*60)
    print("🚀 LinkedIn Easy Apply 表单自动填写 v2")
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
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", easy_apply)
            random_delay(1, 2)
            easy_apply.click()
            print("✅ 已点击 Easy Apply")
            random_delay(4, 6)
            
            # 多轮填写（处理多步骤表单）
            for step in range(1, 6):
                print(f"\n📄 步骤 {step}:")
                
                filled = fill_easy_apply_form(driver)
                print(f"    填写了 {filled} 个字段")
                
                # 尝试点击下一步
                if click_next_or_submit(driver):
                    random_delay(3, 5)
                    
                    # 检查是否已完成
                    if any(x in driver.page_source.lower() for x in ['application sent', 'submitted', 'success']):
                        print("\n🎉 申请已提交！")
                        break
                else:
                    print("    ⚠️ 未找到下一步按钮")
                    break
        else:
            print("❌ 未找到 Easy Apply 按钮")
        
        driver.save_screenshot("final_result.png")
        print("\n📸 已保存截图")
        
        print("\n" + "="*60)
        print("✅ 自动化流程完成！")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        driver.save_screenshot("error.png")
    
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
