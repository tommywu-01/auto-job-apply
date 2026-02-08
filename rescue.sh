#!/bin/bash
# Mission Control 快速救援脚本
# 用法: ./rescue.sh [pause|resume|skip|status]

NOTIFY_FILE="/tmp/mission-control-notify-main.txt"
LOG_DIR="~/.openclaw/workspace/auto-job-apply/logs"

case "$1" in
  pause)
    echo '{"instruction": "PAUSE", "from": "botty", "timestamp": "'$(date -u +%Y-%m-%dT%H:%M:%S)'"}' > "$NOTIFY_FILE"
    echo "⏸️ 已发送暂停指令"
    ;;
  resume)
    echo '{"instruction": "RESUME", "from": "botty", "timestamp": "'$(date -u +%Y-%m-%dT%H:%M:%S)'"}' > "$NOTIFY_FILE"
    echo "▶️ 已发送恢复指令"
    ;;
  skip)
    echo '{"instruction": "SKIP", "from": "botty", "timestamp": "'$(date -u +%Y-%m-%dT%H:%M:%S)'"}' > "$NOTIFY_FILE"
    echo "⏭️ 已发送跳过指令"
    ;;
  status)
    if [ -f "$NOTIFY_FILE" ]; then
      echo "📨 当前消息:"
      cat "$NOTIFY_FILE"
    else
      echo "📭 无待处理消息"
    fi
    
    echo ""
    echo "📊 最近进度:"
    if [ -f "$LOG_DIR/progress.json" ]; then
      tail -5 "$LOG_DIR/progress.json" | python3 -m json.tool 2>/dev/null || tail -5 "$LOG_DIR/progress.json"
    else
      echo "   无进度记录"
    fi
    ;;
  *)
    echo "LinkedIn Easy Apply - Mission Control 救援脚本"
    echo ""
    echo "用法:"
    echo "  ./rescue.sh pause     - 暂停申请流程"
    echo "  ./rescue.sh resume    - 恢复申请流程"
    echo "  ./rescue.sh skip      - 跳过当前职位"
    echo "  ./rescue.sh status    - 查看状态"
    ;;
esac
