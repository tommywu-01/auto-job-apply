# LinkedIn Easy Apply - 故障救援机制

## 救援系统架构

```
┌─────────────────────────────────────────────────────────┐
│              LinkedIn Easy Apply Bot                    │
│                    (主申请流程)                          │
└──────────────────┬──────────────────────────────────────┘
                   │
                   │ 检测到卡住/错误
                   ▼
┌─────────────────────────────────────────────────────────┐
│              Rescue System                              │
│  • 记录进度                                            │
│  • 截图保存                                            │
│  • 检测卡住 (>5分钟无进展)                             │
│  • 错误计数 (>3次错误)                                 │
└──────────────────┬──────────────────────────────────────┘
                   │
                   │ 写入 /tmp/mission-control-notify-main.txt
                   ▼
┌─────────────────────────────────────────────────────────┐
│              Mission Control                            │
│              (中央通知系统)                              │
└──────────────────┬──────────────────────────────────────┘
                   │
                   │ 消息路由
                   ▼
┌─────────────────────────────────────────────────────────┐
│              Botty (Main)                               │
│  • 接收求救信号                                        │
│  • 分析问题                                            │
│  • 远程修复                                            │
│  • 恢复申请流程                                        │
└─────────────────────────────────────────────────────────┘
```

## 触发救援的条件

1. **卡住检测**: 5分钟内无任何进展
2. **错误超限**: 连续3次错误
3. **未知异常**: 未捕获的异常

## 求救信号格式

```json
{
  "timestamp": "2026-02-08T17:45:00",
  "from": "linkedin-easy-apply-bot",
  "to": "botty",
  "priority": "high",
  "error_type": "STUCK|BUTTON_NOT_FOUND|FORM_ERROR",
  "details": {
    "error_message": "...",
    "current_step": "click_easy_apply",
    "job_url": "https://linkedin.com/jobs/view/123",
    "screenshot": "logs/error_20260208_174500.png"
  },
  "request": "troubleshoot_and_resume"
}
```

## 可用脚本

### 1. 带救援的版本
```bash
python3 linkedin_easy_apply_rescue.py
```

### 2. 普通版本
```bash
python3 linkedin_easy_apply_v4.py
```

### 3. 批量版本
```bash
python3 auto_apply_bot.py
```

## 手动救援指令

如果 Botty 收到救援信号，可以通过 Mission Control 发送指令：

```bash
# 暂停申请
echo '{"instruction": "PAUSE"}' > /tmp/mission-control-notify-main.txt

# 恢复申请
echo '{"instruction": "RESUME"}' > /tmp/mission-control-notify-main.txt

# 跳过当前职位
echo '{"instruction": "SKIP"}' > /tmp/mission-control-notify-main.txt
```

## 日志文件

- `logs/progress.json` - 进度记录
- `logs/applications.json` - 申请历史
- `logs/error_*.png` - 错误截图
- `logs/cron.log` - Cron 运行日志

## 故障排查检查清单

当收到救援信号时：

1. [ ] 查看错误截图 `logs/error_*.png`
2. [ ] 检查当前步骤 `logs/progress.json`
3. [ ] 分析页面结构变化
4. [ ] 更新选择器
5. [ ] 发送恢复指令

## 联系方式

- **Rescue Bot**: `jn7apr58t773gffa140hktc9ds80fvqr` (Port 19789)
- **Botty (Main)**: `jn78tecygdgddznnd4vjvjdw9980f9je` (Port 18789)
- **Mission Control Dashboard**: https://dashboard.convex.dev/d/clean-goat-205
