#!/usr/bin/env python3
"""
Stealth utilities for job application automation
整合 EasyApplyJobsBot 和 linkedin-application-bot 的最佳实践
包含：反检测、Cookie管理、智能等待、错误处理、截图等
"""

import os
import sys
import time
import pickle
import random
import logging
import hashlib
from pathlib import Path
from datetime import datetime
from typing import List, Optional, Callable

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

# 尝试导入 selenium-stealth
try:
    from selenium_stealth import stealth
    STEALTH_AVAILABLE = True
except ImportError:
    STEALTH_AVAILABLE = False

# 默认配置
DEFAULT_BOT_SPEED = 3  # medium speed
DEFAULT_COOKIES_DIR = Path("cookies")
DEFAULT_SCREENSHOTS_DIR = Path("screenshots")


def prRed(prt):
    """打印红色文字"""
    print(f"\033[91m{prt}\033[00m")


def prGreen(prt):
    """打印绿色文字"""
    print(f"\033[92m{prt}\033[00m")


def prYellow(prt):
    """打印黄色文字"""
    print(f"\033[93m{prt}\033[00m")


def prBlue(prt):
    """打印蓝色文字"""
    print(f"\033[94m{prt}\033[00m")


class StealthDriverManager:
    """
    管理带反检测功能的Chrome WebDriver
    整合了 reference-easy-apply-bot 的 stealth 配置
    """
    
    def __init__(self, 
                 headless: bool = False,
                 use_profile: bool = False,
                 profile_path: str = "",
                 bot_speed: int = DEFAULT_BOT_SPEED,
                 cookies_dir: Path = DEFAULT_COOKIES_DIR,
                 screenshots_dir: Path = DEFAULT_SCREENSHOTS_DIR):
        self.headless = headless
        self.use_profile = use_profile
        self.profile_path = profile_path
        self.bot_speed = bot_speed
        self.cookies_dir = cookies_dir
        self.screenshots_dir = screenshots_dir
        self.driver = None
        
        # 确保目录存在
        self.cookies_dir.mkdir(parents=True, exist_ok=True)
        self.screenshots_dir.mkdir(parents=True, exist_ok=True)
    
    def create_chrome_options(self) -> Options:
        """
        创建Chrome选项 - 整合 reference-easy-apply-bot 的反检测配置
        """
        options = Options()
        
        # 基础设置
        options.add_argument('--no-sandbox')
        options.add_argument("--ignore-certificate-errors")
        options.add_argument("--disable-extensions")
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--start-maximized")
        
        # 反检测关键设置
        options.add_argument("--disable-blink-features")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option('useAutomationExtension', False)
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        
        # Headless模式
        if self.headless:
            options.add_argument("--headless=new")
            options.add_argument("--disable-gpu")
        
        # 用户代理 - 模拟真实浏览器
        user_agent = (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        options.add_argument(f"--user-agent={user_agent}")
        
        # 使用Chrome Profile (推荐，避免重复登录)
        if self.use_profile and self.profile_path:
            # 处理不同系统的路径分隔符
            normalized_path = self.profile_path.replace('\\', os.sep).replace('/', os.sep)
            last_sep_index = normalized_path.rfind(os.sep)
            
            if last_sep_index != -1:
                user_data_dir = normalized_path[:last_sep_index]
                profile_dir = normalized_path[last_sep_index + 1:]
                options.add_argument(f'--user-data-dir={user_data_dir}')
                options.add_argument(f"--profile-directory={profile_dir}")
            else:
                options.add_argument("--incognito")
        else:
            options.add_argument("--incognito")
        
        # 禁用密码管理器弹窗
        options.add_experimental_option("prefs", {
            "credentials_enable_service": False,
            "profile.password_manager_enabled": False,
            "download.default_directory": str(Path.home() / "Downloads"),
            "download.prompt_for_download": False,
        })
        
        return options
    
    def setup_driver(self) -> webdriver.Chrome:
        """
        设置并返回配置好的Chrome WebDriver
        包含 ChromeDriverManager 自动管理驱动版本
        """
        prYellow("🤖 初始化 Chrome WebDriver...")
        
        options = self.create_chrome_options()
        
        try:
            # 使用 ChromeDriverManager 自动管理驱动
            # 参考 reference-easy-apply-bot 的处理方式
            chrome_install = ChromeDriverManager().install()
            
            # 处理不同平台的 chromedriver 路径
            if sys.platform == "win32":
                folder = os.path.dirname(chrome_install)
                chromedriver_path = os.path.join(folder, "chromedriver.exe")
                service = Service(chromedriver_path)
            else:
                service = Service(chrome_install)
            
            self.driver = webdriver.Chrome(service=service, options=options)
            
        except Exception as e:
            prYellow(f"⚠️ 警告: 无法使用显式 chromedriver 路径，使用默认方式: {str(e)[:50]}")
            self.driver = webdriver.Chrome(
                service=Service(ChromeDriverManager().install()),
                options=options
            )
        
        # 应用 selenium-stealth (如果可用)
        if STEALTH_AVAILABLE:
            try:
                stealth(self.driver,
                        languages=["en-US", "en"],
                        vendor="Google Inc.",
                        platform="Win32" if sys.platform == "win32" else "MacIntel",
                        webgl_vendor="Intel Inc.",
                        renderer="Intel Iris OpenGL Engine",
                        fix_hairline=True)
                prGreen("✅ Stealth 模式已启用")
            except Exception as e:
                prYellow(f"⚠️ 警告: 无法应用 stealth 模式: {str(e)[:50]}")
        else:
            prYellow("⚠️ 提示: 安装 selenium-stealth 以获得更好的反检测保护")
            prYellow("   pip install selenium-stealth")
        
        # 隐藏 webdriver 标志
        self.driver.execute_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        )
        
        prGreen("✅ Chrome WebDriver 初始化完成")
        return self.driver
    
    def get_hash(self, string: str) -> str:
        """生成字符串的MD5哈希"""
        return hashlib.md5(string.encode('utf-8')).hexdigest()
    
    def get_cookies_path(self, identifier: str) -> Path:
        """获取cookie文件路径"""
        return self.cookies_dir / f"{self.get_hash(identifier)}.pkl"
    
    def save_cookies(self, identifier: str) -> bool:
        """
        保存Cookies到文件
        从 reference-easy-apply-bot 复制
        """
        if not self.driver:
            prRed("❌ WebDriver 未初始化")
            return False
        
        try:
            cookies_path = self.get_cookies_path(identifier)
            cookies = self.driver.get_cookies()
            
            with open(cookies_path, 'wb') as f:
                pickle.dump(cookies, f)
            
            prGreen(f"✅ Cookies 已保存: {cookies_path}")
            return True
            
        except Exception as e:
            prYellow(f"⚠️ 警告: 无法保存 cookies: {str(e)[:80]}")
            return False
    
    def load_cookies(self, identifier: str) -> bool:
        """
        从文件加载Cookies
        从 reference-easy-apply-bot 复制
        """
        if not self.driver:
            prRed("❌ WebDriver 未初始化")
            return False
        
        cookies_path = self.get_cookies_path(identifier)
        
        if not cookies_path.exists():
            prYellow(f"⚠️ Cookie 文件不存在: {cookies_path}")
            return False
        
        try:
            with open(cookies_path, 'rb') as f:
                cookies = pickle.load(f)
            
            self.driver.delete_all_cookies()
            
            for cookie in cookies:
                try:
                    # 移除可能导致问题的字段
                    if 'sameSite' in cookie and cookie['sameSite'] not in ['Strict', 'Lax', 'None']:
                        del cookie['sameSite']
                    self.driver.add_cookie(cookie)
                except Exception as e:
                    logging.debug(f"添加 cookie 失败: {e}")
            
            prGreen(f"✅ Cookies 已加载: {cookies_path}")
            return True
            
        except Exception as e:
            prYellow(f"⚠️ 警告: 无法加载 cookies: {str(e)[:80]}")
            return False
    
    def take_screenshot(self, name: str = None, subdirectory: str = None) -> Optional[Path]:
        """截取当前屏幕"""
        if not self.driver:
            prRed("❌ WebDriver 未初始化")
            return None
        
        if name is None:
            name = f"screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # 处理子目录
        screenshot_dir = self.screenshots_dir
        if subdirectory:
            screenshot_dir = self.screenshots_dir / subdirectory
            screenshot_dir.mkdir(parents=True, exist_ok=True)
        
        screenshot_path = screenshot_dir / f"{name}.png"
        
        try:
            self.driver.save_screenshot(str(screenshot_path))
            prGreen(f"✅ 截图已保存: {screenshot_path}")
            return screenshot_path
        except Exception as e:
            prRed(f"❌ 截图失败: {e}")
            return None
    
    def random_delay(self, min_seconds: float = None, max_seconds: float = None):
        """
        随机延迟 - 避免固定间隔被检测
        从 reference-easy-apply-bot 复制
        """
        if min_seconds is None:
            min_seconds = 1
        if max_seconds is None:
            max_seconds = self.bot_speed
        
        delay = random.uniform(min_seconds, max_seconds)
        time.sleep(delay)
        return delay
    
    def safe_find_element(self, by: By, selectors: List[str], timeout: int = 10):
        """
        安全查找元素 - 支持多种 fallback selector
        """
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        
        for selector in selectors:
            try:
                element = WebDriverWait(self.driver, timeout).until(
                    EC.presence_of_element_located((by, selector))
                )
                return element
            except:
                continue
        
        return None
    
    def safe_click(self, element, retries: int = 3) -> bool:
        """安全点击元素，带重试"""
        from selenium.common.exceptions import ElementClickInterceptedException, StaleElementReferenceException
        
        for i in range(retries):
            try:
                # 滚动到元素
                self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", element)
                self.random_delay(0.5, 1.5)
                element.click()
                return True
            except (ElementClickInterceptedException, StaleElementReferenceException) as e:
                if i < retries - 1:
                    prYellow(f"⚠️ 点击失败，重试 ({i+1}/{retries}): {str(e)[:50]}")
                    self.random_delay(1, 2)
                else:
                    prRed(f"❌ 点击失败，已达最大重试次数")
                    return False
            except Exception as e:
                prRed(f"❌ 点击时出错: {e}")
                return False
        
        return False
    
    def element_exists(self, by: By, selector: str) -> bool:
        """检查元素是否存在"""
        try:
            elements = self.driver.find_elements(by, selector)
            return len(elements) > 0 and any(e.is_displayed() for e in elements)
        except:
            return False
    
    def close(self):
        """关闭浏览器"""
        if self.driver:
            self.driver.quit()
            prGreen("✅ WebDriver 已关闭")


class LoggerMixin:
    """日志混入类，提供统一的日志功能"""
    
    def __init__(self, name: str = None):
        self.logger = self._setup_logger(name or self.__class__.__name__)
    
    def _setup_logger(self, name: str) -> logging.Logger:
        """设置日志记录器"""
        logger = logging.getLogger(name)
        
        if not logger.handlers:
            logger.setLevel(logging.DEBUG)
            
            # 控制台处理器
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.INFO)
            console_format = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            console_handler.setFormatter(console_format)
            logger.addHandler(console_handler)
        
        return logger
    
    def log_info(self, msg: str):
        self.logger.info(msg)
        prGreen(f"ℹ️ {msg}")
    
    def log_warning(self, msg: str):
        self.logger.warning(msg)
        prYellow(f"⚠️ {msg}")
    
    def log_error(self, msg: str):
        self.logger.error(msg)
        prRed(f"❌ {msg}")
    
    def log_debug(self, msg: str):
        self.logger.debug(msg)


# 便捷函数
def setup_stealth_driver(headless: bool = False, 
                         use_profile: bool = False,
                         profile_path: str = "") -> tuple:
    """
    快速设置带stealth功能的WebDriver
    
    Returns:
        tuple: (driver, manager)
    """
    manager = StealthDriverManager(
        headless=headless,
        use_profile=use_profile,
        profile_path=profile_path
    )
    driver = manager.setup_driver()
    return driver, manager


def with_retry(max_retries: int = 3, delay: float = 2.0):
    """
    装饰器：为函数添加重试机制
    
    Usage:
        @with_retry(max_retries=3)
        def my_function():
            pass
    """
    def decorator(func: Callable):
        def wrapper(*args, **kwargs):
            for i in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if i < max_retries - 1:
                        prYellow(f"⚠️ {func.__name__} 失败，重试 ({i+1}/{max_retries}): {str(e)[:50]}")
                        time.sleep(delay * (i + 1))  # 递增延迟
                    else:
                        prRed(f"❌ {func.__name__} 失败，已达最大重试次数")
                        raise
            return None
        return wrapper
    return decorator


# 兼容性导入 - 保持与 reference-easy-apply-bot 相同的API
def chromeBrowserOptions(headless: bool = False, profile_path: str = "") -> Options:
    """
    兼容 reference-easy-apply-bot 的API
    """
    manager = StealthDriverManager(headless=headless, profile_path=profile_path)
    return manager.create_chrome_options()


# 导出主要类
__all__ = [
    'StealthDriverManager',
    'LoggerMixin',
    'setup_stealth_driver',
    'with_retry',
    'chromeBrowserOptions',
    'prRed',
    'prGreen',
    'prYellow',
    'prBlue',
    'STEALTH_AVAILABLE',
]