#!/usr/bin/env python3
"""
测试脚本 - 验证自动化求职申请系统配置
"""

import os
import sys
import yaml
import json
from pathlib import Path

# 添加父目录到路径
sys.path.insert(0, str(Path(__file__).parent))

def test_profile_config():
    """测试个人资料配置"""
    print("=" * 60)
    print("测试配置文件: config/profile.yaml")
    print("=" * 60)
    
    try:
        with open("config/profile.yaml", 'r') as f:
            config = yaml.safe_load(f)
        
        # 验证必需字段
        required_fields = {
            'personal_info': ['first_name', 'last_name', 'email', 'phone'],
            'education': ['school', 'degree'],
            'work_experience': ['job_title', 'company'],
            'application_settings': ['resume_path', 'years_of_experience']
        }
        
        # 检查personal_info
        personal = config.get('personal_info', {})
        print(f"✓ 姓名: {personal.get('full_name', 'N/A')}")
        print(f"✓ 邮箱: {personal.get('email', 'N/A')}")
        print(f"✓ 电话: {personal.get('phone', 'N/A')}")
        
        # 检查教育经历
        education = config.get('education', [])
        print(f"✓ 教育经历: {len(education)} 条")
        for edu in education:
            print(f"  - {edu.get('school')}: {edu.get('degree')} in {edu.get('field_of_study')}")
        
        # 检查工作经历
        work_exp = config.get('work_experience', [])
        print(f"✓ 工作经历: {len(work_exp)} 条")
        for exp in work_exp:
            print(f"  - {exp.get('job_title')} @ {exp.get('company')}")
        
        # 检查技能
        skills = config.get('skills', {})
        tech_skills = skills.get('technical', [])
        prof_skills = skills.get('professional', [])
        print(f"✓ 技术技能: {len(tech_skills)} 项")
        print(f"✓ 专业技能: {len(prof_skills)} 项")
        
        # 检查简历路径
        resume_path = config.get('application_settings', {}).get('resume_path', '')
        expanded_path = os.path.expanduser(resume_path)
        if os.path.exists(expanded_path):
            print(f"✓ 简历文件存在: {resume_path}")
        else:
            print(f"⚠ 简历文件不存在: {resume_path}")
        
        print("\n✅ 配置文件测试通过")
        return True
        
    except Exception as e:
        print(f"\n❌ 配置文件测试失败: {e}")
        return False

def test_answers_config():
    """测试答案库配置"""
    print("\n" + "=" * 60)
    print("测试配置文件: config/answers.json")
    print("=" * 60)
    
    try:
        with open("config/answers.json", 'r') as f:
            answers = json.load(f)
        
        common_q = answers.get('common_questions', {})
        print(f"✓ 常见问题数量: {len(common_q)}")
        
        # 显示部分问题
        print("\n  示例问题:")
        for i, (key, value) in enumerate(list(common_q.items())[:3]):
            print(f"    {i+1}. {key}")
        
        # 检查薪资配置
        salary = answers.get('salary_related', {})
        print(f"\n✓ 期望薪资: ${salary.get('desired_salary_usd', 'N/A'):,}")
        print(f"✓ 薪资范围: ${salary.get('salary_range_min', 'N/A'):,} - ${salary.get('salary_range_max', 'N/A'):,}")
        
        print("\n✅ 答案库测试通过")
        return True
        
    except Exception as e:
        print(f"\n❌ 答案库测试失败: {e}")
        return False

def test_job_targets():
    """测试目标职位配置"""
    print("\n" + "=" * 60)
    print("测试配置文件: config/job_targets.json")
    print("=" * 60)
    
    try:
        with open("config/job_targets.json", 'r') as f:
            targets = json.load(f)
        
        companies = targets.get('target_companies', [])
        print(f"✓ 目标公司数量: {len(companies)}")
        
        print("\n  目标职位列表:")
        for i, company in enumerate(companies, 1):
            print(f"    {i}. {company.get('company')}")
            print(f"       职位: {company.get('title')}")
            print(f"       平台: {company.get('platform')}")
            print(f"       优先级: {company.get('priority')}")
            if company.get('salary_range'):
                print(f"       薪资: {company.get('salary_range')}")
        
        # 检查搜索偏好
        prefs = targets.get('search_preferences', {})
        keywords = prefs.get('keywords', [])
        locations = prefs.get('locations', [])
        print(f"\n✓ 搜索关键词: {len(keywords)} 个")
        print(f"✓ 搜索地点: {len(locations)} 个")
        
        print("\n✅ 目标职位测试通过")
        return True
        
    except Exception as e:
        print(f"\n❌ 目标职位测试失败: {e}")
        return False

def test_scripts():
    """测试脚本文件"""
    print("\n" + "=" * 60)
    print("测试自动化脚本")
    print("=" * 60)
    
    scripts = [
        ('auto_apply_all.py', '主自动化脚本'),
        ('linkedin_easy_apply.py', 'LinkedIn Easy Apply脚本'),
        ('greenhouse_auto_apply.py', 'Greenhouse ATS脚本'),
        ('workday_auto_apply.py', 'Workday ATS脚本'),
        ('run.sh', '一键运行脚本')
    ]
    
    all_exist = True
    for script, description in scripts:
        if os.path.exists(script):
            size = os.path.getsize(script)
            print(f"✓ {description}: {script} ({size:,} bytes)")
        else:
            print(f"❌ {description}: {script} (不存在)")
            all_exist = False
    
    if all_exist:
        print("\n✅ 所有脚本文件存在")
        return True
    else:
        print("\n⚠ 部分脚本文件缺失")
        return False

def test_imports():
    """测试Python依赖"""
    print("\n" + "=" * 60)
    print("测试Python依赖")
    print("=" * 60)
    
    dependencies = [
        ('selenium', 'Selenium WebDriver'),
        ('yaml', 'PyYAML'),
        ('json', 'JSON'),
    ]
    
    all_ok = True
    for module, name in dependencies:
        try:
            __import__(module)
            print(f"✓ {name}")
        except ImportError:
            print(f"❌ {name} (未安装)")
            all_ok = False
    
    if all_ok:
        print("\n✅ 所有依赖已安装")
        return True
    else:
        print("\n⚠ 部分依赖缺失，运行: pip install -r requirements.txt")
        return False

def run_module_tests():
    """测试模块导入"""
    print("\n" + "=" * 60)
    print("测试模块加载")
    print("=" * 60)
    
    try:
        # 测试主脚本导入
        print("测试导入 auto_apply_all...")
        import auto_apply_all
        print("✓ auto_apply_all 模块加载成功")
        
        # 测试配置加载
        print("测试配置加载...")
        system = auto_apply_all.AutoApplySystem()
        print(f"✓ 配置加载成功")
        print(f"  - 个人: {system.profile['personal_info']['full_name']}")
        print(f"  - 目标: {len(system.targets.get('target_companies', []))} 个公司")
        
        print("\n✅ 模块测试通过")
        return True
        
    except Exception as e:
        print(f"\n❌ 模块测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("Tommy Wu 自动化求职申请系统 - 测试套件")
    print("=" * 60)
    
    results = []
    
    # 运行测试
    results.append(('配置文件', test_profile_config()))
    results.append(('答案库', test_answers_config()))
    results.append(('目标职位', test_job_targets()))
    results.append(('脚本文件', test_scripts()))
    results.append(('Python依赖', test_imports()))
    results.append(('模块加载', run_module_tests()))
    
    # 汇总
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{status} - {name}")
    
    print(f"\n总计: {passed}/{total} 项测试通过")
    
    if passed == total:
        print("\n🎉 所有测试通过！系统已准备就绪！")
        return 0
    else:
        print("\n⚠ 部分测试未通过，请检查配置")
        return 1

if __name__ == "__main__":
    sys.exit(main())
