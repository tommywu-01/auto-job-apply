# Tommy Wu 完全自动化求职申请系统

## 📋 项目概述

本系统整合了三个主流ATS（申请跟踪系统）平台，实现**零点击自动申请**：

| 平台 | 工具 | 状态 |
|------|------|------|
| **LinkedIn Easy Apply** | Auto_job_applier_linkedIn | ✅ 已配置 |
| **Greenhouse ATS** | auto-apply | ✅ 已配置 |
| **Workday ATS** | Workday-Application-Automator | ✅ 已配置 |

---

## 🎯 目标职位

### 优先级 1: Spring Studios
- **职位**: Director of Technical Services
- **薪资**: $120,000 - $150,000
- **地点**: New York, NY
- **平台**: LinkedIn Easy Apply
- **状态**: 待执行

### 优先级 2: Eyeline Studios
- **职位**: Stage Operator (Virtual Production)
- **平台**: Greenhouse ATS
- **状态**: 待执行

### 优先级 3: Disney
- **职位**: Sr Manager, Technical Events Production
- **平台**: Workday ATS
- **状态**: 待执行

---

## 📁 文件结构

```
~/.openclaw/workspace/auto-job-apply/
├── README.md                      # 项目说明
├── requirements.txt               # Python依赖
├── run.sh                         # 一键运行脚本 ⭐
├── test_system.py                 # 系统测试
│
├── config/                        # 配置文件目录
│   ├── profile.yaml              # 个人信息主配置
│   ├── answers.json              # 常见问题和答案库
│   └── job_targets.json          # 目标职位列表
│
├── auto_apply_all.py             # 主自动化脚本
├── linkedin_easy_apply.py        # LinkedIn Easy Apply自动化
├── greenhouse_auto_apply.py      # Greenhouse ATS自动化
└── workday_auto_apply.py         # Workday ATS自动化
```

---

## 🚀 快速开始

### 1. 环境准备

```bash
# 进入项目目录
cd ~/.openclaw/workspace/auto-job-apply

# 安装依赖
pip3 install -r requirements.txt --user

# 或者使用一键脚本
./run.sh
```

### 2. 设置环境变量（必需）

```bash
# LinkedIn 密码
export LINKEDIN_PASSWORD="your_linkedin_password"

# Workday 密码 (Disney等)
export WORKDAY_PASSWORD="your_workday_password"
```

### 3. 运行自动化申请

```bash
# 方法一: 使用一键脚本（推荐）
./run.sh

# 方法二: 直接运行Python脚本
# 申请所有目标职位
python3 auto_apply_all.py --target all

# 仅申请LinkedIn职位
python3 auto_apply_all.py --target linkedin

# 仅申请Greenhouse职位
python3 auto_apply_all.py --target greenhouse

# 仅申请Workday职位
python3 auto_apply_all.py --target workday

# 申请特定公司
python3 auto_apply_all.py --company "Spring Studios"
```

---

## ⚙️ 配置说明

### 个人信息配置 (config/profile.yaml)

已配置的个人信息包括：

- ✅ 基本信息：姓名、邮箱、电话
- ✅ 地址：Brooklyn Navy Yard
- ✅ 教育：NYU Tandon (M.S.) + NYU Tisch (B.F.A.)
- ✅ 工作经历：4段完整经历
  - Director of Creative Technology @ Madwell
  - Co-Founder & CCO @ WLab
  - Assistant Director @ Shanghai Media Group
  - Freelance Creative Producer
- ✅ 技能：12项技术技能 + 8项专业技能
- ✅ 简历路径：~/Downloads/TOMMY WU Resume Dec 2025.pdf

### 常见问答库 (config/answers.json)

已配置20个常见申请问题及答案：

1. Why are you interested in this position?
2. Describe your relevant experience
3. Leadership experience
4. Technical skills
5. Visa sponsorship requirements
6. Salary expectations
7. Availability and notice period
8. And more...

### 目标职位 (config/job_targets.json)

已配置3个优先目标职位，按优先级排序。

---

## 🔄 申请流程

### LinkedIn Easy Apply 流程 (3-5步)

1. **Contact Info** - 自动填写联系方式
2. **Resume** - 自动上传简历
3. **Additional Questions** - 自动回答自定义问题
4. **Work Authorization** - 自动填写工作授权
5. **Review & Submit** - 自动提交

### Greenhouse 流程

1. **Basic Info** - 姓名、邮箱、电话
2. **Resume/CV** - 简历上传
3. **Cover Letter** - 求职信（可选）
4. **Custom Questions** - 自定义问题
5. **Demographic Info** - 多元化信息（可选）
6. **Submit** - 提交

### Workday 流程

1. **Sign In** - 登录/创建账户
2. **Contact Information** - 联系信息
3. **My Experience** - 工作经历和教育
4. **Voluntary Disclosures** - 自愿披露信息
5. **Self Identification** - 自我识别
6. **Review & Submit** - 审核并提交

---

## 🛠️ 技术细节

### 使用的技术栈

- **Python 3.9+** - 主要编程语言
- **Selenium** - 浏览器自动化
- **Puppeteer** - Workday自动化（Node.js）
- **YAML/JSON** - 配置文件
- **Chrome WebDriver** - 浏览器驱动

### 自动化特点

- ✅ 处理多步弹窗（LinkedIn Easy Apply）
- ✅ 自动填写所有表单字段
- ✅ 智能匹配问题和答案
- ✅ 自动上传简历
- ✅ 自动提交申请
- ✅ 详细的日志记录
- ✅ 错误处理和恢复

---

## 📝 测试结果

```
✅ 配置文件        - 通过
✅ 答案库          - 通过
✅ 目标职位        - 通过
✅ 脚本文件        - 通过
✅ Python依赖      - 通过
✅ 模块加载        - 通过

总计: 6/6 项测试通过
```

---

## 🔒 安全说明

- 密码通过环境变量管理，**不会**硬编码在代码中
- 简历路径使用绝对路径并验证文件存在性
- 所有个人信息存储在本地配置文件中
- 不收集或传输任何个人数据到外部服务器

---

## 📊 下一步行动

1. **立即执行**
   ```bash
   # 设置密码
   export LINKEDIN_PASSWORD="your_password"
   
   # 运行申请
   ./run.sh
   # 选择选项 1) 申请所有目标职位
   ```

2. **监控申请状态**
   - 查看日志文件：`logs/` 目录
   - LinkedIn申请状态：linkedin_apply.log
   - Greenhouse申请状态：greenhouse_apply.log
   - Workday申请状态：workday_apply.log

3. **跟进**
   - 检查邮箱（tommy.wu@nyu.edu）
   - 更新LinkedIn状态
   - 准备面试

---

## 🎓 Tommy Wu 简历亮点

### 教育背景
- **M.S. Integrated Design & Media** - NYU Tandon, 2025
- **B.F.A. Photography** - NYU Tisch, 2023

### 核心技能
- Unreal Engine, Virtual Production, LED Walls
- TouchDesigner, LiDAR, Motion Capture
- Python, C++, Real-Time Rendering

### 代表项目
- Mercedes-Benz, Sony Music, e.l.f. Cosmetics (19.9M views)
- NASA microgravity motion capture
- Visible "Truth About Yadas" (1.5B+ impressions, Webby winner)

### 工作经历
- **Director of Creative Technology** @ Madwell (2024-2025)
- **Co-Founder & CCO** @ WLab (2023-2024, 被收购)
- **Assistant Director** @ Shanghai Media Group (2018-2021)

---

## 📞 支持与联系

如有问题，请检查：
1. 环境变量是否正确设置
2. 配置文件是否完整
3. 简历文件路径是否正确
4. 网络连接是否正常

---

**祝求职顺利！🎉**
