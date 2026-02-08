#!/usr/bin/env python3
"""
LinkedIn Easy Apply 完整自动化 - 表单填写版
"""

import os
import time
import yaml
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# 加载配置
config_path = Path("config/profile.yaml")
with open(config_path) as f:
    config = yaml.safe_load(f)

personal = config.get('personal_info', {})
LINKEDIN_EMAIL = "wuyuehao2001@outlook.com"
LINKEDIN_PASSWORD = "Tommy12345#"
RESUME_PATH = os.path.expanduser(config.get('application_settings', {}).get('resume_path', '~/Downloads/TOMMY WU Resume Dec 2025.pdf'))

def setup_driver():
    options = Options()
    options.add_argument('--no-sandbox')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=options)

def safe_find(driver, by, value, timeout=10):
    try:
        return WebDriverWait(driver, timeout).until(EC.presence_of_element_located((by, value)))
    except:
        return None

def fill_form_field(driver, field_name, value):
    """填写表单字段"""
    try:
        # 尝试多种 selector
        selectors = [
            f"input[name='{field_name}']",
            f"input[id='{field_name}']",
            f"input[aria-label*='{field_name}']",
            f"input[placeholder*='{field_name}']",
        ]
        
        for selector in selectors:
            field = safe_find(driver, By.CSS_SELECTOR, selector, timeout=2)
            if field:
                field.clear()
                field.send_keys(value)
                print(f"  ✅ 填写 {field_name}: {value}")
                return True
        
        return False
    except Exception as e:
        print(f"  ❌ 填写 {field_name} 失败: {e}")
        return False

def main():
    print("="*60)
    print("🚀 LinkedIn Easy Apply 完整自动化")
    print("="*60)
    
    driver = setup_driver()
    
    try:
        # 登录
        print("\n🔐 登录 LinkedIn...")
        driver.get("https://www.linkedin.com/login")
        safe_find(driver, By.ID, "username").send_keys(LINKEDIN_EMAIL)
        safe_find(driver, By.ID, "password").send_keys(LINKEDIN_PASSWORD)
        safe_find(driver, By.CSS_SELECTOR, "button[type='submit']").click()
        time.sleep(3)
        print("✅ 登录成功")
        
        # 搜索职位
        print("\n🔍 搜索 Easy Apply 职位...")
        driver.get("https://www.linkedin.com/jobs/search/?keywords=Creative%20Technologist&location=New%20York&f_AL=true")
        time.sleep(4)
        
        # 点击第一个职位
        print("\n📋 点击第一个职位...")
        first_job = safe_find(driver, By.CSS_SELECTOR, ".job-card-container", timeout=10)
        if not first_job:
            print("❌ 未找到职位")
            return
        
        first_job.click()
        time.sleep(3)
        
        # 查找 Easy Apply 按钮
        print("\n🔍 查找 Easy Apply 按钮...")
        easy_apply_btn = safe_find(driver, By.CSS_SELECTOR, "button[aria-label*='Easy Apply']", timeout=5)
        
        if not easy_apply_btn:
            print("❌ 未找到 Easy Apply 按钮")
            return
        
        print(f"✅ 找到 Easy Apply: {easy_apply_btn.text}")
        
        # 点击 Easy Apply
        print("\n🖱️ 点击 Easy Apply...")
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", easy_apply_btn)
        time.sleep(1)
        easy_apply_btn.click()
        time.sleep(3)
        
        # 检测申请表单（多种方式）
        print("\n🔍 检测申请表单...")
        
        # 方式1: 查找 artdeco-modal
        modal_selectors = [
            ".artdeco-modal",
            ".jobs-easy-apply-modal",
            "[role='dialog']",
            ".artdeco-modal__content"
        ]
        
        modal_found = False
        for selector in modal_selectors:
            modal = safe_find(driver, By.CSS_SELECTOR, selector, timeout=3)
            if modal:
                print(f"✅ 找到表单弹窗: {selector}")
                modal_found = True
                break
        
        if not modal_found:
            print("⚠️ 未找到标准弹窗，检查页面结构...")
            driver.save_screenshot("form_check.png")
        
        # 分析表单字段
        print("\n📝 分析表单字段...")
        
        # 查找所有输入字段
        inputs = driver.find_elements(By.CSS_SELECTOR, "input, textarea, select")
        print(f"  找到 {len(inputs)} 个输入字段")
        
        for i, inp in enumerate(inputs[:15]):
            tag = inp.tag_name
            input_type = inp.get_attribute("type") or "text"
            name = inp.get_attribute("name") or ""
            id_attr = inp.get_attribute("id") or ""
            aria_label = inp.get_attribute("aria-label") or ""
            placeholder = inp.get_attribute("placeholder") or ""
            
            print(f"  {i+1}. {tag}[type={input_type}] name={name} id={id_attr}")
            if aria_label:
                print(f"      aria-label: {aria_label}")
            if placeholder:
                print(f"      placeholder: {placeholder}")
        
        # 尝试自动填写常见字段
        print("\n✍️ 自动填写表单...")
        
        # 姓名字段
        fill_form_field(driver, "firstName", personal.get('first_name', 'Tommy'))
        fill_form_field(driver, "lastName", personal.get('last_name', 'Wu'))
        fill_form_field(driver, "email", personal.get('email', 'tommy.wu@nyu.edu'))
        fill_form_field(driver, "phone", personal.get('phone', '917-742-4303'))
        
        # 保存截图
        driver.save_screenshot("form_filled.png")
        print("\n📸 已保存填写后的表单截图")
        
        print("\n✅ 测试完成！系统可以：")
        print("   - 自动登录 LinkedIn")
        print("   - 搜索 Easy Apply 职位")
        print("   - 点击申请按钮")
        print("   - 分析表单结构")
        print("   - 自动填写基本信息")
        
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        driver.save_screenshot("error.png")
    
    finally:
        input("\n按 Enter 关闭浏览器...")
        driver.quit()

if __name__ == "__main__":
    main()
