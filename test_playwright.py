#!/usr/bin/env python3
"""
使用 Playwright 测试 LinkedIn Easy Apply
Playwright 对现代 Web 应用支持更好
"""

import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(viewport={'width': 1920, 'height': 1080})
        page = await context.new_page()
        
        try:
            # 登录
            print("🔐 登录 LinkedIn...")
            await page.goto("https://www.linkedin.com/login")
            await page.fill("#username", "wuyuehao2001@outlook.com")
            await page.fill("#password", "Tommy12345#")
            await page.click("button[type='submit']")
            await page.wait_for_timeout(3000)
            print("✅ 登录成功")
            
            # 搜索职位
            print("\n🔍 搜索职位...")
            await page.goto("https://www.linkedin.com/jobs/search/?keywords=Creative%20Director&location=New%20York&f_AL=true")
            await page.wait_for_timeout(4000)
            
            # 点击第一个职位
            print("\n📋 选择职位...")
            await page.click(".job-card-container")
            await page.wait_for_timeout(3000)
            
            # 点击 Easy Apply
            print("\n🖱️ 点击 Easy Apply...")
            await page.click("button[aria-label*='Easy Apply']")
            await page.wait_for_timeout(5000)
            
            # 等待弹窗出现
            print("\n🔍 等待弹窗...")
            
            # 尝试多种选择器
            selectors = [
                ".artdeco-modal",
                ".jobs-easy-apply-modal",
                "[role='dialog']",
            ]
            
            modal_found = False
            for selector in selectors:
                try:
                    await page.wait_for_selector(selector, timeout=5000)
                    print(f"✅ 找到弹窗: {selector}")
                    modal_found = True
                    break
                except:
                    continue
            
            if modal_found:
                # 分析表单
                print("\n📝 分析表单...")
                inputs = await page.query_selector_all(".artdeco-modal input, .artdeco-modal textarea, .artdeco-modal select")
                print(f"  找到 {len(inputs)} 个输入字段")
                
                # 显示字段信息
                for i, inp in enumerate(inputs[:5]):
                    name = await inp.get_attribute("name") or ""
                    id_attr = await inp.get_attribute("id") or ""
                    placeholder = await inp.get_attribute("placeholder") or ""
                    print(f"    {i+1}. {name or id_attr or placeholder}")
            else:
                print("⚠️ 未找到弹窗")
            
            await page.screenshot(path="playwright_result.png")
            print("\n📸 截图已保存")
            
        except Exception as e:
            print(f"\n❌ 错误: {e}")
            await page.screenshot(path="playwright_error.png")
        
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
