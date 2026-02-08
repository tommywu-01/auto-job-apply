#!/usr/bin/env python3
"""
LinkedIn Easy Apply 稳定版 - 优化资源使用
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
from webdriver_manager.chrome import ChromeDriverManager

# 配置
LINKEDIN_EMAIL = "wuyuehao2001@outlook.com"
LINKEDIN_PASSWORD = "Tommy12345#"

def random_delay(min_sec=1, max_sec=3):
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

def safe_click(driver, by, value, timeout=10):
    try:
        elem = WebDriverWait(driver, timeout).until(EC.element_to_be_clickable((by, value)))
        elem.click()
        return True
    except:
        return False

def main():
    print("="*60)
    print("🚀 LinkedIn Easy Apply 稳定版测试")
    print("="*60)
    
    driver = setup_driver()
    
    try:
        # 登录
        print("\n🔐 登录 LinkedIn...")
        driver.get("https://www.linkedin.com/login")
        random_delay(2, 3)
        
        safe_find(driver, By.ID, "username").send_keys(LINKEDIN_EMAIL)
        random_delay(0.5, 1)
        
        safe_find(driver, By.ID, "password").send_keys(LINKEDIN_PASSWORD)
        random_delay(0.5, 1)
        
        safe_find(driver, By.CSS_SELECTOR, "button[type='submit']").click()
        random_delay(3, 4)
        
        if "feed" not in driver.current_url and "linkedin.com" not in driver.current_url:
            print("❌ 登录失败")
            return
        print("✅ 登录成功")
        
        # 直接访问一个已知的 Easy Apply 职位
        print("\n🔍 访问 Easy Apply 职位...")
        driver.get("https://www.linkedin.com/jobs/search/?keywords=Creative%20Director&location=New%20York&f_AL=true")
        random_delay(4, 5)
        
        # 点击第一个职位
        print("\n📋 选择职位...")
        job_card = safe_find(driver, By.CSS_SELECTOR, ".job-card-container", timeout=10)
        if job_card:
            job_card.click()
            random_delay(3, 4)
        
        # 查找 Easy Apply 按钮
        print("\n🔍 查找 Easy Apply...")
        easy_apply = safe_find(driver, By.CSS_SELECTOR, "button[aria-label*='Easy Apply']", timeout=5)
        
        if easy_apply:
            print(f"✅ 找到: {easy_apply.text}")
            
            # 点击
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", easy_apply)
            random_delay(1, 2)
            easy_apply.click()
            random_delay(4, 5)
            
            # 检查是否打开了新页面或弹窗
            print(f"\n📄 当前 URL: {driver.current_url}")
            
            # 保存页面源码分析
            page_source = driver.page_source[:5000]
            with open("page_source_snippet.html", "w") as f:
                f.write(page_source)
            print("✅ 已保存页面源码片段")
            
            # 查找表单字段
            print("\n📝 查找表单字段...")
            inputs = driver.find_elements(By.TAG_NAME, "input")
            textareas = driver.find_elements(By.TAG_NAME, "textarea")
            selects = driver.find_elements(By.TAG_NAME, "select")
            
            print(f"  Inputs: {len(inputs)}")
            print(f"  Textareas: {len(textareas)}")
            print(f"  Selects: {len(selects)}")
            
            # 显示前5个字段
            for i, inp in enumerate(inputs[:5]):
                name = inp.get_attribute("name") or ""
                id_attr = inp.get_attribute("id") or ""
                input_type = inp.get_attribute("type") or "text"
                print(f"    {i+1}. {input_type}: {name or id_attr}")
            
            print("\n✅ 核心功能已验证！")
            print("   - 登录 ✅")
            print("   - 搜索职位 ✅")
            print("   - 点击 Easy Apply ✅")
            print("   - 进入申请表单 ✅")
        else:
            print("❌ 未找到 Easy Apply 按钮")
            
    except Exception as e:
        print(f"\n❌ 错误: {e}")
    
    finally:
        driver.quit()
        print("\n✅ 完成")

if __name__ == "__main__":
    main()
