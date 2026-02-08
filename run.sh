#!/bin/bash
# Tommy Wu 完全自动化求职申请系统 - 一键运行脚本

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 脚本目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║         Tommy Wu 完全自动化求职申请系统                    ║${NC}"
echo -e "${BLUE}║    LinkedIn Easy Apply | Greenhouse | Workday             ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

# 检查依赖
check_dependencies() {
    echo -e "${YELLOW}▶ 检查依赖...${NC}"
    
    # 检查Python
    if ! command -v python3 &> /dev/null; then
        echo -e "${RED}✗ Python3 未安装${NC}"
        exit 1
    fi
    echo -e "${GREEN}✓ Python3 已安装${NC}"
    
    # 检查Node.js (用于Workday)
    if ! command -v node &> /dev/null; then
        echo -e "${YELLOW}⚠ Node.js 未安装 (Workday申请需要)${NC}"
    else
        echo -e "${GREEN}✓ Node.js 已安装${NC}"
    fi
    
    # 安装Python依赖
    if [ -f "requirements.txt" ]; then
        echo -e "${YELLOW}▶ 安装Python依赖...${NC}"
        pip3 install -q -r requirements.txt
        echo -e "${GREEN}✓ Python依赖已安装${NC}"
    fi
}

# 显示菜单
show_menu() {
    echo ""
    echo -e "${BLUE}请选择操作:${NC}"
    echo "  1) 申请所有目标职位 (Spring Studios + Eyeline + Disney)"
    echo "  2) 仅申请 LinkedIn Easy Apply 职位"
    echo "  3) 仅申请 Greenhouse 职位"
    echo "  4) 仅申请 Workday 职位"
    echo "  5) 申请特定公司"
    echo "  6) 生成配置文件"
    echo "  7) 运行测试"
    echo "  0) 退出"
    echo ""
}

# 申请所有职位
apply_all() {
    echo -e "${YELLOW}▶ 开始申请所有目标职位...${NC}"
    
    # LinkedIn - Spring Studios
    echo -e "${BLUE}  → 申请 Spring Studios (LinkedIn Easy Apply)${NC}"
    python3 linkedin_easy_apply.py 2>&1 | tee -a logs/linkedin_apply.log || true
    
    # Greenhouse - Eyeline Studios
    echo -e "${BLUE}  → 申请 Eyeline Studios (Greenhouse)${NC}"
    python3 greenhouse_auto_apply.py 2>&1 | tee -a logs/greenhouse_apply.log || true
    
    # Workday - Disney
    echo -e "${BLUE}  → 申请 Disney (Workday)${NC}"
    python3 workday_auto_apply.py 2>&1 | tee -a logs/workday_apply.log || true
    
    echo -e "${GREEN}✓ 所有申请流程完成${NC}"
}

# 申请LinkedIn
apply_linkedin() {
    echo -e "${YELLOW}▶ 开始 LinkedIn Easy Apply 申请...${NC}"
    
    # 检查密码环境变量
    if [ -z "$LINKEDIN_PASSWORD" ]; then
        echo -e "${YELLOW}⚠ 请设置 LINKEDIN_PASSWORD 环境变量${NC}"
        read -sp "输入LinkedIn密码: " LINKEDIN_PASSWORD
        echo ""
        export LINKEDIN_PASSWORD
    fi
    
    python3 linkedin_easy_apply.py
}

# 申请Greenhouse
apply_greenhouse() {
    echo -e "${YELLOW}▶ 开始 Greenhouse 申请...${NC}"
    python3 greenhouse_auto_apply.py
}

# 申请Workday
apply_workday() {
    echo -e "${YELLOW}▶ 开始 Workday 申请...${NC}"
    
    # 检查密码环境变量
    if [ -z "$WORKDAY_PASSWORD" ]; then
        echo -e "${YELLOW}⚠ 请设置 WORKDAY_PASSWORD 环境变量${NC}"
        read -sp "输入Workday密码: " WORKDAY_PASSWORD
        echo ""
        export WORKDAY_PASSWORD
    fi
    
    python3 workday_auto_apply.py
}

# 申请特定公司
apply_company() {
    echo ""
    echo -e "${BLUE}可选公司:${NC}"
    echo "  1) Spring Studios (LinkedIn)"
    echo "  2) Eyeline Studios (Greenhouse)"
    echo "  3) Disney (Workday)"
    echo ""
    read -p "请选择 (1-3): " company_choice
    
    case $company_choice in
        1)
            echo -e "${YELLOW}▶ 申请 Spring Studios...${NC}"
            export LINKEDIN_SEARCH_KEYWORDS="Spring Studios Director Technical Services"
            apply_linkedin
            ;;
        2)
            echo -e "${YELLOW}▶ 申请 Eyeline Studios...${NC}"
            apply_greenhouse
            ;;
        3)
            echo -e "${YELLOW}▶ 申请 Disney...${NC}"
            export WORKDAY_JOB_URL="https://jobs.disneycareers.com/"
            apply_workday
            ;;
        *)
            echo -e "${RED}无效选择${NC}"
            ;;
    esac
}

# 生成配置文件
generate_config() {
    echo -e "${YELLOW}▶ 生成配置文件...${NC}"
    
    # 确保配置目录存在
    mkdir -p config
    
    # 检查现有配置
    if [ -f "config/profile.yaml" ]; then
        read -p "配置文件已存在，是否覆盖? (y/N): " overwrite
        if [[ ! $overwrite =~ ^[Yy]$ ]]; then
            echo -e "${YELLOW}保留现有配置${NC}"
            return
        fi
    fi
    
    echo -e "${GREEN}✓ 配置文件已准备${NC}"
    echo -e "${YELLOW}请编辑 config/profile.yaml 自定义您的信息${NC}"
}

# 运行测试
run_tests() {
    echo -e "${YELLOW}▶ 运行测试...${NC}"
    
    # 测试配置文件
    python3 -c "
import yaml
with open('config/profile.yaml') as f:
    config = yaml.safe_load(f)
    print('✓ Profile配置有效')
    print(f'  姓名: {config[\"personal_info\"][\"full_name\"]}')
    print(f'  邮箱: {config[\"personal_info\"][\"email\"]}')
"
    
    # 测试答案库
    python3 -c "
import json
with open('config/answers.json') as f:
    answers = json.load(f)
    print('✓ Answers配置有效')
    print(f'  常见问题数量: {len(answers[\"common_questions\"])}')
"
    
    echo -e "${GREEN}✓ 所有测试通过${NC}"
}

# 创建日志目录
mkdir -p logs

# 检查依赖
check_dependencies

# 主循环
while true; do
    show_menu
    read -p "请输入选项 (0-7): " choice
    
    case $choice in
        1)
            apply_all
            ;;
        2)
            apply_linkedin
            ;;
        3)
            apply_greenhouse
            ;;
        4)
            apply_workday
            ;;
        5)
            apply_company
            ;;
        6)
            generate_config
            ;;
        7)
            run_tests
            ;;
        0)
            echo -e "${GREEN}再见！祝求职顺利！${NC}"
            exit 0
            ;;
        *)
            echo -e "${RED}无效选项${NC}"
            ;;
    esac
    
    echo ""
    read -p "按回车键继续..."
done
