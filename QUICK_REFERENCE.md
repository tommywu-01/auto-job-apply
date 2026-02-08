# 🚀 快速参考卡片

## 一键启动
```bash
cd ~/.openclaw/workspace/auto-job-apply
./run.sh
```

## 环境变量设置
```bash
export LINKEDIN_PASSWORD="your_password"
export WORKDAY_PASSWORD="your_password"
```

## 常用命令

### 申请所有职位
```bash
python3 auto_apply_all.py --target all
```

### 申请特定平台
```bash
python3 auto_apply_all.py --target linkedin
python3 auto_apply_all.py --target greenhouse
python3 auto_apply_all.py --target workday
```

### 申请特定公司
```bash
python3 auto_apply_all.py --company "Spring Studios"
```

### 测试系统
```bash
python3 test_system.py
```

## 配置文件位置

| 文件 | 用途 |
|------|------|
| `config/profile.yaml` | 个人信息、工作经历、教育背景 |
| `config/answers.json` | 常见问题和答案 |
| `config/job_targets.json` | 目标职位列表 |

## 日志文件位置

| 文件 | 内容 |
|------|------|
| `logs/linkedin_apply.log` | LinkedIn申请日志 |
| `logs/greenhouse_apply.log` | Greenhouse申请日志 |
| `logs/workday_apply.log` | Workday申请日志 |

## 目标职位

| # | 公司 | 职位 | 平台 | 薪资 |
|---|------|------|------|------|
| 1 | Spring Studios | Director of Technical Services | LinkedIn | $120-150K |
| 2 | Eyeline Studios | Stage Operator | Greenhouse | - |
| 3 | Disney | Sr Manager Technical Events | Workday | - |

## 简历路径
```
~/Downloads/TOMMY WU Resume Dec 2025.pdf
```

## 联系方式
- 邮箱: tommy.wu@nyu.edu
- 电话: 917-742-4303
- LinkedIn: https://www.linkedin.com/in/tommywu/

---

**配置完成时间**: 2026-02-08  
**系统状态**: ✅ 已就绪，等待执行
