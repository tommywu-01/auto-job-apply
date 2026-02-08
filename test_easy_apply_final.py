#!/usr/bin/env python3
"""
LinkedIn Easy Apply 最终测试
点击职位卡片，然后测试 Easy Apply 按钮
"""

import os
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

LINKEDIN_EMAIL = "wuyuehao2001@outlook.com"
LINKEDIN_PASSWORD = "Tommy12345#"

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

def main():
    print("🚀 LinkedIn Easy Apply 测试")
    driver = setup_driver()
    
    try:
        # 登录
        print("🔐 登录中...")
        driver.get("https://www.linkedin.com/login")
        safe_find(driver, By.ID, "username").send_keys(LINKEDIN_EMAIL)
        safe_find(driver, By.ID, "password").send_keys(LINKEDIN_PASSWORD)
        safe_find(driver, By.CSS_SELECTOR, "button[type='submit']").click()
        time.sleep(3)
        print("✅ 登录成功")
        
        # 访问职位搜索
        print("\n🔍 搜索 Easy Apply 职位...")
        driver.get("https://www.linkedin.com/jobs/search/?keywords=Creative%20Technologist&location=New%20York&f_AL=true")
        time.sleep(4)
        
        # 找到第一个职位卡片并点击
        print("\n📋 点击第一个职位...")
        first_job = safe_find(driver, By.CSS_SELECTOR, ".job-card-container", timeout=10)
        if not first_job:
            print("❌ 未找到职位")
            return
        
        first_job.click()
        time.sleep(3)
        
        # 保存页面
        driver.save_screenshot("job_detail.png")
        print("📸 职位详情已保存")
        
        # 查找 Easy Apply 按钮
        print("\n🔍 查找 Easy Apply 按钮...")
        easy_apply_btn = safe_find(driver, By.CSS_SELECTOR, "button[aria-label*='Easy Apply']", timeout=5)
        
        if easy_apply_btn:
            print(f"✅ 找到 Easy Apply: {easy_apply_btn.text}")
            
            # 点击 Easy Apply
            print("\n🖱️ 点击 Easy Apply...")
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", easy_apply_btn)
            time.sleep(1)
            easy_apply_btn.click()
            time.sleep(3)
            
            # 保存申请表单
            driver.save_screenshot("easy_apply_form.png")
            print("📸 申请表单已保存")
            
            # 检查弹窗
            modal = safe_find(driver, By.CSS_SELECTOR, ".jobs-easy-apply-modal", timeout=5)
            if modal:
                print("✅ Easy Apply 弹窗已打开！")
                
                # 分析表单
                inputs = driver.find_elements(By.CSS_SELECTOR, ".jobs-easy-apply-modal input, .jobs-easy-apply-modal textarea, .jobs-easy-apply-modal select")
                print(f"\n📝 表单字段数: {len(inputs)}")
                
                for i, inp in enumerate(inputs[:10]):
                    tag = inp.tag_name
                    name = inp.get_attribute("name") or inp.get_attribute("id") or "unnamed"
                    print(f"  {i+1}. {tag}: {name}")
                
                print("\n✅ 测试成功！系统可以处理 Easy Apply 表单")
            else:
                print("⚠️ 未找到 Easy Apply 弹窗")
        else:
            print("❌ 未找到 Easy Apply 按钮")
            # 检查是否是外部申请
            external_btn = safe_find(driver, By.CSS_SELECTOR, "button[aria-label*='Apply']", timeout=3)
            if external_btn:
                print(f"  找到外部申请按钮: {external_btn.text}")
    
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        driver.save_screenshot("error.png")
    
    finally:
        input("\n按 Enter 关闭...")
        driver.quit()

if __name__ == "__main__":
    main()
