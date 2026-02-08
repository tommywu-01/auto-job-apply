#!/usr/bin/env python3
"""
Mission Control 双重通知系统 v2.0
出错时同时通知 Botty 和 Rescue Bot
"""

import os
import json
import time
from datetime import datetime
from pathlib import Path

# Agent IDs
AGENTS = {
    'botty': 'jn78tecygdgddznnd4vjvjdw9980f9je',  # Main
    'rescue_bot': 'jn7apr58t773gffa140hktc9ds80fvqr',  # Rescue
}

# 通知文件路径
NOTIFY_FILES = {
    'botty': '/tmp/mission-control-notify-main.txt',
    'rescue_bot': '/tmp/mission-control-notify-rescue.txt',
}

class DualNotifySystem:
    """双重通知系统 - 同时通知 Botty 和 Rescue Bot"""
    
    def __init__(self):
        self.log_dir = Path('logs')
        self.log_dir.mkdir(exist_ok=True)
    
    def send_alert(self, alert_type, details, priority='high'):
        """
        发送双重警报
        同时通知 Botty 和 Rescue Bot
        """
        timestamp = datetime.now().isoformat()
        
        # 构建警报消息
        alert = {
            'timestamp': timestamp,
            'from': 'linkedin-easy-apply-bot',
            'alert_type': alert_type,
            'priority': priority,
            'details': details,
            'request': 'troubleshoot_and_resume',
            'escalation_count': details.get('retry_count', 0)
        }
        
        # 1. 通知 Botty (Main)
        self._notify_agent('botty', alert)
        
        # 2. 通知 Rescue Bot (Backup)
        if priority in ['high', 'urgent']:
            rescue_alert = alert.copy()
            rescue_alert['check_botty_status'] = True  # 让 RB 检查 Botty 是否活着
            rescue_alert['takeover_if_needed'] = True  # 必要时接管
            self._notify_agent('rescue_bot', rescue_alert)
        
        print(f"🚨 双重警报已发送: {alert_type}")
        print(f"   Botty: {NOTIFY_FILES['botty']}")
        print(f"   Rescue Bot: {NOTIFY_FILES['rescue_bot']}")
        
        # 记录到日志
        self._log_alert(alert)
        
        return True
    
    def _notify_agent(self, agent_name, alert):
        """通知指定 Agent"""
        notify_file = Path(NOTIFY_FILES[agent_name])
        try:
            # 读取现有消息（如果有）
            existing = []
            if notify_file.exists():
                try:
                    with open(notify_file) as f:
                        content = f.read().strip()
                        if content:
                            existing = json.loads(content)
                            if not isinstance(existing, list):
                                existing = [existing]
                except:
                    existing = []
            
            # 添加新消息
            existing.append(alert)
            
            # 只保留最近5条
            existing = existing[-5:]
            
            # 写入文件
            with open(notify_file, 'w') as f:
                json.dump(existing, f, indent=2)
            
            return True
        except Exception as e:
            print(f"   ⚠️ 通知 {agent_name} 失败: {e}")
            return False
    
    def _log_alert(self, alert):
        """记录警报到日志"""
        log_file = self.log_dir / 'alerts.json'
        
        alerts = []
        if log_file.exists():
            try:
                with open(log_file) as f:
                    alerts = json.load(f)
            except:
                pass
        
        alerts.append(alert)
        
        # 只保留最近100条
        alerts = alerts[-100:]
        
        with open(log_file, 'w') as f:
            json.dump(alerts, f, indent=2)
    
    def notify_error(self, error_message, context, screenshot=None):
        """通知错误"""
        return self.send_alert('ERROR', {
            'error_message': error_message,
            'current_step': context.get('step', 'unknown'),
            'job_url': context.get('job_url', 'unknown'),
            'retry_count': context.get('retry_count', 0),
            'screenshot': str(screenshot) if screenshot else None
        }, priority='high')
    
    def notify_stuck(self, last_step, duration, context):
        """通知卡住"""
        return self.send_alert('STUCK', {
            'last_step': last_step,
            'stuck_duration': f"{duration} seconds",
            'job_url': context.get('job_url', 'unknown'),
            'retry_count': context.get('retry_count', 0)
        }, priority='urgent')
    
    def notify_success(self, job):
        """通知成功（仅 Botty）"""
        alert = {
            'timestamp': datetime.now().isoformat(),
            'from': 'linkedin-easy-apply-bot',
            'alert_type': 'SUCCESS',
            'priority': 'normal',
            'details': {
                'job_title': job.get('title'),
                'company': job.get('company'),
                'url': job.get('url')
            }
        }
        self._notify_agent('botty', alert)
        print(f"✅ 成功通知已发送: {job.get('company')} - {job.get('title')}")

def check_mission_control_messages(agent='botty'):
    """检查 Mission Control 是否有消息"""
    notify_file = Path(NOTIFY_FILES.get(agent, NOTIFY_FILES['botty']))
    if notify_file.exists():
        try:
            with open(notify_file) as f:
                content = f.read().strip()
                if content:
                    messages = json.loads(content)
                    # 清空文件
                    notify_file.unlink()
                    return messages if isinstance(messages, list) else [messages]
        except:
            pass
    return None

if __name__ == '__main__':
    # 测试双重通知
    notify = DualNotifySystem()
    
    print("测试双重通知系统...\n")
    
    # 测试错误通知
    notify.notify_error(
        "Easy Apply button not found",
        {'step': 'click_easy_apply', 'job_url': 'https://linkedin.com/jobs/123', 'retry_count': 3}
    )
    
    print("\n测试完成！")
    print(f"检查文件:\n  {NOTIFY_FILES['botty']}\n  {NOTIFY_FILES['rescue_bot']}")
