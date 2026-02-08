#!/usr/bin/env python3
"""
LinkedIn Easy Apply - 调试版
分析页面结构，找到弹窗
"""

import os
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

def setup_driver():
    options = Options()
    options.add_argument('--no-sandbox')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36')
    
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=options)

def main():
    driver = setup_driver()
    
    try:
        # 登录
        print("🔐 登录...")
        driver.get("https://www.linkedin.com/login")
        time.sleep(2)
        driver.find_element(By.ID, "username").send_keys("wuyuehao2001@outlook.com")
        driver.find_element(By.ID, "password").send_keys("Tommy12345#")
        driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        time.sleep(3)
        
        # 访问职位
        print("\n📋 访问职位...")
        driver.get("https://www.linkedin.com/jobs/search/?keywords=Creative%20Director&f_AL=true")
        time.sleep(4)
        
        # 点击职位卡片
        job = driver.find_element(By.CSS_SELECTOR, ".job-card-container")
        job.click()
        time.sleep(3)
        
        # 保存点击前的页面源码
        with open("before_click.html", "w") as f:
            f.write(driver.page_source[:10000])
        print("✅ 已保存点击前的页面源码: before_click.html")
        
        # 点击 Easy Apply
        print("\n🖱️ 点击 Easy Apply...")
        easy_apply = driver.find_element(By.CSS_SELECTOR, "button[aria-label*='Easy Apply']")
        easy_apply.click()
        time.sleep(6)  # 等待弹窗
        
        # 保存点击后的页面源码
        with open("after_click.html", "w") as f:
            f.write(driver.page_source[:20000])
        print("✅ 已保存点击后的页面源码: after_click.html")
        
        # 分析关键元素
        print("\n🔍 分析页面元素:")
        
        # 查找 artdeco-modal
        modals = driver.find_elements(By.CSS_SELECTOR, ".artdeco-modal")
        print(f"  artdeco-modal: {len(modals)}")
        
        # 查找 role='dialog'
        dialogs = driver.find_elements(By.CSS_SELECTOR, "[role='dialog']")
        print(f"  role='dialog': {len(dialogs)}")
        
        # 查找 jobs-easy-apply-content
        contents = driver.find_elements(By.CSS_SELECTOR, ".jobs-easy-apply-content")
        print(f"  jobs-easy-apply-content: {len(contents)}")
        
        # 查找所有 dialog 元素
        all_dialogs = driver.find_elements(By.TAG_NAME, "dialog")
        print(f"  dialog tags: {len(all_dialogs)}")
        
        # 查找 body 的直接子元素
        body_children = driver.find_elements(By.CSS_SELECTOR, "body > *")
        print(f"\n  Body 直接子元素:")
        for child in body_children[-5:]:  # 最后5个
            class_name = child.get_attribute("class") or ""
            tag = child.tag_name
            print(f"    {tag}: {class_name[:50]}")
        
        driver.save_screenshot("debug.png")
        print("\n📸 截图: debug.png")
        
    except Exception as e:
        print(f"❌ 错误: {e}")
    
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
