#!/usr/bin/env python3
"""
LinkedIn External Apply - 外部链接自动申请系统 v1.0
处理 LinkedIn 上标记为 "Apply"（非 Easy Apply）的职位
自动跳转到公司网站并完成申请
"""

import time
import yaml
from pathlib import Path
from urllib.parse import urlparse
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

def detect_ats_type(url):
    """检测 ATS 类型"""
    url_lower = url.lower()
    
    if 'greenhouse.io' in url_lower or 'boards.greenhouse' in url_lower:
        return 'greenhouse'
    elif 'lever.co' in url_lower:
        return 'lever'
    elif 'workday' in url_lower or 'myworkday' in url_lower:
        return 'workday'
    elif 'smartrecruiters' in url_lower:
        return 'smartrecruiters'
    elif 'jobs.ashby' in url_lower:
        return 'ashby'
    elif 'breezy' in url_lower:
        return 'breezy'
    else:
        return 'unknown'

def click_external_apply(driver):
    """点击外部申请按钮"""
    print("\n🖱️ 点击外部申请按钮...")
    
    result = driver.execute_script("""
        // 查找 Apply 按钮（非 Easy Apply）
        var buttons = document.querySelectorAll('button');
        for (var btn of buttons) {
            var text = btn.textContent.trim();
            var aria = btn.getAttribute('aria-label') || '';
            
            // Apply 按钮（不是 Easy Apply）
            if ((text === 'Apply' || text === 'Apply on company website' || 
                 aria.includes('Apply') && !aria.includes('Easy Apply')) &&
                btn.offsetParent !== null) {
                btn.click();
                return 'Clicked: ' + text;
            }
        }
        
        // 查找外部链接
        var links = document.querySelectorAll('a[href*="apply"], a[href*="jobs"], a[href*="careers"]');
        for (var link of links) {
            if (link.offsetParent !== null && 
                (link.textContent.includes('Apply') || link.textContent.includes('External'))) {
                link.click();
                return 'Clicked link: ' + link.textContent.trim();
            }
        }
        
        return 'Apply button not found';
    """)
    
    print(f"   {result}")
    return 'not found' not in result.lower()

def handle_greenhouse(driver, job):
    """处理 Greenhouse ATS"""
    print("\n🏢 检测到 Greenhouse ATS")
    
    # 等待页面加载
    time.sleep(3)
    
    # 填写表单
    try:
        # 基本信息
        driver.find_element(By.ID, "first_name").send_keys(PERSONAL.get('first_name', 'Tommy'))
        driver.find_element(By.ID, "last_name").send_keys(PERSONAL.get('last_name', 'Wu'))
        driver.find_element(By.ID, "email").send_keys(PERSONAL.get('email', 'tommy.wu@nyu.edu'))
        driver.find_element(By.ID, "phone").send_keys(PERSONAL.get('phone', '917-742-4303'))
        
        # 上传简历
        resume_path = str(Path.home() / "Downloads/TOMMY WU Resume Dec 2025.pdf")
        driver.find_element(By.CSS_SELECTOR, "input[type='file']").send_keys(resume_path)
        
        print("   ✅ 基本信息填写完成")
        return True
        
    except Exception as e:
        print(f"   ⚠️ 填写失败: {e}")
        return False

def handle_lever(driver, job):
    """处理 Lever ATS"""
    print("\n🏢 检测到 Lever ATS")
    
    time.sleep(3)
    
    try:
        # Lever 表单
        driver.find_element(By.NAME, "name").send_keys(f"{PERSONAL.get('first_name')} {PERSONAL.get('last_name')}")
        driver.find_element(By.NAME, "email").send_keys(PERSONAL.get('email'))
        
        # 电话可能在不同位置
        try:
            driver.find_element(By.NAME, "phone").send_keys(PERSONAL.get('phone'))
        except:
            pass
        
        # 上传简历
        resume_path = str(Path.home() / "Downloads/TOMMY WU Resume Dec 2025.pdf")
        driver.find_element(By.CSS_SELECTOR, "input[type='file']").send_keys(resume_path)
        
        print("   ✅ 基本信息填写完成")
        return True
        
    except Exception as e:
        print(f"   ⚠️ 填写失败: {e}")
        return False

def handle_workday(driver, job):
    """处理 Workday ATS"""
    print("\n🏢 检测到 Workday ATS")
    print("   ⚠️ Workday 需要登录，暂不支持自动申请")
    return False

def handle_external_apply(driver, job):
    """处理外部申请流程"""
    # 点击外部申请
    if not click_external_apply(driver):
        return False
    
    # 等待新窗口或跳转
    time.sleep(3)
    
    # 检查是否有新窗口
    windows = driver.window_handles
    if len(windows) > 1:
        driver.switch_to.window(windows[-1])
        print(f"\n🔄 切换到新窗口: {driver.current_url}")
    
    # 检测 ATS 类型
    ats_type = detect_ats_type(driver.current_url)
    print(f"   ATS 类型: {ats_type}")
    
    # 根据不同 ATS 处理
    if ats_type == 'greenhouse':
        return handle_greenhouse(driver, job)
    elif ats_type == 'lever':
        return handle_lever(driver, job)
    elif ats_type == 'workday':
        return handle_workday(driver, job)
    else:
        print(f"   ⚠️ 未知的 ATS 系统，需要手动处理")
        return False

def search_external_apply_jobs(driver, keyword):
    """搜索外部申请职位"""
    print(f"\n🔍 搜索: {keyword}")
    
    # 搜索所有职位
    search_url = f"https://www.linkedin.com/jobs/search/?keywords={keyword.replace(' ', '%20')}&location=New%20York"
    driver.get(search_url)
    time.sleep(5)
    
    # 获取职位列表，然后逐个检查
    jobs = driver.execute_script(r"""
        var jobCards = document.querySelectorAll('.job-card-container, .jobs-search-results__list-item');
        var results = [];
        jobCards.forEach(function(card, index) {
            if (index < 10) {
                var titleEl = card.querySelector('.job-card-list__title, strong');
                var companyEl = card.querySelector('.job-card-container__company-name, .artdeco-entity-lockup__subtitle');
                var linkEl = card.querySelector('a[href*="/jobs/view/"]');
                
                if (titleEl && linkEl) {
                    var href = linkEl.href;
                    var match = href.match(/\d+/);
                    results.push({
                        title: titleEl.textContent.trim(),
                        company: companyEl ? companyEl.textContent.trim() : 'Unknown',
                        url: href,
                        id: match ? match[0] : ''
                    });
                }
            }
        });
        return results;
    """)
    
    print(f"   找到 {len(jobs)} 个职位，检查申请类型...")
    
    # 逐个检查是否是外部申请
    external_jobs = []
    for job in jobs[:5]:  # 只检查前5个
        try:
            driver.get(job['url'])
            time.sleep(3)
            
            # 检查是否有 Easy Apply 按钮
            has_easy_apply = driver.execute_script("""
                var btn = document.getElementById('jobs-apply-button-id');
                var ariaBtns = document.querySelectorAll('button[aria-label*="Easy Apply"]');
                return !!(btn || ariaBtns.length > 0);
            """)
            
            if not has_easy_apply:
                job['apply_type'] = 'external'
                external_jobs.append(job)
                print(f"   ✅ 外部申请: {job['title'][:40]}")
            else:
                print(f"   ⏭️ Easy Apply: {job['title'][:40]}")
                
        except Exception as e:
            print(f"   ⚠️ 检查失败: {e}")
            continue
    
    print(f"\n   找到 {len(external_jobs)} 个外部申请职位")
    return external_jobs

def main():
    print("="*60)
    print("🚀 LinkedIn External Apply - 外部链接自动申请 v1.0")
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
        
        # 搜索外部申请职位
        jobs = search_external_apply_jobs(driver, "Creative Director")
        
        # 测试第一个外部申请职位
        if jobs:
            job = jobs[0]
            print(f"\n📋 测试职位: {job['title']}")
            print(f"   公司: {job['company']}")
            
            driver.get(job['url'])
            time.sleep(4)
            
            # 尝试外部申请
            handle_external_apply(driver, job)
            
            # 截图
            driver.save_screenshot("external_apply_test.png")
            print("\n📸 截图: external_apply_test.png")
        else:
            print("\n⚠️ 未找到外部申请职位")
        
        print("\n" + "="*60)
        print("✅ 测试完成")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        driver.save_screenshot("external_error.png")
    
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
