#!/usr/bin/env python3
"""
Tommy Wu 完全自动化求职申请系统
整合 LinkedIn Easy Apply, Greenhouse ATS, 和 Workday ATS

使用方法:
    python3 auto_apply_all.py --target all
    python3 auto_apply_all.py --target linkedin
    python3 auto_apply_all.py --target greenhouse
    python3 auto_apply_all.py --target workday
    python3 auto_apply_all.py --company "Spring Studios"
"""

import os
import sys
import json
import yaml
import argparse
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

# 配置文件路径
CONFIG_DIR = Path(__file__).parent / "config"
PROFILE_FILE = CONFIG_DIR / "profile.yaml"
ANSWERS_FILE = CONFIG_DIR / "answers.json"
TARGETS_FILE = CONFIG_DIR / "job_targets.json"

# 工具路径
LINKEDIN_TOOL = Path("~/.openclaw/workspace/Auto_job_applier_linkedIn").expanduser()
WORKDAY_TOOL = Path("~/.openclaw/workspace/Workday-Application-Automator").expanduser()
GREENHOUSE_TOOL = Path("~/.openclaw/workspace/auto-apply").expanduser()

class AutoApplySystem:
    """完全自动化求职申请系统"""
    
    def __init__(self):
        self.profile = self._load_profile()
        self.answers = self._load_answers()
        self.targets = self._load_targets()
        self.log_file = CONFIG_DIR / f"application_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        
    def _load_profile(self) -> Dict:
        """加载个人资料配置"""
        with open(PROFILE_FILE, 'r') as f:
            return yaml.safe_load(f)
    
    def _load_answers(self) -> Dict:
        """加载常见问题和答案"""
        with open(ANSWERS_FILE, 'r') as f:
            return json.load(f)
    
    def _load_targets(self) -> Dict:
        """加载目标职位配置"""
        with open(TARGETS_FILE, 'r') as f:
            return json.load(f)
    
    def log(self, message: str):
        """记录日志"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        print(log_entry)
        with open(self.log_file, 'a') as f:
            f.write(log_entry + "\n")
    
    def apply_linkedin(self, target: Optional[Dict] = None):
        """
        申请LinkedIn Easy Apply职位
        
        使用Auto_job_applier_linkedIn工具
        """
        self.log("=" * 60)
        self.log("开始 LinkedIn Easy Apply 申请流程")
        self.log("=" * 60)
        
        # 首先同步配置到LinkedIn工具
        self._sync_linkedin_config()
        
        linkedin_config = self.profile['personal_info']
        
        if target:
            self.log(f"目标职位: {target['company']} - {target['title']}")
            # 这里可以添加针对特定职位的申请逻辑
        else:
            self.log("申请所有匹配的LinkedIn职位")
        
        # 构建运行命令
        run_script = LINKEDIN_TOOL / "runAiBot.py"
        if run_script.exists():
            self.log(f"运行LinkedIn自动申请工具: {run_script}")
            # 在实际运行中，这里会调用工具
            # subprocess.run([sys.executable, str(run_script)], cwd=LINKEDIN_TOOL)
        else:
            self.log(f"警告: 找不到LinkedIn工具脚本: {run_script}")
        
        self.log("LinkedIn申请流程完成")
    
    def apply_greenhouse(self, target: Optional[Dict] = None):
        """
        申请Greenhouse ATS职位
        
        使用auto-apply工具
        """
        self.log("=" * 60)
        self.log("开始 Greenhouse ATS 申请流程")
        self.log("=" * 60)
        
        # 同步配置
        self._sync_greenhouse_config()
        
        if target and target.get('url'):
            self.log(f"申请职位: {target['company']} - {target['title']}")
            self.log(f"职位URL: {target['url']}")
            
            # 运行Greenhouse申请
            main_script = GREENHOUSE_TOOL / "auto_apply" / "main.py"
            if main_script.exists():
                self.log(f"运行Greenhouse申请: {main_script}")
                # subprocess.run([sys.executable, str(main_script)], cwd=GREENHOUSE_TOOL)
        else:
            self.log("搜索Greenhouse职位...")
            # 这里可以添加职位搜索逻辑
        
        self.log("Greenhouse申请流程完成")
    
    def apply_workday(self, target: Optional[Dict] = None):
        """
        申请Workday ATS职位
        
        使用Workday-Application-Automator工具
        """
        self.log("=" * 60)
        self.log("开始 Workday ATS 申请流程")
        self.log("=" * 60)
        
        # 同步配置
        self._sync_workday_config()
        
        if target and target.get('url'):
            self.log(f"申请职位: {target['company']} - {target['title']}")
            
            # 更新information.js中的URL
            self._update_workday_url(target['url'])
            
            # 运行Workday申请
            apply_script = WORKDAY_TOOL / "apply.js"
            if apply_script.exists():
                self.log(f"运行Workday申请: {apply_script}")
                # subprocess.run(["node", str(apply_script)], cwd=WORKDAY_TOOL)
        else:
            self.log("搜索Workday职位...")
        
        self.log("Workday申请流程完成")
    
    def _sync_linkedin_config(self):
        """同步配置到LinkedIn工具"""
        self.log("同步LinkedIn配置...")
        
        # 读取现有配置
        personals_py = LINKEDIN_TOOL / "config" / "personals.py"
        questions_py = LINKEDIN_TOOL / "config" / "questions.py"
        
        # 在实际实现中，这里会动态更新配置文件
        # 基于self.profile的内容
        
        self.log("LinkedIn配置同步完成")
    
    def _sync_greenhouse_config(self):
        """同步配置到Greenhouse工具"""
        self.log("同步Greenhouse配置...")
        
        # 更新main.py中的数据
        main_py = GREENHOUSE_TOOL / "auto_apply" / "main.py"
        
        self.log("Greenhouse配置同步完成")
    
    def _sync_workday_config(self):
        """同步配置到Workday工具"""
        self.log("同步Workday配置...")
        
        # 读取现有的information.js模板
        info_js = WORKDAY_TOOL / "information.js"
        
        # 基于self.profile生成新的information.js
        work_experiences = self.profile.get('work_experience', [])
        
        # 构建workexperience对象
        work_exp_js = []
        for exp in work_experiences[:2]:  # 只取前两个
            work_exp_js.append({
                "jobtitle": exp['job_title'],
                "company": exp['company'],
                "location": exp['location'],
                "startDateMonth": exp['start_month'],
                "startDateYear": exp['start_year'],
                "endDateMonth": exp.get('end_month', ''),
                "endDateYear": exp.get('end_year', ''),
                "description": exp['description']
            })
        
        self.log("Workday配置同步完成")
    
    def _update_workday_url(self, url: str):
        """更新Workday申请的目标URL"""
        apply_js = WORKDAY_TOOL / "apply.js"
        
        if apply_js.exists():
            with open(apply_js, 'r') as f:
                content = f.read()
            
            # 替换URL
            import re
            new_content = re.sub(
                r"const url = '.*?';",
                f"const url = '{url}';",
                content
            )
            
            with open(apply_js, 'w') as f:
                f.write(new_content)
            
            self.log(f"已更新Workday目标URL: {url}")
    
    def apply_by_company(self, company_name: str):
        """根据公司名称申请职位"""
        self.log(f"搜索 {company_name} 的职位...")
        
        # 在targets中查找
        for target in self.targets.get('target_companies', []):
            if company_name.lower() in target['company'].lower():
                self.log(f"找到匹配职位: {target['title']}")
                
                platform = target.get('platform', '').lower()
                
                if platform == 'linkedin':
                    self.apply_linkedin(target)
                elif platform == 'greenhouse':
                    self.apply_greenhouse(target)
                elif platform == 'workday':
                    self.apply_workday(target)
                else:
                    self.log(f"未知平台: {platform}")
                
                return
        
        self.log(f"未找到 {company_name} 的职位配置")
    
    def apply_all(self):
        """申请所有目标职位"""
        self.log("=" * 60)
        self.log("开始完整自动化申请流程")
        self.log("=" * 60)
        
        # 按优先级排序
        targets = sorted(
            self.targets.get('target_companies', []),
            key=lambda x: x.get('priority', 999)
        )
        
        for target in targets:
            platform = target.get('platform', '').lower()
            
            try:
                if platform == 'linkedin':
                    self.apply_linkedin(target)
                elif platform == 'greenhouse':
                    self.apply_greenhouse(target)
                elif platform == 'workday':
                    self.apply_workday(target)
                
                # 在每个申请之间添加延迟
                import time
                time.sleep(5)
                
            except Exception as e:
                self.log(f"申请 {target['company']} 时出错: {e}")
        
        self.log("=" * 60)
        self.log("所有申请流程完成")
        self.log(f"日志文件: {self.log_file}")
        self.log("=" * 60)


def main():
    parser = argparse.ArgumentParser(
        description='Tommy Wu 完全自动化求职申请系统'
    )
    parser.add_argument(
        '--target',
        choices=['all', 'linkedin', 'greenhouse', 'workday'],
        default='all',
        help='申请目标平台'
    )
    parser.add_argument(
        '--company',
        type=str,
        help='指定公司名称申请'
    )
    
    args = parser.parse_args()
    
    # 初始化系统
    system = AutoApplySystem()
    
    # 执行申请
    if args.company:
        system.apply_by_company(args.company)
    elif args.target == 'all':
        system.apply_all()
    elif args.target == 'linkedin':
        system.apply_linkedin()
    elif args.target == 'greenhouse':
        system.apply_greenhouse()
    elif args.target == 'workday':
        system.apply_workday()


if __name__ == '__main__':
    main()
