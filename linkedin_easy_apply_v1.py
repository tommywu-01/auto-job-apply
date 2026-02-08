#!/usr/bin/env python3
"""
LinkedIn Easy Apply - 完整自动填写版 v1.0
成功打开弹窗并填写表单
"""

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
    'linkedin': personal.get('linkedin', 'https://linkedin.com/in/tommywu'),
}

def setup_driver():
    options = Options()
    options.add_argument('--no-sandbox')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('--disable-gpu')
    options.add_argument('--disable-extensions')
    
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=options)

def click_easy_apply(driver):
    """使用 JavaScript 点击 Easy Apply 按钮"""
    print("\n🖱️ 点击 Easy Apply...")
    result = driver.execute_script("""
        var btn = document.getElementById('jobs-apply-button-id');
        if (btn) {
            btn.click();
            return 'Clicked successfully';
        }
        return 'Button not found';
    """)
    print(f"   {result}")
    time.sleep(5)

def get_modal(driver):
    """获取弹窗元素"""
    modals = driver.execute_script("""
        var selectors = ['.artdeco-modal', '[role="dialog"]', '.jobs-easy-apply-modal'];
        for (var s of selectors) {
            var el = document.querySelector(s);
            if (el && el.offsetParent !== null) return el;
        }
        return null;
    """)
    return modals

def fill_form(driver):
    """填写表单字段"""
    print("\n📝 填写表单...")
    
    filled = driver.execute_script("""
        var filled = [];
        var inputs = document.querySelectorAll('.artdeco-modal input, .artdeco-modal textarea, .artdeco-modal select');
        
        inputs.forEach(function(inp) {
            if (!inp.offsetParent) return; // 跳过不可见元素
            
            var name = (inp.name || '').toLowerCase();
            var placeholder = (inp.placeholder || '').toLowerCase();
            var aria = (inp.getAttribute('aria-label') || '').toLowerCase();
            var identifiers = name + ' ' + placeholder + ' ' + aria;
            
            var value = null;
            var fieldName = '';
            
            if (identifiers.includes('first') || identifiers.includes('fname')) {
                value = '%s';
                fieldName = 'First Name';
            } else if (identifiers.includes('last') || identifiers.includes('lname') || identifiers.includes('surname')) {
                value = '%s';
                fieldName = 'Last Name';
            } else if (identifiers.includes('email')) {
                value = '%s';
                fieldName = 'Email';
            } else if (identifiers.includes('phone') || identifiers.includes('mobile') || identifiers.includes('tel')) {
                value = '%s';
                fieldName = 'Phone';
            }
            
            if (value && !inp.value) {
                inp.value = value;
                inp.dispatchEvent(new Event('input', { bubbles: true }));
                inp.dispatchEvent(new Event('change', { bubbles: true }));
                filled.push(fieldName + ': ' + value);
            }
        });
        
        return filled;
    """ % (PROFILE['first_name'], PROFILE['last_name'], PROFILE['email'], PROFILE['phone']))
    
    for field in filled:
        print(f"   ✅ {field}")
    
    return len(filled)

def click_next(driver):
    """点击下一步按钮"""
    print("\n➡️ 点击 Next...")
    result = driver.execute_script("""
        var btn = document.querySelector('.artdeco-modal button[aria-label="Next"], .artdeco-modal button[type="submit"]');
        if (!btn) {
            // 查找包含 Next 或 Continue 文本的按钮
            var buttons = document.querySelectorAll('.artdeco-modal button');
            for (var b of buttons) {
                if (b.textContent.includes('Next') || b.textContent.includes('Continue')) {
                    btn = b;
                    break;
                }
            }
        }
        if (btn) {
            btn.click();
            return 'Clicked: ' + btn.textContent.trim();
        }
        return 'Next button not found';
    """)
    print(f"   {result}")
    time.sleep(4)

def main():
    print("="*60)
    print("🚀 LinkedIn Easy Apply - 完整自动填写版 v1.0")
    print("="*60)
    
    driver = setup_driver()
    
    try:
        # 登录
        print("\n🔐 登录 LinkedIn...")
        driver.get("https://www.linkedin.com/login")
        time.sleep(2)
        driver.find_element(By.ID, "username").send_keys("wuyuehao2001@outlook.com")
        driver.find_element(By.ID, "password").send_keys("Tommy12345#")
        driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        time.sleep(3)
        print("✅ 登录成功")
        
        # 访问职位
        print("\n📋 访问职位页面...")
        driver.get("https://www.linkedin.com/jobs/view/4361442478")
        time.sleep(5)
        
        # 点击 Easy Apply
        click_easy_apply(driver)
        
        # 填写表单
        filled_count = fill_form(driver)
        print(f"\n   填写了 {filled_count} 个字段")
        
        # 点击 Next
        click_next(driver)
        
        # 保存截图
        driver.save_screenshot("final_application.png")
        print("\n📸 截图: final_application.png")
        
        print("\n" + "="*60)
        print("✅ 申请流程完成！")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        driver.save_screenshot("error.png")
    
    finally:
        time.sleep(3)
        driver.quit()

if __name__ == "__main__":
    main()
