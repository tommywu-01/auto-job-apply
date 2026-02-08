#!/usr/bin/env python3
"""
LinkedIn Easy Apply - 最终稳定版
优化资源使用，精准定位弹窗
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
}

def setup_driver():
    options = Options()
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    options.add_argument('--disable-gpu')
    options.add_argument('--disable-extensions')
    options.add_argument('--disable-logging')
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    driver.set_page_load_timeout(30)
    return driver

def safe_find(driver, by, value, timeout=10):
    try:
        return WebDriverWait(driver, timeout).until(EC.presence_of_element_located((by, value)))
    except:
        return None

def main():
    print("🚀 LinkedIn Easy Apply 最终稳定版")
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
        
        # 搜索职位
        print("\n🔍 搜索职位...")
        driver.get("https://www.linkedin.com/jobs/search/?keywords=Creative%20Director&location=New%20York&f_AL=true")
        time.sleep(4)
        
        # 点击第一个职位
        print("\n📋 选择职位...")
        job = safe_find(driver, By.CSS_SELECTOR, ".job-card-container", timeout=10)
        if job:
            job.click()
            time.sleep(3)
        
        # 点击 Easy Apply
        print("\n🖱️ 点击 Easy Apply...")
        easy_apply = safe_find(driver, By.CSS_SELECTOR, "button[aria-label*='Easy Apply']", timeout=5)
        
        if easy_apply:
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", easy_apply)
            time.sleep(1)
            easy_apply.click()
            print("✅ 已点击 Easy Apply，等待弹窗...")
            time.sleep(5)  # 给足够时间加载弹窗
            
            # 分析页面结构
            print("\n🔍 分析页面...")
            
            # 查找 artdeco-modal
            modals = driver.find_elements(By.CSS_SELECTOR, ".artdeco-modal")
            print(f"  找到 {len(modals)} 个 artdeco-modal")
            
            # 查找所有输入框
            inputs = driver.find_elements(By.CSS_SELECTOR, ".artdeco-modal input, .artdeco-modal textarea")
            print(f"  弹窗内输入框: {len(inputs)}")
            
            # 显示字段信息
            for i, inp in enumerate(inputs[:5]):
                name = inp.get_attribute("name") or ""
                id_attr = inp.get_attribute("id") or ""
                placeholder = inp.get_attribute("placeholder") or ""
                aria = inp.get_attribute("aria-label") or ""
                print(f"    {i+1}. {name or id_attr or placeholder or aria}")
            
            # 尝试填写
            print("\n✍️ 填写表单...")
            filled = 0
            for inp in inputs:
                try:
                    if not inp.is_displayed():
                        continue
                    
                    identifiers = f"{inp.get_attribute('name')} {inp.get_attribute('placeholder')} {inp.get_attribute('aria-label')}".lower()
                    
                    value = None
                    if 'first' in identifiers:
                        value = PROFILE['first_name']
                    elif 'last' in identifiers:
                        value = PROFILE['last_name']
                    elif 'email' in identifiers:
                        value = PROFILE['email']
                    elif 'phone' in identifiers:
                        value = PROFILE['phone']
                    elif 'linkedin' in identifiers:
                        value = PROFILE['linkedin']
                    elif 'website' in identifiers or 'portfolio' in identifiers:
                        value = PROFILE['website']
                    
                    if value:
                        inp.clear()
                        inp.send_keys(value)
                        print(f"    ✅ {identifiers[:40]}: {value}")
                        filled += 1
                        time.sleep(0.5)
                except:
                    continue
            
            print(f"\n  填写了 {filled} 个字段")
            
            # 查找并点击下一步按钮
            print("\n➡️ 查找下一步按钮...")
            buttons = driver.find_elements(By.CSS_SELECTOR, ".artdeco-modal button")
            for btn in buttons:
                try:
                    text = btn.text.strip().lower()
                    if any(x in text for x in ['next', 'review', 'submit', 'continue']):
                        print(f"    找到按钮: {btn.text}")
                        # 不实际点击，只演示
                        break
                except:
                    continue
        
        driver.save_screenshot("result.png")
        print("\n📸 截图已保存: result.png")
        print("\n✅ 完成！")
        
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        try:
            driver.save_screenshot("error.png")
        except:
            pass
    
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
