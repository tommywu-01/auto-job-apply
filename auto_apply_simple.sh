#!/bin/bash
# LinkedIn Easy Apply - 简化版自动申请脚本
# 每小时运行一次，申请指定职位

cd ~/.openclaw/workspace/auto-job-apply

# 创建日志目录
mkdir -p logs

# 记录开始时间
echo "========================================" | tee -a logs/cron.log
echo "🚀 自动申请启动: $(date)" | tee -a logs/cron.log
echo "========================================" | tee -a logs/cron.log

# 职位列表（可以扩展）
JOBS=(
    "https://www.linkedin.com/jobs/view/4361442478"  # US Tech Solutions - Creative Director
)

# 申请计数
APPLIED=0
MAX_APPLY=3

for JOB_URL in "${JOBS[@]}"; do
    if [ $APPLIED -ge $MAX_APPLY ]; then
        echo "已达到最大申请数量 ($MAX_APPLY)" | tee -a logs/cron.log
        break
    fi
    
    echo "" | tee -a logs/cron.log
    echo "📝 申请职位: $JOB_URL" | tee -a logs/cron.log
    
    # 运行申请脚本
    python3 linkedin_easy_apply_v4.py 2>&1 | tee -a logs/apply_$(date +%Y%m%d_%H%M%S).log
    
    if [ $? -eq 0 ]; then
        echo "✅ 申请成功" | tee -a logs/cron.log
        APPLIED=$((APPLIED + 1))
    else
        echo "❌ 申请失败" | tee -a logs/cron.log
    fi
    
    # 等待避免被封
    echo "⏳ 等待 30 秒..." | tee -a logs/cron.log
    sleep 30
done

echo "" | tee -a logs/cron.log
echo "========================================" | tee -a logs/cron.log
echo "✅ 本次共申请 $APPLIED 个职位" | tee -a logs/cron.log
echo "结束时间: $(date)" | tee -a logs/cron.log
echo "========================================" | tee -a logs/cron.log
