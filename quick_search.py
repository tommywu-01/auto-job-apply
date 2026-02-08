#!/usr/bin/env python3
"""
快速搜索 LinkedIn 职位并验证哪些是开放的
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
else:
    email = password = ''

# 设置 Chrome
options = Options()
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
options.add_argument('--window-size=1920,1080')
options.add_argument('--disable-blink-features=AutomationControlled')
options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
# 无头模式
options.add_argument('--headless=new')

print("🚀 启动浏览器...")
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=options)
wait = WebDriverWait(driver, 10)

try:
    # 先访问 LinkedIn 职位搜索
    search_url = "https://www.linkedin.com/jobs/search/?keywords=Creative%20Technologist&f_WT=2&geoId=90000070"
    print(f"🔍 访问: {search_url}")
    driver.get(search_url)
    time.sleep(3)
    
    # 保存页面源码用于分析
    with open("linkedin_search_page.html", "w") as f:
        f.write(driver.page_source)
    print("✅ 页面已保存到 linkedin_search_page.html")
    
    # 查找职位卡片
    job_cards = driver.find_elements(By.CSS_SELECTOR, "[data-job-id]")
    print(f"📊 找到 {len(job_cards)} 个职位卡片")
    
    # 提取职位信息
    jobs = []
    for card in job_cards[:10]:  # 只取前10个
        try:
            job_id = card.get_attribute("data-job-id")
            title_elem = card.find_element(By.CSS_SELECTOR, "a.job-card-container__link")
            title = title_elem.text.strip()
            href = title_elem.get_attribute("href")
            
            company_elem = card.find_element(By.CSS_SELECTOR, ".job-card-container__company-name")
            company = company_elem.text.strip()
            
            # 检查是否有 Easy Apply
            easy_apply = len(card.find_elements(By.CSS_SELECTOR, "[aria-label*='Easy Apply']")) > 0
            
            jobs.append({
                'id': job_id,
                'title': title,
                'company': company,
                'url': href,
                'easy_apply': easy_apply
            })
            print(f"  ✅ {title} @ {company} (Easy Apply: {easy_apply})")
        except Exception as e:
            continue
    
    # 保存结果
    import json
    with open("linkedin_jobs_found.json", "w") as f:
        json.dump(jobs, f, indent=2)
    
    print(f"\n🎯 找到 {len(jobs)} 个有效职位")
    print("💾 结果已保存到 linkedin_jobs_found.json")
    
    # 找一个 Easy Apply 的测试
    easy_jobs = [j for j in jobs if j['easy_apply']]
    if easy_jobs:
        test_job = easy_jobs[0]
        print(f"\n🧪 测试职位: {test_job['title']} @ {test_job['company']}")
        print(f"   URL: {test_job['url']}")
    
except Exception as e:
    print(f"❌ 错误: {e}")
    # 保存截图
    driver.save_screenshot("search_error.png")
    print("📸 截图已保存到 search_error.png")
    
finally:
    driver.quit()
    print("\n✅ 完成")
