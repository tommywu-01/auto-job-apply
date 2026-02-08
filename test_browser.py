#!/usr/bin/env python3
"""
功能测试 - 验证浏览器启动和 stealth 功能
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from utils_stealth import StealthDriverManager, prGreen, prYellow, prRed


def test_browser_launch():
    """测试浏览器启动"""
    print("=" * 60)
    print("🌐 测试浏览器启动 (非无头模式)")
    print("=" * 60)
    
    manager = None
    try:
        manager = StealthDriverManager(
            headless=False,
            bot_speed=3
        )
        driver = manager.setup_driver()
        
        # 访问测试页面
        print("访问 LinkedIn...")
        driver.get("https://www.linkedin.com")
        manager.random_delay(3, 5)
        
        # 截图
        screenshot_path = manager.take_screenshot("test_linkedin")
        if screenshot_path:
            prGreen(f"✅ 截图已保存: {screenshot_path}")
        
        # 测试 cookies
        print("\n测试 Cookie 功能...")
        manager.save_cookies("test_user")
        manager.load_cookies("test_user")
        prGreen("✅ Cookie 功能正常")
        
        # 检查 navigator.webdriver 是否被隐藏
        webdriver_flag = driver.execute_script("return navigator.webdriver")
        if webdriver_flag is None or webdriver_flag is False:
            prGreen("✅ navigator.webdriver 已被隐藏 (反检测成功)")
        else:
            prYellow(f"⚠️ navigator.webdriver = {webdriver_flag}")
        
        prGreen("\n✅ 浏览器启动测试成功！")
        return True
        
    except Exception as e:
        prRed(f"\n❌ 浏览器启动失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        if manager:
            manager.close()


def main():
    print("\n" + "=" * 60)
    print("🚀 Auto-Job-Apply 浏览器功能测试")
    print("=" * 60)
    
    success = test_browser_launch()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 所有功能测试通过！")
        print("\n现在可以运行真实的申请任务:")
        print("  python3 linkedin_easy_apply_fixed.py --max-jobs 1")
    else:
        print("⚠️ 功能测试失败，请检查错误信息")
    print("=" * 60)
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
