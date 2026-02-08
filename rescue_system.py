#!/usr/bin/env python3
"""
LinkedIn Easy Apply - 故障自动召唤系统
当申请流程卡住时，自动通过 Mission Control 召唤救援
"""

import os
import json
import time
from datetime import datetime
from pathlib import Path

# Mission Control 配置
MISSION_CONTROL = {
    'notify_file': '/tmp/mission-control-notify-main.txt',
    'rescue_bot_id': 'jn7apr58t773gffa140hktc9ds80fvqr',  # Rescue Bot
    'botty_id': 'jn78tecygdgddznnd4vjvjdw9980f9je',  # Botty (self)
}

class RescueSystem:
    def __init__(self):
        self.log_dir = Path('logs')
        self.log_dir.mkdir(exist_ok=True)
        self.error_count = 0
        self.max_retries = 3
        
    def send_mission_control_alert(self, error_type, details, screenshot_path=None):
        """通过 Mission Control 发送求救信号"""
        
        alert = {
            'timestamp': datetime.now().isoformat(),
            'from': 'linkedin-easy-apply-bot',
            'to': 'botty',
            'priority': 'high',
            'error_type': error_type,
            'details': details,
            'screenshot': str(screenshot_path) if screenshot_path else None,
            'request': 'troubleshoot_and_resume',
            'job_url': details.get('job_url', 'unknown'),
            'step': details.get('current_step', 'unknown')
        }
        
        # 写入 Mission Control 通知文件
        notify_file = Path(MISSION_CONTROL['notify_file'])
        with open(notify_file, 'w') as f:
            json.dump(alert, f, indent=2)
        
        print(f"🚨 Mission Control 求救信号已发送: {error_type}")
        return True
    
    def is_stuck(self, last_progress_time, timeout=300):
        """检测是否卡住（默认5分钟无进展视为卡住）"""
        return (time.time() - last_progress_time) > timeout
    
    def record_progress(self, step, message):
        """记录进度"""
        progress_file = self.log_dir / 'progress.json'
        progress = {
            'timestamp': datetime.now().isoformat(),
            'step': step,
            'message': message
        }
        
        history = []
        if progress_file.exists():
            try:
                with open(progress_file) as f:
                    history = json.load(f)
            except:
                pass
        
        history.append(progress)
        
        with open(progress_file, 'w') as f:
            json.dump(history[-20:], f, indent=2)  # 保留最近20条
        
        return time.time()
    
    def handle_error(self, error, context, driver=None):
        """处理错误并决定是否需要救援"""
        self.error_count += 1
        
        print(f"\n❌ 错误 #{self.error_count}: {error}")
        
        # 截图
        screenshot_path = None
        if driver:
            try:
                screenshot_path = self.log_dir / f'error_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png'
                driver.save_screenshot(str(screenshot_path))
                print(f"📸 截图: {screenshot_path}")
            except:
                pass
        
        # 如果错误次数超过阈值，请求救援
        if self.error_count >= self.max_retries:
            print("🚨 错误次数过多，请求救援...")
            self.send_mission_control_alert(
                error_type=type(error).__name__,
                details={
                    'error_message': str(error),
                    'current_step': context.get('step', 'unknown'),
                    'job_url': context.get('job_url', 'unknown'),
                    'error_count': self.error_count
                },
                screenshot_path=screenshot_path
            )
            return 'RESCUE_REQUESTED'
        
        return 'RETRY'
    
    def reset_error_count(self):
        """重置错误计数"""
        self.error_count = 0

def check_mission_control_messages():
    """检查 Mission Control 是否有回复"""
    notify_file = Path('/tmp/mission-control-notify-main.txt')
    if notify_file.exists():
        try:
            with open(notify_file) as f:
                message = json.load(f)
            notify_file.unlink()  # 删除已读消息
            return message
        except:
            pass
    return None

if __name__ == '__main__':
    # 测试救援系统
    rescue = RescueSystem()
    
    # 模拟进度
    last_progress = rescue.record_progress('login', '登录成功')
    print("✅ 已记录进度: 登录成功")
    
    # 模拟错误
    class MockDriver:
        def save_screenshot(self, path):
            pass
    
    result = rescue.handle_error(
        Exception("Easy Apply button not found"),
        {'step': 'click_easy_apply', 'job_url': 'https://linkedin.com/jobs/view/123'},
        MockDriver()
    )
    
    print(f"\n处理结果: {result}")
