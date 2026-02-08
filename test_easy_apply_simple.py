#!/usr/bin/env python3
"""
LinkedIn Easy Apply 简化测试 - 直接测试申请流程
"""

import os
import sys
import time
import yaml
import random
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager

# ============ 配置 ============
LINKEDIN_EMAIL = "wuyuehao2001@outlook.com"
LINKEDIN_PASSWORD = "Tommy12345#"

# 测试职位 - Creative Technologist at Kyndryl (已验证开放)
TEST_JOB_URL = "https://www.linkedin.com/jobs/view/creative-technologist-at-kyndryl-4368403070"

def setup_driver():
    options = Options()
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    # 非无头模式观察
    # options.add_argument('--headless=new')
    
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=options)

def safe_find(driver, by, value, timeout=10):
    try:
        return WebDriverWait(driver, timeout).until(EC.presence_of_element_located((by, value)))
    except:
        return None

def safe_click(driver, by, value, timeout=10):
    try:
        elem = WebDriverWait(driver, timeout).until(EC.element_to_be_clickable((by, value)))
        elem.click()
        return True
    except:
        return False

def linkedin_login(driver):
    print("🔐 登录 LinkedIn...")
    driver.get("https://www.linkedin.com/login")
    time.sleep(2)
    
    # 输入邮箱
    email_field = safe_find(driver, By.ID, "username")
    if email_field:
        email_field.send_keys(LINKEDIN_EMAIL)
    
    # 输入密码
    password_field = safe_find(driver, By.ID, "password")
    if password_field:
        password_field.send_keys(LINKEDIN_PASSWORD)
    
    # 点击登录
    login_btn = safe_find(driver, By.CSS_SELECTOR, "button[type='submit']")
    if login_btn:
        login_btn.click()
        time.sleep(3)
    
    if "feed" in driver.current_url:
        print("✅ 登录成功")
        return True
    return False

def test_easy_apply(driver):
    print(f"\n🎯 访问测试职位...")
    driver.get(TEST_JOB_URL)
    time.sleep(3)
    
    # 保存页面
    driver.save_screenshot("test_job_page.png")
    with open("test_job_page.html", "w") as f:
        f.write(driver.page_source)
    print("📸 页面已保存")
    
    # 检查是否是 Easy Apply
    print("\n🔍 检查申请类型...")
    
    # 查找 Easy Apply 按钮
    easy_apply_selectors = [
        "button[aria-label*='Easy Apply']",
        "button[aria-label*='easy apply']",
        "button.jobs-apply-button:not([aria-label*='External'])"
    ]
    
    is_easy_apply = False
    for selector in easy_apply_selectors:
        btn = safe_find(driver, By.CSS_SELECTOR, selector, timeout=3)
        if btn:
            print(f"✅ 找到 Easy Apply 按钮: {btn.text}")
            is_easy_apply = True
            break
    
    if not is_easy_apply:
        print("⚠️ 这不是 Easy Apply 职位（是外部申请）")
        # 检查是否有外部申请标识
        external_indicators = driver.find_elements(By.CSS_SELECTOR, "[data-control-name='jobdetails_topcard_inapply']")
        if external_indicators:
            print("  确认：外部申请职位")
        return False
    
    # 找到 Easy Apply 按钮，点击它
    print("\n🖱️ 点击 Easy Apply 按钮...")
    apply_btn = safe_find(driver, By.CSS_SELECTOR, "button[aria-label*='Easy Apply']", timeout=5)
    if apply_btn:
        # 滚动到按钮位置确保可点击
        driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", apply_btn)
        time.sleep(1)
        apply_btn.click()
        time.sleep(3)
        
        # 保存申请表单截图
        driver.save_screenshot("apply_form.png")
        print("📸 申请表单截图已保存")
        
        # 检查弹窗
        modal = safe_find(driver, By.CSS_SELECTOR, ".jobs-easy-apply-modal", timeout=5)
        if modal:
            print("✅ Easy Apply 弹窗已打开！")
            
            # 分析表单字段
            print("\n📝 分析表单字段...")
            
            # 查找所有输入字段
            inputs = driver.find_elements(By.CSS_SELECTOR, ".jobs-easy-apply-modal input")
            print(f"  找到 {len(inputs)} 个 input 元素")
            
            for inp in inputs[:15]:
                name = inp.get_attribute("name") or ""
                id_attr = inp.get_attribute("id") or ""
                input_type = inp.get_attribute("type") or "text"
                if name or id_attr:
                    print(f"    - name={name}, id={id_attr}, type={input_type}")
            
            # 查找文本域
            textareas = driver.find_elements(By.CSS_SELECTOR, ".jobs-easy-apply-modal textarea")
            print(f"  找到 {len(textareas)} 个 textarea 元素")
            
            # 查找下拉框
            selects = driver.find_elements(By.CSS_SELECTOR, ".jobs-easy-apply-modal select")
            print(f"  找到 {len(selects)} 个 select 元素")
            
            print("\n✅ Easy Apply 表单分析完成！")
            return True
        else:
            print("⚠️ 未找到 Easy Apply 弹窗")
            return False
    
    return False

def main():
    print("="*60)
    print("🚀 LinkedIn Easy Apply 简化测试")
    print("="*60)
    
    driver = setup_driver()
    
    try:
        # 登录
        if not linkedin_login(driver):
            print("❌ 登录失败")
            return
        
        # 测试申请
        test_easy_apply(driver)
        
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        input("\n按 Enter 关闭浏览器...")
        driver.quit()
        print("\n✅ 完成")

if __name__ == "__main__":
    main()
