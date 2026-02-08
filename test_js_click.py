#!/usr/bin/env python3
"""
LinkedIn Easy Apply - 使用 JavaScript 点击
绕过可见性问题
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
    print("🚀 LinkedIn Easy Apply - JavaScript 点击测试")
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
        time.sleep(5)
        
        # 查找所有可能的 Easy Apply 按钮
        print("\n🔍 分析页面按钮...")
        
        all_buttons = driver.find_elements(By.TAG_NAME, "button")
        print(f"页面共有 {len(all_buttons)} 个按钮")
        
        easy_apply_btns = []
        for btn in all_buttons:
            try:
                text = btn.text.strip()
                aria = btn.get_attribute("aria-label") or ""
                if "Easy Apply" in text or "Easy Apply" in aria:
                    easy_apply_btns.append({
                        'element': btn,
                        'text': text,
                        'aria': aria,
                        'visible': btn.is_displayed(),
                        'id': btn.get_attribute("id")
                    })
            except:
                pass
        
        print(f"\n找到 {len(easy_apply_btns)} 个 Easy Apply 按钮:")
        for i, btn_info in enumerate(easy_apply_btns[:5]):
            print(f"  {i+1}. ID={btn_info['id']}, 文本='{btn_info['text']}', 可见={btn_info['visible']}")
        
        # 使用 JavaScript 点击第一个
        if easy_apply_btns:
            print("\n🖱️ 使用 JavaScript 点击...")
            driver.execute_script("arguments[0].click();", easy_apply_btns[0]['element'])
            print("✅ 已点击")
            
            time.sleep(6)
            
            # 检查弹窗
            print("\n🔍 查找弹窗...")
            
            # 检查 body 的子元素变化
            body = driver.find_element(By.TAG_NAME, "body")
            body_children = body.find_elements(By.XPATH, "./div")
            print(f"Body 有 {len(body_children)} 个直接子 div")
            
            for i, child in enumerate(body_children[-3:]):
                class_name = child.get_attribute("class") or ""
                print(f"  子元素 {i}: class='{class_name[:50]}'")
            
            # 查找 modal
            modals = driver.find_elements(By.CSS_SELECTOR, ".artdeco-modal, [role='dialog'], .jobs-easy-apply-modal")
            visible_modals = [m for m in modals if m.is_displayed()]
            print(f"\n找到 {len(visible_modals)} 个可见弹窗")
            
            if visible_modals:
                modal = visible_modals[0]
                inputs = modal.find_elements(By.CSS_SELECTOR, "input, textarea, select")
                print(f"弹窗内有 {len(inputs)} 个表单字段")
                
                for inp in inputs[:10]:
                    try:
                        name = inp.get_attribute("name") or ""
                        placeholder = inp.get_attribute("placeholder") or ""
                        print(f"  - {name or placeholder}")
                    except:
                        pass
        
        driver.save_screenshot("js_click_result.png")
        print("\n📸 截图: js_click_result.png")
        
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
