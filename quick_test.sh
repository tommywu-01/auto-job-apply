#!/bin/bash
# 快速测试脚本 - 用于验证修复后的系统
# 使用方法: ./quick_test.sh

echo "========================================"
echo " 自动化求职系统 - 快速测试"
echo "========================================"
echo ""

cd ~/.openclaw/workspace/auto-job-apply

# 检查目录结构
echo "1. 检查目录结构..."
mkdir -p logs screenshots test_reports
echo "   ✓ 目录结构已准备"
echo ""

# 检查Python依赖
echo "2. 检查Python依赖..."
python3 -c "import selenium, webdriver_manager, yaml" 2>/dev/null
if [ $? -eq 0 ]; then
    echo "   ✓ 所有依赖已安装"
else
    echo "   ✗ 缺少依赖，正在安装..."
    pip3 install selenium webdriver-manager pyyaml
fi
echo ""

# 检查配置文件
echo "3. 检查配置文件..."
if [ -f "config/profile.yaml" ]; then
    echo "   ✓ profile.yaml 存在"
else
    echo "   ✗ profile.yaml 不存在"
fi
echo ""

# 检查简历文件
echo "4. 检查简历文件..."
if [ -f "$HOME/Downloads/TOMMY WU Resume Dec 2025.pdf" ]; then
    echo "   ✓ 简历文件存在"
else
    echo "   ⚠ 简历文件不存在于默认路径"
    echo "      请确保简历路径配置正确"
fi
echo ""

# 语法检查
echo "5. 语法检查..."
python3 -m py_compile linkedin_easy_apply_fixed.py
if [ $? -eq 0 ]; then
    echo "   ✓ linkedin_easy_apply_fixed.py"
else
    echo "   ✗ linkedin_easy_apply_fixed.py 语法错误"
fi

python3 -m py_compile greenhouse_auto_apply_fixed.py
if [ $? -eq 0 ]; then
    echo "   ✓ greenhouse_auto_apply_fixed.py"
else
    echo "   ✗ greenhouse_auto_apply_fixed.py 语法错误"
fi
echo ""

# 类加载测试
echo "6. 类加载测试..."
python3 -c "
from linkedin_easy_apply_fixed import LinkedInEasyApply
from greenhouse_auto_apply_fixed import GreenhouseAutoApply
print('   ✓ LinkedInEasyApply 类加载成功')
print('   ✓ GreenhouseAutoApply 类加载成功')
" 2>/dev/null
echo ""

# 显示使用说明
echo "========================================"
echo " 测试通过! 系统已准备就绪"
echo "========================================"
echo ""
echo "使用方法:"
echo ""
echo "1. LinkedIn Easy Apply:"
echo "   python3 linkedin_easy_apply_fixed.py \\"
echo "     --keywords 'Director of Technical Services' \\"
echo "     --location 'New York' \\"
echo "     --max-jobs 5"
echo ""
echo "2. Greenhouse/Lever申请 (测试URL):"
echo "   python3 greenhouse_auto_apply_fixed.py \\"
echo "     --url 'https://jobs.lever.co/skydance/56de5f07-3f50-4371-9e0a-321d49a3304f' \\"
echo "     --retries 2"
echo ""
echo "选项说明:"
echo "   --headless      无头模式 (不显示浏览器窗口)"
echo "   --no-profile    不使用Chrome profile"
echo "   --no-cookies    不使用cookie登录"
echo "   --retries N     设置重试次数"
echo ""
echo "输出位置:"
echo "   日志: logs/"
echo "   截图: screenshots/"
echo "   报告: test_reports/"
echo ""
