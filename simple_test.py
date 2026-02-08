#!/usr/bin/env python3
"""
LinkedIn Easy Apply - 简化稳定版
"""

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
    options.add_argument('--disable-gpu')
    options.add_argument('--disable-extensions')
    
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=options)

def main():
    driver = setup_driver()
    
    try:
        print("1. 登录...")
        driver.get("https://www.linkedin.com/login")
        time.sleep(2)
        driver.find_element(By.ID, "username").send_keys("wuyuehao2001@outlook.com")
        driver.find_element(By.ID, "password").send_keys("Tommy12345#")
        driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        time.sleep(3)
        print("✅ 登录成功")
        
        print("\n2. 访问职位...")
        driver.get("https://www.linkedin.com/jobs/view/4361442478")
        time.sleep(5)
        
        print("\n3. 点击 Easy Apply...")
        # 直接使用 JavaScript 点击
        result = driver.execute_script("""
            var btn = document.getElementById('jobs-apply-button-id');
            if (btn) {
                btn.click();
                return 'Clicked';
            }
            return 'Button not found';
        """)
        print(f"   结果: {result}")
        
        time.sleep(6)
        
        print("\n4. 检查弹窗...")
        # 检查是否有弹窗出现
        result = driver.execute_script("""
            var modals = document.querySelectorAll('.artdeco-modal, [role="dialog"]');
            return 'Found ' + modals.length + ' modals';
        """)
        print(f"   {result}")
        
        driver.save_screenshot("simple_test.png")
        print("\n✅ 完成！截图: simple_test.png")
        
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        driver.save_screenshot("error.png")
    
    finally:
        time.sleep(2)
        driver.quit()

if __name__ == "__main__":
    main()
