#!/usr/bin/env python3
"""
LinkedIn Easy Apply 完整自动化测试
使用配置文件中的个人信息
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

# ============ 配置 ============
CONFIG_PATH = Path("config/profile.yaml")
LINKEDIN_EMAIL = "wuyuehao2001@outlook.com"
LINKEDIN_PASSWORD = "Tommy12345#"

# 加载配置
if CONFIG_PATH.exists():
    with open(CONFIG_PATH) as f:
        config = yaml.safe_load(f)
    personal = config.get('personal_info', {})
    first_name = personal.get('first_name', '')
    last_name = personal.get('last_name', '')
    phone = personal.get('phone', '')
    email = personal.get('email', '')
    resume_path = os.path.expanduser(config.get('application_settings', {}).get('resume_path', ''))
else:
    print("❌ 配置文件不存在")
    sys.exit(1)

# 搜索关键词
SEARCH_KEYWORDS = "Creative Technologist"
SEARCH_LOCATION = "New York"
MAX_JOBS = 3

# ============ 浏览器设置 ============
def setup_driver():
    options = Options()
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    # 非无头模式以便观察
    # options.add_argument('--headless=new')
    
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=options)

# ============ 工具函数 ============
def random_delay(min_sec=1, max_sec=3):
    time.sleep(random.uniform(min_sec, max_sec))

def safe_find(driver, by, value, timeout=10):
    try:
        return WebDriverWait(driver, timeout).until(EC.presence_of_element_located((by, value)))
    except:
        return None

def safe_click(driver, by, value, timeout=10):
    try:
        elem = WebDriverWait(driver, timeout).until(EC.element_to_be_clickable((by, value)))
        elem.click()
        return True
    except:
        return False

# ============ LinkedIn 登录 ============
def linkedin_login(driver, email, password):
    print("🔐 正在登录 LinkedIn...")
    driver.get("https://www.linkedin.com/login")
    random_delay(2, 3)
    
    # 输入邮箱
    email_field = safe_find(driver, By.ID, "username")
    if email_field:
        email_field.clear()
        email_field.send_keys(email)
        random_delay(0.5, 1)
    
    # 输入密码
    password_field = safe_find(driver, By.ID, "password")
    if password_field:
        password_field.clear()
        password_field.send_keys(password)
        random_delay(0.5, 1)
    
    # 点击登录
    login_btn = safe_find(driver, By.CSS_SELECTOR, "button[type='submit']")
    if login_btn:
        login_btn.click()
        random_delay(3, 5)
    
    # 检查是否登录成功
    current_url = driver.current_url
    print(f"  当前URL: {current_url}")
    
    # 保存登录后页面用于调试
    driver.save_screenshot("linkedin_login_result.png")
    with open("linkedin_login_page.html", "w") as f:
        f.write(driver.page_source)
    print("  📸 登录结果截图已保存")
    
    if "feed" in current_url or "linkedin.com/in/" in current_url:
        print("✅ 登录成功！")
        return True
    else:
        print("❌ 登录失败")
        print("  可能原因: 密码错误、验证码、或安全验证")
        return False

# ============ 搜索 Easy Apply 职位 ============
def search_easy_apply_jobs(driver, keywords, location):
    print(f"\n🔍 搜索: {keywords} in {location}")
    
    # 构建搜索 URL (包含 Easy Apply 筛选)
    search_url = f"https://www.linkedin.com/jobs/search/?keywords={keywords.replace(' ', '%20')}&location={location.replace(' ', '%20')}&f_AL=true"
    driver.get(search_url)
    random_delay(3, 5)
    
    # 保存页面用于调试
    with open("linkedin_search_results.html", "w") as f:
        f.write(driver.page_source)
    
    # 查找职位卡片
    job_cards = driver.find_elements(By.CSS_SELECTOR, "[data-job-id]")
    print(f"📊 找到 {len(job_cards)} 个职位")
    
    jobs = []
    for card in job_cards[:MAX_JOBS]:
        try:
            job_id = card.get_attribute("data-job-id")
            
            # 获取职位标题
            title_elem = card.find_element(By.CSS_SELECTOR, "a.job-card-container__link")
            title = title_elem.text.strip()
            
            # 获取公司名
            company_elem = card.find_element(By.CSS_SELECTOR, ".job-card-container__company-name")
            company = company_elem.text.strip()
            
            jobs.append({
                'id': job_id,
                'title': title,
                'company': company,
                'element': card
            })
            print(f"  ✅ {title} @ {company}")
        except:
            continue
    
    return jobs

# ============ 申请单个职位 ============
def apply_to_job(driver, job):
    print(f"\n🎯 申请: {job['title']} @ {job['company']}")
    
    # 点击职位卡片
    try:
        job['element'].click()
        random_delay(2, 3)
    except:
        print("  ❌ 无法点击职位卡片")
        return False
    
    # 查找 Easy Apply 按钮
    easy_apply_selectors = [
        "button[aria-label*='Easy Apply']",
        "button[aria-label*='easy apply']",
        ".jobs-apply-button--top-card",
        "button.jobs-apply-button",
        "[data-control-name='jobdetails_topcard_inapply']",
    ]
    
    easy_apply_btn = None
    for selector in easy_apply_selectors:
        easy_apply_btn = safe_find(driver, By.CSS_SELECTOR, selector, timeout=3)
        if easy_apply_btn:
            print(f"  ✅ 找到 Easy Apply 按钮")
            break
    
    if not easy_apply_btn:
        print("  ❌ 不是 Easy Apply 职位，跳过")
        return False
    
    # 点击 Easy Apply
    easy_apply_btn.click()
    random_delay(2, 3)
    
    # 保存申请表单截图
    driver.save_screenshot(f"apply_form_{job['id']}.png")
    print(f"  📸 截图已保存")
    
    # 这里可以继续填写表单...
    # 暂时只记录表单结构
    print("  📝 表单分析完成")
    
    # 关闭申请弹窗
    close_btn = safe_find(driver, By.CSS_SELECTOR, "button[aria-label='Dismiss']", timeout=3)
    if close_btn:
        close_btn.click()
        random_delay(1, 2)
    
    return True

# ============ 主函数 ============
def main():
    print("="*60)
    print("🚀 LinkedIn Easy Apply 自动化测试")
    print("="*60)
    
    # 检查凭据
    if not LINKEDIN_EMAIL or not LINKEDIN_PASSWORD:
        print("\n⚠️ 请先在脚本中设置 LINKEDIN_EMAIL 和 LINKEDIN_PASSWORD")
        print("或者通过环境变量传入:")
        print("  export LINKEDIN_EMAIL=your@email.com")
        print("  export LINKEDIN_PASSWORD=yourpassword")
        return
    
    # 启动浏览器
    print("\n🌐 启动浏览器...")
    driver = setup_driver()
    
    try:
        # 登录
        if not linkedin_login(driver, LINKEDIN_EMAIL, LINKEDIN_PASSWORD):
            print("登录失败，退出")
            return
        
        # 搜索职位
        jobs = search_easy_apply_jobs(driver, SEARCH_KEYWORDS, SEARCH_LOCATION)
        
        if not jobs:
            print("\n❌ 未找到职位")
            return
        
        # 申请职位
        print(f"\n📝 开始申请 {len(jobs)} 个职位...")
        applied = 0
        for job in jobs:
            if apply_to_job(driver, job):
                applied += 1
            random_delay(3, 5)
        
        print(f"\n✅ 完成！成功分析 {applied} 个职位")
        
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        input("\n按 Enter 关闭浏览器...")
        driver.quit()
        print("\n✅ 完成")

if __name__ == "__main__":
    # 允许从环境变量读取
    LINKEDIN_EMAIL = os.getenv('LINKEDIN_EMAIL', LINKEDIN_EMAIL)
    LINKEDIN_PASSWORD = os.getenv('LINKEDIN_PASSWORD', LINKEDIN_PASSWORD)
    main()
