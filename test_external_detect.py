#!/usr/bin/env python3
"""
LinkedIn External Apply - 外部链接自动申请系统 v1.1
改进版：更好的职位检测
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
    profile = yaml.safe_load(f)

PERSONAL = profile.get('personal_info', {})

def setup_driver():
    options = Options()
    options.add_argument('--no-sandbox')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('--disable-gpu')
    
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=options)

def main():
    print("="*60)
    print("🚀 LinkedIn External Apply - 测试职位检测 v1.1")
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
        time.sleep(4)
        
        # 等待跳转到 feed 确认登录成功
        if "feed" in driver.current_url:
            print("✅ 登录成功")
        else:
            print(f"⚠️ 登录后跳转到: {driver.current_url}")
            # 截图查看状态
            driver.save_screenshot("login_status.png")
        
        # 访问 jobs 页面（已登录状态）
        print("\n🔍 搜索 Creative Director...")
        driver.get("https://www.linkedin.com/jobs/")
        time.sleep(3)
        
        # 在 jobs 页面搜索
        search_box = driver.find_element(By.CSS_SELECTOR, "input[placeholder*='Search by title']")
        search_box.send_keys("Creative Director")
        search_box.submit()
        time.sleep(5)
        
        # 截图看看页面
        driver.save_screenshot("search_page.png")
        print("📸 截图: search_page.png")
        
        # 检测职位卡片
        print("\n📋 分析页面结构...")
        
        cards = driver.execute_script("""
            var results = {};
            
            // 尝试多种选择器
            var selectors = [
                '.job-card-container',
                '.jobs-search-results__list-item',
                '[data-job-id]',
                '.job-card-list__entity'
            ];
            
            for (var sel of selectors) {
                var elements = document.querySelectorAll(sel);
                results[sel] = elements.length;
            }
            
            return results;
        """)
        
        print("   职位卡片检测结果:")
        for selector, count in cards.items():
            print(f"     {selector}: {count}")
        
        # 获取职位列表
        jobs = driver.execute_script("""
            var cards = document.querySelectorAll('.job-card-container, .jobs-search-results__list-item');
            var results = [];
            cards.forEach(function(card, i) {
                if (i < 5) {
                    var title = card.querySelector('.job-card-list__title, h3, strong');
                    var company = card.querySelector('.job-card-container__company-name, .artdeco-entity-lockup__subtitle');
                    var link = card.querySelector('a[href*="/jobs/view/"]');
                    
                    results.push({
                        title: title ? title.textContent.trim().substring(0, 50) : 'N/A',
                        company: company ? company.textContent.trim().substring(0, 30) : 'N/A',
                        hasLink: !!link
                    });
                }
            });
            return results;
        """)
        
        print(f"\n   找到 {len(jobs)} 个职位:")
        for i, job in enumerate(jobs, 1):
            print(f"     {i}. {job['title']} @ {job['company']}")
        
        # 点击第一个职位查看详情
        if jobs:
            print("\n🖱️ 点击第一个职位...")
            driver.execute_script("""
                var firstCard = document.querySelector('.job-card-container, .jobs-search-results__list-item');
                if (firstCard) firstCard.click();
            """)
            time.sleep(3)
            
            driver.save_screenshot("job_detail.png")
            print("📸 截图: job_detail.png")
            
            # 检测申请按钮
            buttons = driver.execute_script("""
                var results = {};
                
                // 检查 Easy Apply
                var easyApplyId = document.getElementById('jobs-apply-button-id');
                var easyApplyAria = document.querySelector('button[aria-label*="Easy Apply"]');
                results['easy_apply_id'] = !!easyApplyId;
                results['easy_apply_aria'] = !!easyApplyAria;
                
                // 检查所有按钮
                var allBtns = document.querySelectorAll('button');
                var btnTexts = [];
                allBtns.forEach(function(btn) {
                    var text = btn.textContent.trim();
                    if (text && text.length < 50) {
                        btnTexts.push(text);
                    }
                });
                results['all_buttons'] = btnTexts.slice(0, 10);
                
                return results;
            """)
            
            print("\n   按钮检测:")
            print(f"     Easy Apply (ID): {buttons.get('easy_apply_id')}")
            print(f"     Easy Apply (Aria): {buttons.get('easy_apply_aria')}")
            print(f"     所有按钮: {buttons.get('all_buttons')}")
        
        print("\n" + "="*60)
        print("✅ 测试完成")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        driver.save_screenshot("error.png")
    
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
