# QUICK-001 为 req:issue 添加 issue-guide skill

## 元信息

| 字段 | 值 |
|-----|-----|
| 编号 | QUICK-001 |
| 改动类型 | 小功能 |
| 端类型 | 全栈 |
| 状态 | 已完成 |
| 模块 | 快速修复 |
| 优先级 | P2 |
| 创建时间 | 2026-05-15 |
| 负责人 | haiqing |
| 关联需求 | - |
| branch | feat/QUICK-001-issue-guide-skill |
| issue | - |
| completedAt | 2026-05-19 |

## 生命周期

- [x] 草稿
- [x] 方案确认
- [x] 开发中
- [x] 已完成

---

## 问题描述

### 现象
`req:issue` 命令没有对应的 skill，Codex 在执行 issue 操作时缺乏关键约束引导，容易在以下场景出错：
- JSON 安全：用字符串拼接构造请求体，含引号/换行时出错
- Gitea labels 限制：误用 PATCH body 修改标签（Gitea 必须走独立端点）
- 标签匹配：硬编码中英文对照表而非从仓库动态拉取

### 期望
添加 `issue-guide` skill，为 Codex 提供平台差异、安全约束和操作规范的引导。

---

## 实现方案

### 问题分析
`req:issue` 命令文件（`issue.md`）已有完整的子命令路由和格式描述，但 skill 层缺失，Codex 执行时无法自动注入关键约束。

### 解决方案
新增 `plugins/req/skills/issue-guide/SKILL.md`，内容覆盖：
- 平台检测与配置读取（repoType / giteaUrl / giteaToken）
- CLI 优先级（GitHub → gh，Gitea → tea → curl 回退）
- JSON 安全约束（禁止字符串拼接，必须用 python3/jq 转义）
- Gitea labels 独立端点限制
- 标签匹配策略（动态拉取，三级匹配）
- 关联需求上下文注入
- 与其他命令的分工（new/fix/done）

### 涉及文件

| 文件 | 改动类型 | 说明 |
|-----|---------|------|
| plugins/req/skills/issue-guide/SKILL.md | 新增 | issue 操作引导 skill |

### 改动量
- 预估：小
- 涉及文件：1 个
- 代码行数：约 80 行

---

## 验证方式

- [x] SKILL.md frontmatter 格式正确（name / description）
- [x] 覆盖 JSON 安全、Gitea labels、标签匹配三个关键约束
- [x] plugin.json 通过目录级注册，无需修改配置

---

## 开发记录

### 2026-05-15
- 创建快速需求 QUICK-001
- 新增 plugins/req/skills/issue-guide/SKILL.md，方案已确认并完成
