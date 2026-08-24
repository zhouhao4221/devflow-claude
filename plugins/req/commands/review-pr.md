---
description: PR 审查与合并 - AI 代码审查、提交评论、合并 PR
argument-hint: "[review|merge|fetch-comments] [PR-ID] [--auto]"
allowed-tools: Read, Write, Edit, Glob, Grep, Bash(git:*, gh:*, tea:*, curl:*), Agent
---

# PR 审查与合并

对已创建的 PR 进行 AI 代码审查，可将审查意见提交到平台，审查通过后合并 PR。

> 不受仓库角色限制，readonly 可执行。不触发缓存同步。
>
> CLI 优先级：GitHub → `gh pr`/`gh api`；Gitea → 按 [`_gitea_cli.md`](./_gitea_cli.md) 检测 `tea`。tea 未覆盖的接口走 curl。

## 命令格式

```
/req:review-pr [子命令] [REQ-XXX]
```

| 子命令 | 说明 | 示例 |
|--------|------|------|
| (空) | 查看 PR 状态 | `/req:review-pr` |
| `review` | AI 代码审查 | `/req:review-pr review` |
| `fetch-comments` | 拉取 PR 评论，AI 生成修改清单并应用 | `/req:review-pr fetch-comments` |
| `merge` | 合并 PR | `/req:review-pr merge` |

省略编号时从当前分支自动匹配需求。未指定子命令时展示 PR 状态概览。

---

## 前置条件

依赖 `/req:pr` 已创建 PR。未找到关联 PR 时提示先创建。

---

## 查看状态

根据 `repoType` 查询 PR（从需求文档 `branch` 字段取分支名，Gitea 需指定 `head=OWNER:branch`）。展示：PR 编号、标题、状态、合并方向、是否可合并、审查状态、可用操作。

---

## review — AI 代码审查

### 1. 获取 PR diff

按平台获取：Gitea `GET /pulls/{N}.diff`，GitHub `gh pr diff`。

### 2. 读取审查依据

按优先级：项目 CLAUDE.md 开发规范 → 测试规范 → 需求文档功能清单和业务规则。

另 Read `docs/prompt/pr-review.md`，存在则将其审查维度（必备输入、优质输出标准、常见失败模式）并入第 4 步审查关注点；缺失静默跳过。

### 3. 对比需求文档与实际实现

检查维度：

| 检查项 | 判断依据 |
|--------|---------|
| 状态字段 | 文档状态是否为「开发中/测试中」 |
| 功能清单 (第二章) | diff 是否覆盖清单每一项 |
| 接口需求 (第五章) | diff 中路由/DTO 是否在文档中记录 |
| 数据模型 (11.1) | 表/字段变更是否在文档中描述 |
| 文件改动清单 (11.3) | diff 实际文件 vs 清单列出文件 |
| 实现步骤 (11.4) | 清单步骤是否在 diff 中能找到 |
| 业务规则 (第三章) | 关键规则是否在代码中体现（如校验逻辑） |
| 关联需求 | 文档「关联」字段引用 |

> primary 读 `docs/requirements/active/`，readonly 读 `<requirementSource.path>/<requirementsDir>/active/`。未找到需求文档时跳过此步。

### 4. AI 逐文件审查

审查维度：正确性、安全性、错误处理、命名规范、代码风格、需求匹配、测试覆盖。

**执行方式按 PR 规模选择**（规则见 [`_delegate.md`](./_delegate.md)）：

| PR 规模 | 方式 |
|---------|------|
| diff ≤ 10 个文件且 ≤ 800 行 | 主会话内联审查 |
| 超过任一阈值 | 按文件并行委派 `file-reviewer` subagent，主会话只做汇总 |

委派时每个 subagent 的 prompt 自包含：该文件的 diff 片段、审查维度、第 2 步读到的项目规范中与该文件相关的条目、第 3 步中与该文件相关的功能点/业务规则。测试文件与被测源文件作为一组派给同一个 subagent。主会话收到各文件清单后去重、核对「待汇总核对」项（如接口改了但调用方未改），再进入第 5 步。

### 5. 输出审查报告

问题分三级：**阻塞**（阻止合并）、**建议**（不阻止）、**信息**（知识分享）。

报告分两部分：代码审查 + 需求文档同步（文档与代码偏差，不阻止合并但建议 `/req:edit` 补齐）。

### 6. 提交审查评论

**零问题直通**：阻塞=0、建议=0、文档同步项=0 时，自动用固定模板提交通过评论，跳过确认。

**有任意问题时**：展示精简版预览 → 询问用户是否提交（`--auto` 跳过确认）。

> 精简规则：保留阻塞（全部）、关键建议、文档同步关键缺失；去除信息级备注、风格命名建议、过程信息。控制在 300 字以内。
>
> Gitea：PR 评论用 `/issues/{N}/comments`（不是 `/pulls/`）。`repoType = "other"` 仅本地展示。

### 7. 无阻塞时的后续操作

阻塞=0 且 PR 为 Open 时：
- **有审核人**（PR reviewers 或 `branchStrategy.reviewers`）→ 提示是否提交 Approved（Gitea `POST /pulls/{N}/reviews` body `{"event":"APPROVED"}`，GitHub `gh pr review --approve`）
- **无审核人** → 仅展示结果，提示可 `/req:review-pr merge`

---

## fetch-comments — 拉取评论并修改代码

### 1. 拉取评论

同时拉取 Issue Comments（整体讨论）和 Review Comments（行内评论，含 `path` 和 `line` 字段）。
Gitea：整体评论 `/issues/{N}/comments`，行内评论先 `GET /pulls/{N}/reviews` 再逐条 `/reviews/{ID}/comments`。

### 2. 过滤评论

排除：当前 git 用户自己的评论、已 resolved/outdated 的行评论、AI 自提交的审查报告（body 以 `AI 代码审查报告` 开头）。

### 3. 展示 & 分析

分组展示评论清单，逐条读取引用源码位置（±20 行上下文），判断可执行/需讨论，生成修改方案。用户确认后执行。

---

## merge — 合并 PR

### 前置检查

PR 存在 → PR 为 Open → 无合并冲突。逐项失败时提示处理方式。

### 执行合并

读取 `branchStrategy.mergeMethod`（默认 `merge`），按平台执行（GitHub `gh pr merge --<mergeMethod>`，Gitea merge method 通过 `Do` 字段传递）。`repoType = "other"` 展示手动合并命令。

### 合并后

输出合并信息，提示 `/req:done` 归档。读取 `branchStrategy.deleteBranchAfterMerge`（默认 `true`），询问是否删除已合并分支。

---

## Git Flow 双 PR 场景

hotfix 分支可能存在两个 PR（→ main + → develop），分别展示，按先 main 后 develop 顺序操作。

---

## 与 `/req:release` 的关系

`/req:review-pr merge` 是单需求里程碑，不是发版：
- migration SQL 在 merge 时不会被归档，等 `/req:release` 统一处理
- 合并到 developBranch ≠ 发布
- 不要手工 tag 或建 Release，应由 `/req:release` 原子化完成

---

## 用户输入

$ARGUMENTS
