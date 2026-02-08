#!/bin/bash
# Chrome DevTools MCP 辅助调试脚本

echo "🔧 Chrome DevTools MCP 调试工具"
echo "================================"
echo ""

# 启动 Chrome with remote debugging
launch_chrome_debug() {
    echo "启动 Chrome with remote debugging..."
    /Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
        --remote-debugging-port=9222 \
        --user-data-dir=/tmp/chrome-debug-profile \
        "$1" &
    echo "Chrome 已启动，调试端口: 9222"
    echo "访问 http://127.0.0.1:9222 查看可调试页面"
}

# 启动 MCP server
start_mcp_server() {
    echo ""
    echo "启动 Chrome DevTools MCP Server..."
    chrome-devtools-mcp \
        --browserUrl http://127.0.0.1:9222 \
        --viewport 1280x720 \
        --logFile /tmp/chrome-devtools-mcp.log
}

# 测试职位页面
test_job_page() {
    local url=$1
    echo ""
    echo "测试职位页面: $url"
    
    # 打开页面
    launch_chrome_debug "$url"
    
    sleep 3
    
    # 启动 MCP server
    start_mcp_server
}

# 使用说明
show_help() {
    echo "使用方法:"
    echo "  $0 test <url>    - 测试指定职位页面"
    echo "  $0 server        - 只启动 MCP server"
    echo ""
    echo "示例:"
    echo "  $0 test https://jobs.lever.co/scanlinevfx/..."
    echo "  $0 test https://www.linkedin.com/jobs/view/4370163550/"
}

# 主逻辑
case "$1" in
    test)
        if [ -z "$2" ]; then
            echo "错误: 需要提供 URL"
            show_help
            exit 1
        fi
        test_job_page "$2"
        ;;
    server)
        start_mcp_server
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        show_help
        ;;
esac
