#!/usr/bin/env python3
"""
测试特定 LinkedIn 职位申请 - Kyndryl Creative Technologist
"""

import os
import sys
import time
import yaml
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# 加载配置
config_path = Path("config/profile.yaml")
if config_path.exists():
    with open(config_path) as f:
        config = yaml.safe_load(f)
    email = config.get('personal_info', {}).get('email', '')
    password = config.get('personal_info', {}).get('password', '')
    first_name = config.get('personal_info', {}).get('first_name', '')
    last_name = config.get('personal_info', {}).get('last_name', '')
    phone = config.get('personal_info', {}).get('phone', '')
else:
    email = password = first_name = last_name = phone = ''

JOB_URL = "https://www.linkedin.com/jobs/view/creative-technologist-at-kyndryl-4368403070"

# 设置 Chrome
options = Options()
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
options.add_argument('--window-size=1920,1080')
options.add_argument('--disable-blink-features=AutomationControlled')
options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
# 非无头模式以便观察
# options.add_argument('--headless=new')

print("🚀 启动浏览器...")
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=options)
wait = WebDriverWait(driver, 15)
short_wait = WebDriverWait(driver, 5)

def safe_find(by, value, timeout=10):
    """安全查找元素"""
    try:
        return WebDriverWait(driver, timeout).until(EC.presence_of_element_located((by, value)))
    except:
        return None

def safe_click(by, value, timeout=10):
    """安全点击元素"""
    try:
        elem = WebDriverWait(driver, timeout).until(EC.element_to_be_clickable((by, value)))
        elem.click()
        return True
    except Exception as e:
        print(f"  点击失败: {e}")
        return False

try:
    print(f"🔍 访问职位: {JOB_URL}")
    driver.get(JOB_URL)
    time.sleep(3)
    
    # 保存页面用于分析
    with open("kyndryl_job_page.html", "w") as f:
        f.write(driver.page_source)
    print("✅ 页面已保存到 kyndryl_job_page.html")
    
    # 截图
    driver.save_screenshot("kyndryl_job_page.png")
    print("📸 截图已保存到 kyndryl_job_page.png")
    
    # 查找 Easy Apply 按钮
    print("\n🔍 查找 Easy Apply 按钮...")
    
    # 多种 selector 尝试
    selectors = [
        "button[aria-label*='Easy Apply']",
        "button[aria-label*='easy apply']",
        ".jobs-apply-button--top-card",
        "button.jobs-apply-button",
        "[data-control-name='jobdetails_topcard_inapply']",
        "button.artdeco-button--primary"
    ]
    
    easy_apply_btn = None
    for selector in selectors:
        easy_apply_btn = safe_find(By.CSS_SELECTOR, selector, timeout=3)
        if easy_apply_btn:
            print(f"  ✅ 找到 Easy Apply 按钮: {selector}")
            print(f"     文本: {easy_apply_btn.text}")
            break
    
    if not easy_apply_btn:
        print("  ❌ 未找到 Easy Apply 按钮")
        print("  可能原因:")
        print("    - 职位需要外部申请")
        print("    - 未登录 LinkedIn")
        print("    - 页面结构不同")
        
        # 查找所有按钮
        print("\n  页面上的所有按钮:")
        buttons = driver.find_elements(By.TAG_NAME, "button")
        for btn in buttons[:10]:
            text = btn.text.strip()
            aria = btn.get_attribute("aria-label") or ""
            if text or aria:
                print(f"    - {text or aria}")
    else:
        print("\n🖱️ 点击 Easy Apply...")
        easy_apply_btn.click()
        time.sleep(2)
        
        # 截图申请表单
        driver.save_screenshot("kyndryl_apply_form.png")
        print("📸 申请表单截图已保存")
        
        # 查找表单字段
        print("\n📝 分析表单字段...")
        
        # 查找输入框
        inputs = driver.find_elements(By.TAG_NAME, "input")
        print(f"  找到 {len(inputs)} 个 input 元素")
        
        for inp in inputs[:10]:
            name = inp.get_attribute("name") or ""
            id_attr = inp.get_attribute("id") or ""
            placeholder = inp.get_attribute("placeholder") or ""
            input_type = inp.get_attribute("type") or "text"
            if name or id_attr or placeholder:
                print(f"    - name={name}, id={id_attr}, type={input_type}, placeholder={placeholder}")
        
        # 查找文本域
        textareas = driver.find_elements(By.TAG_NAME, "textarea")
        print(f"  找到 {len(textareas)} 个 textarea 元素")
        
        print("\n✅ 测试完成！请检查截图和 HTML 文件")
    
except Exception as e:
    print(f"❌ 错误: {e}")
    import traceback
    traceback.print_exc()
    
finally:
    time.sleep(5)  # 等待5秒观察
    driver.quit()
    print("\n✅ 完成")
