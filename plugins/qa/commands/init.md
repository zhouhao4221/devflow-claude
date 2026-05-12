---
description: 初始化 QA 插件 - 创建目录结构并安装 skill 到项目
argument-hint: ""
allowed-tools: Read, Write, Edit, Glob, Bash(mkdir:*, cp:*, ls:*, grep:*)
model: claude-haiku-4-5-20251001
---

# 初始化 QA 插件

将 qa-executor skill 安装到项目的 `.claude/skills/`，使 Codex 和 Claude 桌面端能在执行测试时自动加载。

## 命令格式

```
/qa:init
```

---

## 执行流程

### 1. 创建目录结构

```bash
mkdir -p docs/qa/flows
mkdir -p docs/qa/reports
mkdir -p docs/qa/screenshots
mkdir -p .claude/skills/qa-executor
```

### 2. 生成 testid 命名约定文档

将约定模板复制到项目：

```bash
cp plugins/qa/templates/testid-convention.md docs/qa/testid-convention.md
```

此文件提交到 git，供前端开发参考添加 `data-testid` 属性。

### 3. 安装 qa-executor skill

将插件源文件复制到项目 skills 目录：

```bash
cp plugins/qa/skills/qa-executor/SKILL.md .claude/skills/qa-executor/SKILL.md
```

若插件路径不存在（说明插件未通过 Claude Code 安装），输出：

```
❌ 未找到 qa 插件源文件
💡 请先通过 devflow 安装 qa 插件后重试
```

### 4. 更新 .gitignore

检查项目根目录的 `.gitignore`：

- 若已包含 `docs/qa/reports/` → 跳过
- 否则追加：

```
# QA test artifacts
docs/qa/reports/
docs/qa/screenshots/
```

### 5. 输出结果

```
✅ QA 插件初始化完成

已创建目录：
  docs/qa/flows/          测试流程文档
  docs/qa/reports/        测试报告（已加入 .gitignore）
  docs/qa/screenshots/    截图存储（已加入 .gitignore）

已安装 skill：
  .claude/skills/qa-executor/SKILL.md

已生成约定文档：
  docs/qa/testid-convention.md    data-testid 命名约定（提交 git，供前端参考）

💡 Codex / Claude 桌面端现在可以使用 /qa:run 执行测试
💡 使用 /qa:new 创建第一个测试流程文档
```
