#!/usr/bin/env python3
"""
测试整合后的 auto-job-apply 系统
验证所有改进是否正常工作
"""

import sys
import os
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

def test_imports():
    """测试所有导入是否正常"""
    print("=" * 60)
    print("🧪 测试模块导入")
    print("=" * 60)
    
    tests = []
    
    # 测试 utils_stealth
    try:
        from utils_stealth import (
            StealthDriverManager, prRed, prGreen, prYellow, prBlue,
            setup_stealth_driver, with_retry, chromeBrowserOptions
        )
        print("✅ utils_stealth 导入成功")
        tests.append(("utils_stealth", True, None))
    except Exception as e:
        print(f"❌ utils_stealth 导入失败: {e}")
        tests.append(("utils_stealth", False, str(e)))
    
    # 测试 selenium-stealth
    try:
        from selenium_stealth import stealth
        print("✅ selenium-stealth 可用")
        tests.append(("selenium-stealth", True, None))
    except ImportError:
        print("⚠️ selenium-stealth 未安装 (pip install selenium-stealth)")
        tests.append(("selenium-stealth", False, "未安装"))
    
    # 测试 webdriver_manager
    try:
        from webdriver_manager.chrome import ChromeDriverManager
        print("✅ webdriver-manager 可用")
        tests.append(("webdriver-manager", True, None))
    except ImportError as e:
        print(f"❌ webdriver-manager 导入失败: {e}")
        tests.append(("webdriver-manager", False, str(e)))
    
    # 测试 linkedin_easy_apply_fixed
    try:
        import linkedin_easy_apply_fixed
        print("✅ linkedin_easy_apply_fixed 导入成功")
        tests.append(("linkedin_easy_apply_fixed", True, None))
    except Exception as e:
        print(f"❌ linkedin_easy_apply_fixed 导入失败: {e}")
        tests.append(("linkedin_easy_apply_fixed", False, str(e)))
    
    # 测试 greenhouse_auto_apply_fixed
    try:
        import greenhouse_auto_apply_fixed
        print("✅ greenhouse_auto_apply_fixed 导入成功")
        tests.append(("greenhouse_auto_apply_fixed", True, None))
    except Exception as e:
        print(f"❌ greenhouse_auto_apply_fixed 导入失败: {e}")
        tests.append(("greenhouse_auto_apply_fixed", False, str(e)))
    
    return tests


def test_stealth_features():
    """测试 StealthDriverManager 功能"""
    print("\n" + "=" * 60)
    print("🛡️ 测试 Stealth 功能")
    print("=" * 60)
    
    from utils_stealth import StealthDriverManager, STEALTH_AVAILABLE
    
    print(f"Stealth 可用: {STEALTH_AVAILABLE}")
    
    # 测试 Chrome 选项创建
    try:
        manager = StealthDriverManager(headless=True)
        options = manager.create_chrome_options()
        
        # 检查关键反检测选项
        args = options.arguments
        checks = {
            "--disable-blink-features=AutomationControlled": "--disable-blink-features=AutomationControlled" in args,
            "--disable-extensions": "--disable-extensions" in args,
            "--no-sandbox": "--no-sandbox" in args,
        }
        
        for name, passed in checks.items():
            if passed:
                print(f"✅ {name} 已设置")
            else:
                print(f"⚠️ {name} 未设置")
        
        # 检查实验性选项
        exp_options = options.experimental_options
        if 'excludeSwitches' in exp_options and 'enable-automation' in exp_options['excludeSwitches']:
            print("✅ enable-automation 已从 excludeSwitches 中移除")
        else:
            print("⚠️ enable-automation 排除设置有问题")
        
        print("✅ Chrome 选项创建成功")
        return True
        
    except Exception as e:
        print(f"❌ Stealth 功能测试失败: {e}")
        return False


def test_config_loading():
    """测试配置文件加载"""
    print("\n" + "=" * 60)
    print("📄 测试配置文件加载")
    print("=" * 60)
    
    try:
        import yaml
        config_path = Path(__file__).parent / "config" / "profile.yaml"
        
        if config_path.exists():
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            
            required_keys = ['personal_info', 'application_settings']
            for key in required_keys:
                if key in config:
                    print(f"✅ {key} 配置存在")
                else:
                    print(f"❌ {key} 配置缺失")
            
            # 检查 personal_info
            personal = config.get('personal_info', {})
            info_keys = ['email', 'first_name', 'last_name']
            for key in info_keys:
                if personal.get(key):
                    print(f"✅ personal_info.{key} = {personal[key][:20]}...")
                else:
                    print(f"⚠️ personal_info.{key} 为空")
            
            return True
        else:
            print(f"❌ 配置文件不存在: {config_path}")
            return False
            
    except Exception as e:
        print(f"❌ 配置加载失败: {e}")
        return False


def test_directory_structure():
    """测试目录结构"""
    print("\n" + "=" * 60)
    print("📁 测试目录结构")
    print("=" * 60)
    
    base_dir = Path(__file__).parent
    
    required_dirs = [
        "cookies",
        "screenshots",
        "logs",
        "config"
    ]
    
    for dir_name in required_dirs:
        dir_path = base_dir / dir_name
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"✅ 创建目录: {dir_name}")
        else:
            print(f"✅ 目录存在: {dir_name}")
    
    return True


def main():
    """主测试函数"""
    print("\n" + "=" * 60)
    print("🚀 Auto-Job-Apply 整合测试")
    print("整合 EasyApplyJobsBot 和 linkedin-application-bot 最佳实践")
    print("=" * 60)
    
    all_passed = True
    
    # 运行所有测试
    results = test_imports()
    all_passed = all(r[1] for r in results) and all_passed
    
    stealth_passed = test_stealth_features()
    all_passed = stealth_passed and all_passed
    
    config_passed = test_config_loading()
    all_passed = config_passed and all_passed
    
    dir_passed = test_directory_structure()
    all_passed = dir_passed and all_passed
    
    # 总结
    print("\n" + "=" * 60)
    print("📊 测试结果总结")
    print("=" * 60)
    
    print(f"\n模块导入测试:")
    for name, passed, error in results:
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"  {status}: {name}")
        if error:
            print(f"      错误: {error}")
    
    print(f"\nStealth 功能: {'✅ 通过' if stealth_passed else '❌ 失败'}")
    print(f"配置加载: {'✅ 通过' if config_passed else '❌ 失败'}")
    print(f"目录结构: {'✅ 通过' if dir_passed else '❌ 失败'}")
    
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 所有测试通过！系统已准备好使用。")
        print("\n使用示例:")
        print("  python linkedin_easy_apply_fixed.py --keywords 'Director' --max-jobs 3")
        print("  python greenhouse_auto_apply_fixed.py --url 'https://boards.greenhouse.io/...'")
    else:
        print("⚠️ 部分测试失败，请检查错误信息。")
    print("=" * 60)
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
