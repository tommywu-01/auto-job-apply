#!/usr/bin/env python3
"""
搜索并测试 LinkedIn Easy Apply 职位
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

LINKEDIN_EMAIL = "wuyuehao2001@outlook.com"
LINKEDIN_PASSWORD = "Tommy12345#"

def setup_driver():
    options = Options()
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    # options.add_argument('--headless=new')
    
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=options)

def safe_find(driver, by, value, timeout=10):
    try:
        return WebDriverWait(driver, timeout).until(EC.presence_of_element_located((by, value)))
    except:
        return None

def linkedin_login(driver):
    print("🔐 登录 LinkedIn...")
    driver.get("https://www.linkedin.com/login")
    time.sleep(2)
    
    safe_find(driver, By.ID, "username").send_keys(LINKEDIN_EMAIL)
    safe_find(driver, By.ID, "password").send_keys(LINKEDIN_PASSWORD)
    safe_find(driver, By.CSS_SELECTOR, "button[type='submit']").click()
    time.sleep(3)
    
    if "feed" in driver.current_url:
        print("✅ 登录成功")
        return True
    return False

def find_easy_apply_jobs(driver):
    """搜索 Easy Apply 职位"""
    print("\n🔍 搜索 Easy Apply 职位...")
    
    # 访问 LinkedIn Jobs 页面，筛选 Easy Apply
    search_url = "https://www.linkedin.com/jobs/search/?keywords=Creative%20Technologist&location=New%20York&f_AL=true"
    driver.get(search_url)
    time.sleep(4)
    
    # 保存搜索结果
    driver.save_screenshot("job_search_results.png")
    with open("job_search_results.html", "w") as f:
        f.write(driver.page_source)
    print("📸 搜索结果已保存")
    
    # 查找职位卡片
    job_cards = driver.find_elements(By.CSS_SELECTOR, ".job-card-container")
    print(f"📊 找到 {len(job_cards)} 个职位卡片")
    
    easy_apply_jobs = []
    
    for card in job_cards[:5]:
        try:
            # 获取职位标题
            title_elem = card.find_element(By.CSS_SELECTOR, ".job-card-list__title")
            title = title_elem.text.strip()
            
            # 获取公司名
            company_elem = card.find_element(By.CSS_SELECTOR, ".job-card-container__company-name")
            company = company_elem.text.strip()
            
            # 检查是否是 Easy Apply (查找按钮文本)
            apply_btn = card.find_element(By.CSS_SELECTOR, ".job-card-container__apply-method")
            apply_text = apply_btn.text.strip()
            
            print(f"\n  📋 {title} @ {company}")
            print(f"     申请方式: {apply_text}")
            
            if "Easy Apply" in apply_text:
                easy_apply_jobs.append({
                    'title': title,
                    'company': company,
                    'element': card
                })
                print(f"     ✅ 是 Easy Apply 职位！")
            else:
                print(f"     ❌ 不是 Easy Apply")
                
        except Exception as e:
            continue
    
    return easy_apply_jobs

def test_apply_to_job(driver, job):
    """测试申请单个职位"""
    print(f"\n🎯 测试申请: {job['title']} @ {job['company']}")
    
    # 点击职位卡片
    try:
        job['element'].click()
        time.sleep(3)
    except:
        print("  ❌ 无法点击职位")
        return False
    
    # 查找 Easy Apply 按钮
    easy_apply_btn = safe_find(driver, By.CSS_SELECTOR, "button[aria-label*='Easy Apply']", timeout=5)
    
    if not easy_apply_btn:
        print("  ❌ 未找到 Easy Apply 按钮")
        return False
    
    print(f"  ✅ 找到 Easy Apply 按钮: {easy_apply_btn.text}")
    
    # 滚动并点击
    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", easy_apply_btn)
    time.sleep(1)
    easy_apply_btn.click()
    time.sleep(3)
    
    # 保存截图
    driver.save_screenshot("easy_apply_form.png")
    print("  📸 申请表单截图已保存")
    
    # 检查弹窗
    modal = safe_find(driver, By.CSS_SELECTOR, ".jobs-easy-apply-modal", timeout=5)
    if modal:
        print("  ✅ Easy Apply 弹窗已打开！")
        
        # 分析表单
        print("\n  📝 表单字段分析:")
        
        # 查找输入字段
        inputs = driver.find_elements(By.CSS_SELECTOR, ".jobs-easy-apply-modal input")
        print(f"     Input 字段: {len(inputs)} 个")
        for inp in inputs[:10]:
            name = inp.get_attribute("name") or inp.get_attribute("id") or "unnamed"
            print(f"       - {name}")
        
        return True
    
    return False

def main():
    print("="*60)
    print("🚀 LinkedIn Easy Apply 搜索与测试")
    print("="*60)
    
    driver = setup_driver()
    
    try:
        # 登录
        if not linkedin_login(driver):
            print("❌ 登录失败")
            return
        
        # 搜索 Easy Apply 职位
        easy_jobs = find_easy_apply_jobs(driver)
        
        if not easy_jobs:
            print("\n❌ 未找到 Easy Apply 职位")
            return
        
        print(f"\n✅ 找到 {len(easy_jobs)} 个 Easy Apply 职位")
        
        # 测试第一个
        if easy_jobs:
            test_apply_to_job(driver, easy_jobs[0])
        
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
