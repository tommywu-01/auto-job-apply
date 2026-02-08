# GitHub Repository Setup

## 方法 1: 使用 GitHub CLI (推荐)

```bash
cd ~/.openclaw/workspace/auto-job-apply
./setup-github.sh
```

## 方法 2: 使用浏览器

1. 访问: https://github.com/new
2. 填写信息:
   - **Repository name**: `auto-job-apply`
   - **Description**: `AI-Powered Automated Job Application System - Apply to jobs on LinkedIn, Greenhouse, Lever, Workday with zero clicks`
   - **Public** (勾选)
   - **Add a README file** (不要勾选，已有 README)
3. 点击 **Create repository**

4. 然后运行:
```bash
cd ~/.openclaw/workspace/auto-job-apply
git remote add origin https://github.com/tommywu/auto-job-apply.git
git branch -M main
git push -u origin main
```

## 方法 3: 我帮你创建 (需要提供 GH_TOKEN)

如果你给我 GitHub personal access token，我可以直接帮你创建并推送。

获取 token: https://github.com/settings/tokens
需要的权限: `repo`

---

## 快速链接

- [Create New Repository](https://github.com/new)
- [GitHub Token Settings](https://github.com/settings/tokens)
- [GitHub CLI Docs](https://cli.github.com/manual/)
