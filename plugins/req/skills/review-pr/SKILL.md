---
name: review-pr
description: PR 审查与合并 - AI 代码审查、提交评论、合并 PR
---

# PR 审查与合并

对已创建的 PR 进行 AI 代码审查，可将审查意见提交到平台，审查通过后合并 PR。

> 不受仓库角色限制，readonly 可执行。不触发缓存同步。
>
> CLI 优先级：GitHub → `gh pr`/`gh api`；Gitea → 按 `_gitea_cli.md`（见附录：_gitea_cli.md） 检测 `tea`。tea 未覆盖的接口走 curl。

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

**执行方式按 PR 规模选择**（规则见 `_delegate.md`（见附录：_delegate.md））：

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

---

# 附录（自动内联的共享约定）

> 以下内容由 command 引用的共享子文件自动内联，供不支持 slash 的 Claude 客户端离线阅读。请勿手动编辑本文件——改动应在对应 command 进行。

## 附录：_gitea_cli.md

# 公共逻辑参考 - Gitea CLI 优先

> 此文档定义在 `repoType=gitea` 场景下，何时使用 [`tea`](https://gitea.com/gitea/tea) CLI、何时回退到 `curl + REST API`。GitHub 侧统一使用 `gh`，不在此讨论。
>
> 同伴文档（同目录，按需 Read；此处不用链接，避免生成器传递内联）：`_issue.md`、`_branch.md`。

## 总体原则

1. **优先 `tea`**：当本机存在 `tea` 且已为目标 Gitea 实例配置 login 时，凡是 `tea` 能覆盖的操作一律走 `tea`。
2. **回退 `curl`**：以下任一条件不满足即回退到 `curl + giteaToken`：
   - `command -v tea` 不存在
   - `tea login list` 中没有匹配 `branchStrategy.giteaUrl` 的条目
   - 操作不在 `tea` 覆盖范围（见下方矩阵）
3. **绝不自动 `tea login add`**：`tea login add` 会把 token 写入 `~/.config/tea/config.yml`，属用户可见的全局副作用，必须由用户主动配置。命令检测到 tea 未登录时，**只回退 curl**，最多在首次提示一次："已检测到 `tea` 但未配置当前 Gitea 实例，可手动 `tea login add --name <name> --url ${giteaUrl} --token <token>` 启用 tea CLI 工作流"。

## 检测脚本

各命令在执行 Gitea 调用前先跑一次：

```bash
USE_TEA=0
if command -v tea &>/dev/null; then
  if tea login list 2>/dev/null | awk 'NR>1 {print $3}' | grep -qx "${GITEA_URL%/}"; then
    USE_TEA=1
    # 取匹配的 login name 备用（多 login 场景需要 --login <name>）
    TEA_LOGIN=$(tea login list 2>/dev/null | awk -v u="${GITEA_URL%/}" 'NR>1 && $3==u {print $2; exit}')
  fi
fi
```

- `tea login list` 输出列：`Name | URL | SSHHost | User`，第 3 列是 URL
- 多 login 场景务必显式 `--login "${TEA_LOGIN}"`，避免选错实例
- 检测结果在同一命令会话内复用，不重复探测

## 操作覆盖矩阵

| 操作 | tea 命令 | tea 是否够用 | 不够用时回退原因 |
|------|---------|------------|----------------|
| 查看 issue 详情 | `tea issues <N>` | ✅ | — |
| 列出 issues | `tea issues ls --state ... --labels ...` | ✅ | — |
| 创建 issue | `tea issues create --title --body --labels --assignees` | ✅ | — |
| 编辑 issue 标题/正文 | `tea issues edit <N> --title --description` | ⚠️ 部分 | tea 无 `--add-labels` / `--remove-labels`，标签增删仍用 curl |
| 关闭 / 重开 issue | `tea issues close <N>` / `tea issues reopen <N>` | ✅ | tea 不支持 `--reason`（GitHub 专属），保持原静默降级提示 |
| 评论 issue | `tea comment <N> <body>` | ✅ | — |
| 列出 issue 评论 | — | ❌ | tea 无对应子命令，使用 `curl /issues/{n}/comments` |
| 创建 PR | `tea pulls create --title --description --base --head` | ✅ | — |
| 列出 PR | `tea pulls ls --state ... --base ...` | ✅ | — |
| 查看 PR 详情 | `tea pulls <N>` | ✅ | — |
| 拉取 PR diff | — | ❌ | tea 无 `pulls diff`，用 `curl ${url}/pulls/${N}.diff` |
| PR 评论（讨论级） | `tea comment <PR-N> <body>` | ✅ | — |
| PR Review（行内评论 / approve） | — | ❌ | tea 无 reviews API，全部走 curl |
| 合并 PR | `tea pulls merge <N> --style merge|rebase|squash` | ✅ | — |
| 创建 Release | `tea releases create --tag --title --note` | ⚠️ 部分 | 上传附件不便（无 `--asset` 一致语义），SQL 资产仍用 curl |
| 列出 / 查看 Release | `tea releases ls` / `tea releases <tag>` | ✅ | — |
| 标签 CRUD（仓库级 labels） | `tea labels ls` / `tea labels create` | ⚠️ 部分 | 删除/批量场景用 curl |

> 不在表中的 Gitea 接口（如 `collaborators`、`/user`、PR review threads 等）默认走 curl。

## 命令执行约定

**有 tea 的分支**：

```bash
# 示例：关闭 issue
if [[ $USE_TEA -eq 1 ]]; then
  tea issues close --login "${TEA_LOGIN}" "${N}"
else
  curl -s -X PATCH "${GITEA_URL}/api/v1/repos/${OWNER}/${REPO}/issues/${N}" \
    -H "Authorization: token ${TOKEN}" \
    -H "Content-Type: application/json" \
    -d '{"state":"closed"}'
fi
```

**输出解析差异**：
- `tea` 默认输出人类可读表格，要 JSON 用 `--output json`（部分子命令支持）
- 解析需求复杂时，依旧用 curl + jq，保持稳定
- 状态码 / 错误处理：`tea` 失败时 exit code 非 0 + stderr 文字，不要试图按 HTTP code 判断

## 与 `_issue.md` 的关系

`_issue.md` 中所有 `repoType="gitea"` 的 curl 示例都视为 **`USE_TEA=0` 时的回退路径**。命令文件不必在每个 curl 块前重复 `USE_TEA` 判断，但必须在 Gitea 操作总入口处引用本文，让 Claude 在执行时按矩阵选 CLI。

## 不实现的部分

- **不自动 `tea login add`**：理由见上方原则 3
- **不内置 `tea` 安装**：仅检测，缺失时静默回退到 curl，不打断流程
- **不为每个 curl 例改写成 if/else 模板**：命令文件是给 Claude 的指令，Claude 按本文矩阵在运行时挑选即可

## 附录：_delegate.md

# 子任务委派（subagent）规范

> 目的：把「吞吐大、推理浅」的步骤交给独立 subagent 执行，主会话只接收结论。收益有两层：便宜模型单价低；更重要的是**上下文隔离**——测试日志、文件全文、大段 diff 留在 subagent 内，不进入主会话，后续每一轮都不再为它们付费。

## 何时委派

满足任一即委派；否则直接在主会话做（委派本身有开销：写任务说明 + 结果回传）：

| 条件 | 典型步骤 |
|------|---------|
| 步骤会往主会话灌入大量原始输出（估计 > 1 万 token） | 跑测试、拉大 diff、批量 grep |
| 步骤可按单元切分且各单元相互独立 | 逐文件审查、多模块搜索 |
| 步骤不依赖主会话已积累的上下文 | 一条命令 + 判定规则即可完成 |

**不委派**：需要主会话已有上下文才能判断的推理（方案设计、跨文件改动、与用户交互的闸门）。

## 可用 agent（随插件分发，位于 `plugins/req/agents/`）

| agent | 模型 | 用途 | 返回 |
|-------|------|------|------|
| `test-runner` | haiku | 执行给定测试命令 | 计数 + 失败用例（file:line、断言、精简堆栈） |
| `file-reviewer` | sonnet | 审查单个文件的 diff | 阻塞/建议/信息分级清单 + 跨文件疑点 |
| `code-scout` | haiku | 按关键词定位相关代码（实现处/调用链/同类参照） | 文件清单（路径、相关度、关键行、原因），不含文件内容 |

命令的 frontmatter `allowed-tools` **必须包含 `Agent`**（`allowed-tools` 是白名单限制，缺失则无法派生）。

## 委派时必须做到

1. **任务说明自包含**：subagent 没有主会话历史。工作目录、命令、判定规则、项目规范中相关的几条（不是整份文件）都要写进 prompt。
2. **只要结论，不要原文**：agent 定义已规定返回格式；prompt 中再明确「不要回传完整日志/文件内容」。
3. **独立单元并行**：同一批 subagent 在一次调用里一起发出，结果由主会话汇总、去重、合并跨单元问题。
4. **subagent 只读**：agent 定义不含 Write/Edit；需要改代码的结论由主会话执行。
5. **失败要透传**：subagent 报 ERROR/超时时把原因带回，主会话决定重试或降级为内联执行，不静默吞掉。

## 与仓库角色 / 调用形态的关系

- 与 `requirementRole` 无关：委派不涉及需求文档写入。
- skill 形态同样适用：Agent 工具随会话可用；agent 定义随 req 插件安装。
