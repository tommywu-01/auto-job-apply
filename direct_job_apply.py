#!/usr/bin/env python3
"""
LinkedIn Easy Apply - 直接访问职位URL版本
绕过搜索，直接测试已知的Easy Apply职位
"""

import os
import time
import yaml
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

# 已知的Easy Apply职位列表
TEST_JOBS = [
    # US Tech Solutions - Creative Director (之前测试过的)
    "https://www.linkedin.com/jobs/view/4361442478",
    # 可以尝试其他职位...
]

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

def login(driver):
    print("🔐 登录 LinkedIn...")
    driver.get("https://www.linkedin.com/login")
    time.sleep(2)
    
    driver.find_element(By.ID, "username").send_keys("wuyuehao2001@outlook.com")
    driver.find_element(By.ID, "password").send_keys("Tommy12345#")
    driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
    time.sleep(3)
    
    if "feed" in driver.current_url or "linkedin.com" in driver.current_url:
        print("✅ 登录成功")
        return True
    print("❌ 登录失败")
    return False

def try_easy_apply(driver, job_url):
    print(f"\n📋 访问职位: {job_url}")
    driver.get(job_url)
    time.sleep(4)
    
    # 保存页面源码用于分析
    with open("job_page_source.html", "w") as f:
        f.write(driver.page_source)
    print("✅ 已保存页面源码: job_page_source.html")
    
    # 查找Easy Apply按钮
    print("\n🔍 查找 Easy Apply 按钮...")
    
    # 多种选择器尝试
    selectors = [
        "button[aria-label*='Easy Apply']",
        "button.jobs-apply-button",
        ".jobs-s-apply button",
        "button[data-control-name='jobdetails_topcard_inapply']",
    ]
    
    easy_apply_btn = None
    for selector in selectors:
        try:
            btn = driver.find_element(By.CSS_SELECTOR, selector)
            if btn and btn.is_displayed():
                print(f"  ✅ 找到按钮: {selector}")
                easy_apply_btn = btn
                break
        except:
            continue
    
    if not easy_apply_btn:
        print("  ❌ 未找到 Easy Apply 按钮")
        return False
    
    print(f"  按钮文本: {easy_apply_btn.text}")
    
    # 点击前检查是否有iframe或其他容器
    print("\n🔍 检查页面结构...")
    iframes = driver.find_elements(By.TAG_NAME, "iframe")
    print(f"  页面中有 {len(iframes)} 个 iframe")
    
    # 点击按钮
    print("\n🖱️ 点击 Easy Apply 按钮...")
    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", easy_apply_btn)
    time.sleep(1)
    
    # 尝试多种点击方式
    try:
        easy_apply_btn.click()
    except:
        driver.execute_script("arguments[0].click();", easy_apply_btn)
    
    print("  ✅ 已点击")
    time.sleep(6)  # 给足够时间加载
    
    # 检查弹窗
    print("\n🔍 检查弹窗...")
    
    # 截图看看发生了什么
    driver.save_screenshot("after_easy_apply_click.png")
    print("  📸 已截图: after_easy_apply_click.png")
    
    # 尝试查找弹窗的多种方式
    modal_selectors = [
        ".artdeco-modal",
        ".jobs-easy-apply-modal",
        "div[role='dialog']",
        ".artdeco-modal__content",
    ]
    
    for selector in modal_selectors:
        elements = driver.find_elements(By.CSS_SELECTOR, selector)
        visible = [e for e in elements if e.is_displayed()]
        if visible:
            print(f"  ✅ 找到弹窗: {selector} (可见: {len(visible)})")
            
            # 在弹窗内查找输入框
            modal = visible[0]
            inputs = modal.find_elements(By.CSS_SELECTOR, "input, textarea, select")
            print(f"  📋 弹窗内有 {len(inputs)} 个输入字段")
            
            # 显示字段信息
            for i, inp in enumerate(inputs[:10]):
                try:
                    name = inp.get_attribute("name") or ""
                    id_attr = inp.get_attribute("id") or ""
                    placeholder = inp.get_attribute("placeholder") or ""
                    aria = inp.get_attribute("aria-label") or ""
                    input_type = inp.get_attribute("type") or "text"
                    print(f"    {i+1}. [{input_type}] {name or id_attr or placeholder or aria}")
                except:
                    pass
            
            return True, inputs
    
    print("  ⚠️ 未找到弹窗")
    
    # 检查页面是否跳转
    print(f"\n  当前URL: {driver.current_url}")
    
    # 检查是否有错误信息
    error_msgs = driver.find_elements(By.CSS_SELECTOR, ".artdeco-inline-feedback__message")
    if error_msgs:
        for msg in error_msgs:
            print(f"  ⚠️ 错误信息: {msg.text}")
    
    return False, []

def fill_form(driver, inputs):
    """填写表单"""
    print("\n✍️ 开始填写表单...")
    
    filled_count = 0
    
    for inp in inputs:
        try:
            if not inp.is_displayed() or not inp.is_enabled():
                continue
            
            # 获取字段标识
            name = (inp.get_attribute("name") or "").lower()
            id_attr = (inp.get_attribute("id") or "").lower()
            placeholder = (inp.get_attribute("placeholder") or "").lower()
            aria = (inp.get_attribute("aria-label") or "").lower()
            
            identifiers = f"{name} {id_attr} {placeholder} {aria}"
            
            # 确定要填写的值
            value = None
            field_name = None
            
            if any(x in identifiers for x in ['first', 'fname']):
                value = PROFILE['first_name']
                field_name = "First Name"
            elif any(x in identifiers for x in ['last', 'lname', 'surname']):
                value = PROFILE['last_name']
                field_name = "Last Name"
            elif 'email' in identifiers:
                value = PROFILE['email']
                field_name = "Email"
            elif any(x in identifiers for x in ['phone', 'mobile', 'tel']):
                value = PROFILE['phone']
                field_name = "Phone"
            elif 'linkedin' in identifiers:
                value = PROFILE['linkedin']
                field_name = "LinkedIn"
            elif any(x in identifiers for x in ['website', 'portfolio', 'url']):
                value = PROFILE['website']
                field_name = "Website"
            
            if value:
                # 清除并填写
                inp.clear()
                time.sleep(0.2)
                inp.send_keys(value)
                print(f"  ✅ {field_name}: {value}")
                filled_count += 1
                time.sleep(0.5)
                
        except Exception as e:
            continue
    
    print(f"\n  总共填写了 {filled_count} 个字段")
    return filled_count

def click_next_button(driver):
    """点击下一步/继续按钮"""
    print("\n➡️ 查找下一步按钮...")
    
    button_selectors = [
        "button[aria-label='Continue']",
        "button[aria-label='Next']",
        "button[aria-label='Review']",
        ".artdeco-button--primary",
        "button[data-easy-apply-next-button]",
    ]
    
    for selector in button_selectors:
        try:
            buttons = driver.find_elements(By.CSS_SELECTOR, selector)
            for btn in buttons:
                if btn.is_displayed():
                    btn_text = btn.text.strip()
                    print(f"  找到按钮: {btn_text}")
                    # 暂不点击，只报告
                    return btn
        except:
            continue
    
    print("  未找到下一步按钮")
    return None

def main():
    print("="*60)
    print("🚀 LinkedIn Easy Apply - 直接访问职位版本")
    print("="*60)
    
    driver = setup_driver()
    
    try:
        # 登录
        if not login(driver):
            return
        
        # 测试职位
        job_url = TEST_JOBS[0]
        success, inputs = try_easy_apply(driver, job_url)
        
        if success and inputs:
            # 填写表单
            fill_form(driver, inputs)
            
            # 查找下一步按钮
            click_next_button(driver)
        
        # 保存最终截图
        driver.save_screenshot("final_result_v2.png")
        print("\n📸 最终截图: final_result_v2.png")
        
        print("\n" + "="*60)
        print("✅ 测试完成！")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        driver.save_screenshot("error_v2.png")
    
    finally:
        input("\n按 Enter 键关闭浏览器...")
        driver.quit()

if __name__ == "__main__":
    main()
