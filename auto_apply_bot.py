#!/usr/bin/env python3
"""
LinkedIn Easy Apply - 全自动批量申请系统 v5.1 (修复版)
修复 Easy Apply 按钮点击问题
"""

import os
import json
import time
import random
from datetime import datetime
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from dual_notify_system import DualNotifySystem, check_mission_control_messages

# 配置 - 今日目标：20个申请
CONFIG = {
    'search_keywords': ['Creative Director', 'Creative Technologist', 'Director of Technical Services', 'VP Creative', 'Art Director'],
    'location': 'New York',
    'max_applications_per_run': 20,  # 今日目标：20个申请
    'min_match_score': 60,
}

class LinkedInAutoApply:
    def __init__(self):
        self.driver = None
        self.results = []
        self.log_file = Path('logs/applications.json')
        self.log_file.parent.mkdir(exist_ok=True)
        self.log_dir = Path('logs')
        self.log_dir.mkdir(exist_ok=True)
        self.notifier = DualNotifySystem()  # 双重通知系统
        self.context = {'step': 'init', 'job_url': '', 'retry_count': 0}
        
    def setup_driver(self):
        """初始化浏览器 - 使用持久化profile保持登录状态"""
        options = Options()
        options.add_argument('--no-sandbox')
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-extensions')
        
        # 使用持久化用户数据目录保持登录状态
        user_data_dir = Path.home() / '.linkedin_automation_profile'
        user_data_dir.mkdir(exist_ok=True)
        options.add_argument(f'--user-data-dir={user_data_dir}')
        
        # 禁用自动化检测
        options.add_experimental_option('excludeSwitches', ['enable-automation'])
        options.add_experimental_option('useAutomationExtension', False)
        
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=options)
        self.driver.set_page_load_timeout(30)
        
        # 加载之前保存的cookies
        self.load_cookies()
    
    def save_cookies(self):
        """保存cookies到文件"""
        try:
            cookies = self.driver.get_cookies()
            cookies_file = self.log_dir / 'linkedin_cookies.json'
            with open(cookies_file, 'w') as f:
                json.dump(cookies, f)
            print("   💾 Cookies已保存")
        except Exception as e:
            print(f"   ⚠️ 保存cookies失败: {e}")
    
    def load_cookies(self):
        """从文件加载cookies"""
        try:
            cookies_file = self.log_dir / 'linkedin_cookies.json'
            if cookies_file.exists():
                with open(cookies_file) as f:
                    cookies = json.load(f)
                for cookie in cookies:
                    try:
                        self.driver.add_cookie(cookie)
                    except:
                        pass
                print("   📂 Cookies已加载")
        except Exception as e:
            print(f"   ⚠️ 加载cookies失败: {e}")
    
    def is_logged_in(self):
        """检查是否已登录"""
        try:
            self.driver.get("https://www.linkedin.com/feed")
            time.sleep(2)
            # 检查是否有feed页面特征
            current_url = self.driver.current_url
            if "feed" in current_url or "linkedin.com/in/" in current_url:
                print("   ✅ 已登录状态")
                return True
            # 检查是否有登录框
            login_elements = self.driver.find_elements(By.ID, "username")
            if len(login_elements) == 0:
                print("   ✅ 已登录状态")
                return True
            return False
        except Exception as e:
            print(f"   ⚠️ 检查登录状态失败: {e}")
            return False
        
    def login(self):
        """登录 LinkedIn - 智能检查避免重复登录"""
        print("\n🔐 检查登录状态...")
        
        # 先检查是否已登录
        if self.is_logged_in():
            print("✅ 已登录，跳过登录步骤")
            return
        
        print("🔐 需要登录...")
        self.driver.get("https://www.linkedin.com/login")
        time.sleep(2)
        
        try:
            self.driver.find_element(By.ID, "username").send_keys("wuyuehao2001@outlook.com")
            self.driver.find_element(By.ID, "password").send_keys("Tommy12345#")
            self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
            time.sleep(4)
            
            # 保存cookies供下次使用
            self.save_cookies()
            print("✅ 登录成功，已保存登录状态")
            
        except Exception as e:
            print(f"❌ 登录失败: {e}")
            raise
        
    def search_easy_apply_jobs(self, keyword):
        """搜索 Easy Apply 职位"""
        print(f"\n🔍 搜索: {keyword}")
        search_url = f"https://www.linkedin.com/jobs/search/?keywords={keyword.replace(' ', '%20')}&location={CONFIG['location'].replace(' ', '%20')}&f_AL=true"
        self.driver.get(search_url)
        time.sleep(5)
        
        # 滚动页面加载更多职位
        self.driver.execute_script("window.scrollTo(0, 500)")
        time.sleep(2)
        
        # 获取职位列表
        jobs = self.driver.execute_script(r"""
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
        
        print(f"   找到 {len(jobs)} 个职位")
        return jobs
    
    def calculate_match_score(self, title):
        """计算职位匹配分数"""
        title_lower = title.lower()
        score = 0
        
        keywords = {
            'creative director': 100,
            'creative technologist': 95,
            'technical director': 90,
            'director of technical': 90,
            'vp creative': 85,
            'senior creative': 80,
        }
        
        for keyword, points in keywords.items():
            if keyword in title_lower:
                score = max(score, points)
        
        exclude_words = ['intern', 'junior', 'entry level']
        for word in exclude_words:
            if word in title_lower:
                score -= 30
        
        return max(0, min(100, score))
    
    def is_already_applied(self, job_id):
        """检查是否已申请过"""
        if not self.log_file.exists():
            return False
        try:
            with open(self.log_file) as f:
                history = json.load(f)
            return any(app.get('job_id') == job_id for app in history)
        except:
            return False
    
    def click_easy_apply_button(self):
        """点击 Easy Apply 按钮 - 多种方式尝试"""
        print("\n🖱️ 点击 Easy Apply...")
        
        # 等待按钮加载
        time.sleep(2)
        
        # 尝试多种方式点击
        result = self.driver.execute_script("""
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
                    return 'Clicked by aria-label';
                }
            }
            
            // 方式3: 通过文本内容
            var allBtns = document.querySelectorAll('button');
            for (var b of allBtns) {
                if (b.textContent.includes('Easy Apply') && b.offsetParent !== null) {
                    b.click();
                    return 'Clicked by text';
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
            
            return 'Button not found';
        """)
        
        print(f"   {result}")
        if 'not found' in result:
            # 截图保存以便调试
            try:
                self.driver.save_screenshot(f"logs/easy_apply_not_found_{int(time.time())}.png")
            except:
                pass
            return False
        
        time.sleep(5)
        return True
    
    def fill_form(self):
        """填写表单"""
        self.driver.execute_script("""
            var inputs = document.querySelectorAll('.artdeco-modal input[type="text"], .artdeco-modal input[type="number"], .artdeco-modal textarea');
            
            inputs.forEach(function(input) {
                if (!input.value && input.offsetParent !== null) {
                    var label = document.querySelector('label[for="' + input.id + '"]');
                    var questionText = '';
                    
                    if (label) {
                        questionText = label.textContent.toLowerCase();
                    } else {
                        var parent = input.closest('.jobs-easy-apply-form-element, .artdeco-text-input--container');
                        if (parent) {
                            var labelEl = parent.querySelector('label, .jobs-easy-apply-form-element__label');
                            if (labelEl) questionText = labelEl.textContent.toLowerCase();
                        }
                    }
                    
                    var answer = '';
                    if (questionText.includes('photo') || questionText.includes('shoot')) answer = '5';
                    else if (questionText.includes('year') && questionText.includes('experience')) answer = '5';
                    else if (questionText.includes('sponsor') || questionText.includes('visa')) answer = 'Yes';
                    else if (questionText.includes('salary') || questionText.includes('pay')) answer = '150000';
                    else if (questionText.includes('notice') || questionText.includes('start')) answer = '2 weeks';
                    else answer = '5';
                    
                    if (answer) {
                        input.value = answer;
                        input.dispatchEvent(new Event('input', { bubbles: true }));
                        input.dispatchEvent(new Event('change', { bubbles: true }));
                    }
                }
            });
        """)
    
    def click_button(self, button_texts):
        """点击按钮"""
        for text in button_texts:
            result = self.driver.execute_script("""
                var buttons = document.querySelectorAll('.artdeco-modal button');
                for (var btn of buttons) {
                    if (btn.textContent.toLowerCase().includes('""" + text + """') && !btn.disabled && btn.offsetParent !== null) {
                        btn.click();
                        return 'Clicked';
                    }
                }
                return false;
            """)
            if result:
                return True
        return False
    
    def is_application_complete(self):
        """检查申请是否完成"""
        return self.driver.execute_script("""
            return document.body.textContent.includes('Application sent') ||
                   document.body.textContent.includes('Successfully') ||
                   document.querySelector('.jobs-easy-apply-content__success') !== null;
        """)
    
    def apply_to_job(self, job):
        """申请单个职位"""
        print(f"\n📝 申请: {job['title'][:50]}")
        print(f"   公司: {job['company']}")
        
        # 更新上下文
        self.context['job_url'] = job.get('url', '')
        self.context['retry_count'] = 0
        
        try:
            # 访问职位页面
            self.context['step'] = 'visit_job'
            self.driver.get(job['url'])
            time.sleep(4)
            
            # 点击 Easy Apply
            self.context['step'] = 'click_easy_apply'
            if not self.click_easy_apply_button():
                print("   ❌ 无法点击 Easy Apply 按钮")
                # 发送双重通知
                self.notifier.notify_error(
                    "Easy Apply button not found",
                    self.context,
                    self.take_screenshot()
                )
                self.record_application(job, 'error')
                return False
            
            # 处理多步骤申请
            for step in range(8):
                self.context['step'] = f'step_{step+1}'
                print(f"   Step {step + 1}...")
                
                # 填写表单
                self.fill_form()
                
                # 点击按钮
                clicked = self.click_button(['next', 'review', 'submit'])
                time.sleep(3)
                
                # 检查是否完成
                if self.is_application_complete():
                    print("   🎉 申请成功！")
                    self.notifier.notify_success(job)
                    self.record_application(job, 'success')
                    return True
                
                if not clicked:
                    print("   ⚠️ 未找到可点击按钮")
                    # 发送通知
                    self.notifier.notify_error(
                        "Button not found in step " + str(step+1),
                        self.context
                    )
                    break
            
            print("   ⚠️ 申请未完成")
            self.record_application(job, 'incomplete')
            return False
            
        except Exception as e:
            print(f"   ❌ 错误: {e}")
            # 发送双重通知
            self.notifier.notify_error(
                str(e),
                self.context,
                self.take_screenshot()
            )
            self.record_application(job, 'error')
            return False
    
    def record_application(self, job, status):
        """记录申请结果"""
        record = {
            'timestamp': datetime.now().isoformat(),
            'job_id': job.get('id', ''),
            'title': job.get('title', ''),
            'company': job.get('company', ''),
            'url': job.get('url', ''),
            'match_score': job.get('match_score', 0),
            'status': status
        }
        
        history = []
        if self.log_file.exists():
            try:
                with open(self.log_file) as f:
                    history = json.load(f)
            except:
                pass
        
        history.append(record)
        
        with open(self.log_file, 'w') as f:
            json.dump(history, f, indent=2)
        
        self.results.append(record)
    
    def take_screenshot(self):
        """截图"""
        try:
            screenshot_path = self.log_dir / f'error_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png'
            self.driver.save_screenshot(str(screenshot_path))
            return screenshot_path
        except:
            return None
    
    def run(self):
        """主运行流程"""
        print("="*60)
        print("🚀 LinkedIn Easy Apply - 全自动批量申请系统 v5.1")
        print(f"⏰ 启动时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*60)
        
        try:
            self.setup_driver()
            self.login()
            
            total_applied = 0
            
            for keyword in CONFIG['search_keywords']:
                if total_applied >= CONFIG['max_applications_per_run']:
                    break
                
                jobs = self.search_easy_apply_jobs(keyword)
                
                for job in jobs:
                    if total_applied >= CONFIG['max_applications_per_run']:
                        break
                    
                    # 计算匹配分数
                    score = self.calculate_match_score(job['title'])
                    job['match_score'] = score
                    
                    # 检查是否已申请
                    if self.is_already_applied(job['id']):
                        print(f"   ⏭️ 已申请过: {job['title'][:40]}")
                        continue
                    
                    if score >= CONFIG['min_match_score']:
                        print(f"   ✅ 匹配分数 {score}% - {job['title'][:40]}")
                        success = self.apply_to_job(job)
                        if success:
                            total_applied += 1
                        
                        # 随机等待
                        wait_time = random.uniform(5, 10)
                        print(f"   等待 {wait_time:.1f} 秒...")
                        time.sleep(wait_time)
                    else:
                        print(f"   ❌ 匹配分数 {score}% 太低 - {job['title'][:40]}")
            
            print("\n" + "="*60)
            print(f"✅ 本次共申请 {total_applied} 个职位")
            print("="*60)
            
            # 生成报告
            self.generate_report()
            
        except Exception as e:
            print(f"\n❌ 运行错误: {e}")
            # 发送双重通知
            self.context['step'] = 'fatal_error'
            self.notifier.notify_error(
                f"Fatal error: {str(e)}",
                self.context,
                self.take_screenshot()
            )
            import traceback
            traceback.print_exc()
        
        finally:
            if self.driver:
                self.driver.quit()
    
    def generate_report(self):
        """生成申请报告"""
        if not self.results:
            return
        
        report_file = Path(f"logs/report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
        
        with open(report_file, 'w') as f:
            f.write("LinkedIn Easy Apply - 申请报告\n")
            f.write("="*60 + "\n\n")
            
            success_count = sum(1 for r in self.results if r['status'] == 'success')
            f.write(f"总申请数: {len(self.results)}\n")
            f.write(f"成功: {success_count}\n")
            f.write(f"失败: {len(self.results) - success_count}\n\n")
            
            f.write("申请详情:\n")
            f.write("-"*60 + "\n")
            
            for r in self.results:
                f.write(f"\n职位: {r['title']}\n")
                f.write(f"公司: {r['company']}\n")
                f.write(f"匹配度: {r['match_score']}%\n")
                f.write(f"状态: {r['status']}\n")
                f.write(f"时间: {r['timestamp']}\n")
        
        print(f"\n📊 报告已保存: {report_file}")

if __name__ == "__main__":
    bot = LinkedInAutoApply()
    bot.run()
