#!/usr/bin/env python3
"""
快速测试 - 找新的 Easy Apply 职位
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

def main():
    driver = setup_driver()
    
    try:
        # 登录
        print("🔐 登录...")
        driver.get("https://www.linkedin.com/login")
        time.sleep(2)
        driver.find_element(By.ID, "username").send_keys("wuyuehao2001@outlook.com")
        driver.find_element(By.ID, "password").send_keys("Tommy12345#")
        driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        time.sleep(3)
        print("✅ 登录成功")
        
        # 搜索 Easy Apply 职位
        print("\n🔍 搜索 Easy Apply 职位...")
        driver.get("https://www.linkedin.com/jobs/search/?keywords=Creative%20Director&location=New%20York&f_AL=true")
        time.sleep(5)
        
        # 获取职位列表
        jobs = driver.execute_script("""
            var cards = document.querySelectorAll('.job-card-container');
            var results = [];
            cards.forEach(function(card, i) {
                if (i < 5) {
                    var title = card.querySelector('.job-card-list__title');
                    var company = card.querySelector('.job-card-container__company-name');
                    var link = card.querySelector('a.job-card-list__title');
                    if (title && link) {
                        results.push({
                            title: title.textContent.trim(),
                            company: company ? company.textContent.trim() : 'Unknown',
                            url: link.href
                        });
                    }
                }
            });
            return results;
        """)
        
        print(f"\n找到 {len(jobs)} 个职位:\n")
        for i, job in enumerate(jobs, 1):
            print(f"{i}. {job['title']}")
            print(f"   公司: {job['company']}")
            print(f"   URL: {job['url']}")
            print()
        
        driver.save_screenshot("job_search.png")
        print("📸 截图: job_search.png")
        
    except Exception as e:
        print(f"❌ 错误: {e}")
    
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
