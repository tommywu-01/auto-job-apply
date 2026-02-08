#!/bin/bash
# GitHub Repo Setup Script

echo "🔧 GitHub Repo Setup for Auto Job Apply"
echo "========================================"
echo ""

# Check if gh is installed
if ! command -v gh &> /dev/null; then
    echo "Installing GitHub CLI..."
    brew install gh
fi

# Login to GitHub
echo "1. 登录 GitHub..."
gh auth login

# Create repo
echo ""
echo "2. 创建 GitHub repo..."
gh repo create auto-job-apply \
    --public \
    --description "AI-Powered Automated Job Application System" \
    --source=. \
    --remote=origin \
    --push

echo ""
echo "✅ Repo 创建完成！"
echo "URL: https://github.com/tommywu/auto-job-apply"
