#!/usr/bin/env python3
"""
测试修复后的 Easy Apply 按钮点击 - BGB Group 职位
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
    
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=options)

def click_easy_apply(driver):
    """修复后的点击函数"""
    print("\n🖱️ 点击 Easy Apply...")
    
    # 等待按钮加载
    time.sleep(2)
    
    result = driver.execute_script("""
        // 方式1: 通过ID
        var btn = document.getElementById('jobs-apply-button-id');
        if (btn && btn.offsetParent !== null) {
            btn.click();
            return 'Clicked by ID';
        }
        
        // 方式2: 通过aria-label
        var btns = document.querySelectorAll('button[aria-label*="Easy Apply"]');
        for (var b of btns) {
            if (b.offsetParent !== null) {
                b.click();
                return 'Clicked by aria-label: ' + b.getAttribute('aria-label');
            }
        }
        
        // 方式3: 通过文本内容
        var allBtns = document.querySelectorAll('button');
        for (var b of allBtns) {
            if (b.textContent.includes('Easy Apply') && b.offsetParent !== null) {
                b.click();
                return 'Clicked by text: ' + b.textContent.trim();
            }
        }
        
        // 方式4: 通过class
        var classBtns = document.querySelectorAll('.jobs-apply-button, [data-control-name*="apply"]');
        for (var b of classBtns) {
            if (b.offsetParent !== null) {
                b.click();
                return 'Clicked by class';
            }
        }
        
        // 调试信息
        var debug = {
            byId: document.getElementById('jobs-apply-button-id') ? 'exists' : 'not found',
            byAria: document.querySelectorAll('button[aria-label*="Easy Apply"]').length,
            allBtns: document.querySelectorAll('button').length
        };
        return 'Button not found. Debug: ' + JSON.stringify(debug);
    """)
    
    print(f"   结果: {result}")
    return 'not found' not in result.lower()

def main():
    driver = setup_driver()
    
    try:
        print("🚀 测试修复 - BGB Group 职位")
        
        # 登录
        print("\n🔐 登录...")
        driver.get("https://www.linkedin.com/login")
        time.sleep(2)
        driver.find_element(By.ID, "username").send_keys("wuyuehao2001@outlook.com")
        driver.find_element(By.ID, "password").send_keys("Tommy12345#")
        driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        time.sleep(3)
        print("✅ 登录成功")
        
        # 访问 BGB Group 职位
        print("\n📋 访问 BGB Group 职位...")
        driver.get("https://www.linkedin.com/jobs/view/4342322618")
        time.sleep(5)
        
        # 尝试点击 Easy Apply
        success = click_easy_apply(driver)
        
        if success:
            print("\n✅ 点击成功！等待弹窗...")
            time.sleep(5)
            
            # 检查弹窗
            modal = driver.execute_script("""
                var m = document.querySelector('.artdeco-modal, [role="dialog"]');
                return m ? 'Found modal' : 'No modal found';
            """)
            print(f"   {modal}")
        else:
            print("\n❌ 点击失败，截图保存...")
            driver.save_screenshot("logs/bgb_debug.png")
        
        driver.save_screenshot("logs/bgb_test_result.png")
        print("\n📸 截图: logs/bgb_test_result.png")
        
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        driver.save_screenshot("logs/bgb_error.png")
    
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
