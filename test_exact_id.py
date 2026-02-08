#!/usr/bin/env python3
"""
LinkedIn Easy Apply - 使用精确按钮ID
"""

import os
import time
import yaml
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
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
}

def setup_driver():
    options = Options()
    options.add_argument('--no-sandbox')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    driver.set_page_load_timeout(30)
    return driver

def main():
    print("🚀 LinkedIn Easy Apply - 精确选择器测试")
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
        
        # 访问职位
        print("\n📋 访问职位...")
        driver.get("https://www.linkedin.com/jobs/view/4361442478")
        time.sleep(5)  # 给足够时间加载
        
        # 查找 Easy Apply 按钮 - 使用精确ID
        print("\n🔍 查找 Easy Apply 按钮...")
        
        try:
            easy_apply_btn = driver.find_element(By.ID, "jobs-apply-button-id")
            print(f"✅ 找到按钮 (ID): {easy_apply_btn.text}")
            print(f"   aria-label: {easy_apply_btn.get_attribute('aria-label')}")
            print(f"   可见: {easy_apply_btn.is_displayed()}")
            print(f"   可用: {easy_apply_btn.is_enabled()}")
            
            # 点击
            print("\n🖱️ 点击按钮...")
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", easy_apply_btn)
            time.sleep(1)
            easy_apply_btn.click()
            print("✅ 已点击")
            
            # 等待弹窗
            time.sleep(6)
            
            # 查找弹窗
            print("\n🔍 查找弹窗...")
            
            # 检查多种可能的弹窗结构
            selectors = [
                ".artdeco-modal",
                "div[role='dialog']",
                ".jobs-easy-apply-modal",
                ".artdeco-modal__content",
            ]
            
            for selector in selectors:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                visible = [e for e in elements if e.is_displayed()]
                if visible:
                    print(f"✅ 找到弹窗: {selector}")
                    
                    # 查找表单
                    inputs = visible[0].find_elements(By.CSS_SELECTOR, "input, textarea, select")
                    print(f"📋 找到 {len(inputs)} 个输入字段")
                    
                    # 尝试填写
                    for inp in inputs:
                        try:
                            if not inp.is_displayed():
                                continue
                            
                            name = (inp.get_attribute("name") or "").lower()
                            placeholder = (inp.get_attribute("placeholder") or "").lower()
                            aria = (inp.get_attribute("aria-label") or "").lower()
                            
                            identifiers = f"{name} {placeholder} {aria}"
                            
                            value = None
                            if any(x in identifiers for x in ['first', 'fname']):
                                value = PROFILE['first_name']
                            elif any(x in identifiers for x in ['last', 'lname']):
                                value = PROFILE['last_name']
                            elif 'email' in identifiers:
                                value = PROFILE['email']
                            elif any(x in identifiers for x in ['phone', 'mobile']):
                                value = PROFILE['phone']
                            
                            if value:
                                inp.clear()
                                inp.send_keys(value)
                                print(f"   ✅ 填写: {value}")
                                time.sleep(0.5)
                        except:
                            pass
                    
                    break
            else:
                print("⚠️ 未找到弹窗")
                
        except Exception as e:
            print(f"❌ 找不到按钮: {e}")
        
        driver.save_screenshot("test_result.png")
        print("\n📸 截图: test_result.png")
        
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        driver.save_screenshot("error.png")
    
    finally:
        input("\n按 Enter 关闭...")
        driver.quit()

if __name__ == "__main__":
    main()
