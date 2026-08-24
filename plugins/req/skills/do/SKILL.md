---
name: do
description: 智能开发 - AI 分析意图，自动选择流程，生成方案并执行
---

# 智能开发

描述你要做的事，AI 自动分析意图、选择合适的流程、生成方案并执行。无需关心该用哪个命令。

> **Audience:** Engineer
> 此命令**不受仓库角色限制**，readonly 仓库也可执行。
> 不触发缓存同步（无需求文档）。
>
> **CLI 优先级**：GitHub 用 `gh`；Gitea 按 `_gitea_cli.md`（见附录：_gitea_cli.md） 检测 `tea`，可用即走 `tea`，否则回退本文 curl 示例。

## 命令格式

```
/req:do <描述> [--from-issue=#编号]
```

示例：
- `/req:do 优化订单查询性能，加索引和分页缓存`
- `/req:do 重构用户服务层，拆分过大的方法`
- `/req:do 升级 Go 到 1.23`
- `/req:do 统一错误码格式`
- `/req:do 给商品列表加个搜索功能`
- `/req:do --from-issue=#42` - 从 issue 读取描述后分析

---

## 执行流程

### 0. （可选）从 issue 读取描述

若命令带 `--from-issue=#N`，按 _issue.md 的 Issue 拉取规范（见附录：_issue.md） 拉取 issue，把 issue 标题 + 正文拼成用户描述传入步骤 1。

本命令不创建需求文档，issue 编号通过**分支名 `-iN` 后缀**持久化（步骤 3 创建分支时追加），供 `/req:commit`、步骤 5 关闭 issue 等后续操作识别。参见 _issue.md 的 Issue 与分支关联（见附录：_issue.md）。

### 1. AI 分析意图

根据用户描述，AI 判断任务类型和规模：

```
分析：<用户描述>

  类型：<优化 | 重构 | 升级 | 规范 | 小功能 | 修复>
  规模：<轻量（无需文档）| 中等（建议创建 QUICK）| 正式（建议创建 REQ）>
  影响范围：<涉及的模块/文件数估算>
```

**类型判断依据：**

| 类型 | 关键词/特征 | 分支前缀 | 提交前缀 |
|------|-----------|---------|---------|
| 优化 | 性能、缓存、索引、查询慢、加速 | `improve/` | `优化` |
| 重构 | 重构、拆分、抽取、整理、解耦 | `improve/` | `重构` |
| 升级 | 升级、更新、迁移、版本 | `improve/` | `构建` |
| 规范 | 统一、规范、格式、命名、lint | `improve/` | `样式` |
| 小功能 | 增加、新增、添加、支持 | `feat/` | `新功能` |
| 修复 | 修复、bug、报错、异常、失败 | `fix/` | `修复` |

**规模判断依据：**

| 规模 | 条件 | 建议流程 |
|------|------|---------|
| 轻量 | 改动 < 5 个文件，无新 API/表结构 | 直接执行（本命令） |
| 中等 | 改动 5~15 个文件，或有新 API | 建议 `/req:new-quick` |
| 正式 | 改动 > 15 个文件，涉及多模块/新业务 | 建议 `/req:new` |

**规模为中等或正式时**：
```
此任务规模较大，建议使用正式流程以便追踪：

  /req:new-quick <标题>    有文档记录的轻量任务
  /req:new <标题>          正式需求（含评审、测试）

继续用轻量模式执行，还是切换到上述命令？
```

等待用户选择。用户选择继续 → 进入步骤 2。

### 2. 分析代码，生成方案

> 读取项目 CLAUDE.md 的「项目架构」章节，了解分层结构和目录布局。
> 第 1 步意图为「重构 / 优化」时，Read `docs/prompt/refactoring.md`，存在则按其约束（行为不变、契约不变、范围聚焦）生成方案；缺失静默跳过。

定位相关文件委派 `code-scout` subagent（prompt 给：第 1 步识别的意图与目标、关键词/符号名、架构分层目录摘要），主会话只精读其返回的高/中相关片段后生成方案；用户已指明文件或范围 ≤ 3 个文件时直接 Read。规则见 `_delegate.md`（见附录：_delegate.md）。

```
代码分析：

涉及文件：

| 文件 | 改动类型 | 说明 |
|------|---------|------|
| internal/order/store/order_store.go | 修改 | 添加查询索引 |
| internal/order/biz/order_list.go | 修改 | 增加分页缓存逻辑 |
| internal/order/model/order_model.go | 修改 | 补充索引注解 |

修改方案：

1. order_model.go
   - Order 表 `status` + `created_at` 添加复合索引

2. order_store.go
   - ListOrders 查询增加 hint 走索引
   - 添加 count cache（5 分钟 TTL）

3. order_list.go
   - 首页查询结果缓存（Redis，按筛选条件 key）

是否按以上方案执行？（可以补充说明或调整方向）
```

**等待用户确认**。用户可以：
- 确认方案 → 进入步骤 3
- 补充/调整 → AI 重新分析
- 放弃 → 结束

### 3. 执行方案

**无 `--from-issue`**：直接在当前分支上开发，不创建新分支。

**有 `--from-issue=#N`**：在步骤 2 方案确认后、开始编码前，根据分支策略创建分支：
1. 读取 `branchStrategy`（未配置则使用默认前缀）
2. 分支前缀由步骤 1 的类型判断决定（见类型判断依据表的「分支前缀」列）
3. AI 根据 issue 标题生成英文 slug
4. 分支名末尾追加 `-i<N>`（参见 _issue.md 的 Issue 与分支关联（见附录：_issue.md））
5. 示例：`fix/optimize-order-query-i42`、`feat/add-search-feature-i12`

AI 按确认的方案修改代码。修改完成后，若项目 `docs/prompt/testing.md`（或架构章节）定义了测试命令且存在与改动相关的测试，派 `test-runner` subagent 回归（规则见 `_delegate.md`（见附录：_delegate.md））；失败先修再进入步骤 4。无相关测试则跳过。

### 4. 完成提示

```
✅ 完成！

修改文件：
- internal/order/store/order_store.go（+25 -3）
- internal/order/biz/order_list.go（+40 -5）
- internal/order/model/order_model.go（+2 -0）

后续操作：
- /req:commit       提交代码
- /req:pr           创建 PR
```

若来自 `--from-issue=#N`，在后续操作提示中追加：
```
提交时建议在 commit message 末尾添加 closes #N 以自动关联 issue
```

### 5. （可选）关闭 issue

仅当命令带 `--from-issue=#N` 时执行本步骤。

在步骤 4 展示完成提示后，询问用户：

```
本次任务来自 issue #N
   是否关闭该 issue？(y/n)
```

**用户确认（y）** → 按 `repoType` 关闭 issue，逻辑同 [issue.md §5](./issue.md)。

**用户拒绝（n）**：跳过。

---

## 与其他命令的区别

| 命令 | 文档 | 分支 | AI 分析 | 适用场景 |
|------|------|------|--------|---------|
| `/req:do` | 无 | 自动选前缀 | 分析意图+方案 | 优化、重构、升级、小调整 |
| `/req:fix` | 无 | `fix/` | 定位 bug | 明确的 bug 修复 |
| `/req:new-quick` | QUICK 文档 | `fix/` | 无 | 需要记录的小任务 |
| `/req:new` | REQ 文档 | `feat/` | 需求分析 | 正式业务需求 |

**选择依据：**
- 知道是 bug → `/req:fix`
- 优化/重构/升级/规范化 → `/req:do`
- 需要文档记录 → `/req:new-quick`
- 正式业务功能 → `/req:new`
- 不确定用哪个 → `/req:do`（AI 帮你判断）

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

## 附录：_issue.md

# 公共逻辑参考 - Issue 关联

> 此文档定义 `--from-issue` 拉取规范、OWNER/REPO 解析、Issue 与分支/提交的关联规则、Issue 编号读取优先级、关闭策略。
>
> 同伴文档（同目录，按需 Read；此处不用链接，避免生成器传递内联）：`_storage.md`、`_branch.md`、`_template.md`、`_granularity.md`、`_claude-md.md`、`_gitea_cli.md`。
>
> **CLI 优先级**：所有 Gitea 调用先按 `_gitea_cli.md`（见附录：_gitea_cli.md） 检测 `tea`，可用即走 `tea`；本文中的 `curl` 示例视为 `USE_TEA=0` 时的回退路径。

## Issue 拉取规范

`--from-issue=#N` 参数用于从 Git 平台拉取 issue 信息。各命令统一使用以下逻辑：

### 变量来源

| 变量 | 来源 | 说明 |
|------|------|------|
| `GITEA_URL` | `branchStrategy.giteaUrl` | Gitea 实例地址，**必须从配置读取，禁止从 git remote 猜测** |
| `TOKEN` | `branchStrategy.giteaToken` | Gitea API Token |
| `OWNER/REPO` | `git remote get-url origin` 解析 | 从 remote URL 提取，支持 SSH 和 HTTPS 格式 |
| `repoType` | `branchStrategy.repoType` | 决定使用 Gitea API 还是 gh CLI |

### OWNER/REPO 解析

从 `git remote get-url origin` 的结果中提取：
```
ssh://git@gitea.example.com:10022/owner/repo.git  →  owner/repo
git@github.com:owner/repo.git                     →  owner/repo
https://github.com/owner/repo.git                 →  owner/repo
```

去掉 `.git` 后缀，取最后两段路径作为 `OWNER/REPO`。

### 拉取逻辑

**repoType = "gitea"**：
```bash
# tea 可用 + 已 login（详见 _gitea_cli.md）
tea issues --login "${TEA_LOGIN}" "${N}" --output json

# 回退：curl
curl -s "${GITEA_URL}/api/v1/repos/${OWNER}/${REPO}/issues/${N}" \
  -H "Authorization: token ${TOKEN}"
```
- `GITEA_URL` 和 `TOKEN` 未配置时提示：`❌ Gitea 未配置 giteaUrl 或 giteaToken，请先执行 /req:branch init`

**repoType = "github"**：
```bash
gh issue view ${N} --json title,body,number,url,labels
```

**repoType = "other" 或未配置**：
```
❌ 未配置支持的 Git 平台（需 repoType=github 或 gitea）
请先执行 /req:branch init 配置
```

## Issue 与分支/提交的关联

### Issue 编号在分支名中的传递

当需求或任务来自 `--from-issue=#N`，分支名末尾追加 `-iN` 后缀，使 issue 编号可从分支名推断：

```
feat/REQ-001-user-points-i12       ← /req:dev，需求文档 issue=#12
fix/QUICK-003-fix-login-i5         ← /req:dev，快速修复 issue=#5
fix/optimize-order-query-i42       ← /req:do --from-issue=#42
fix/login-token-not-cleared-i42    ← /req:fix --from-issue=#42
feat/REQ-001-user-points           ← 无 issue 关联，不加后缀
```

**规则**：
- `-iN` 仅当 issue 编号存在时追加（需求文档 `issue` 字段非 `-`，或 `/req:do`、`/req:fix` 的 `--from-issue` 参数）
- `N` 为纯数字，不带 `#`
- 位于分支名最末尾，不影响 REQ-XXX / QUICK-XXX 的提取

### Issue 编号的读取优先级

各命令需要获取当前 issue 编号时，按以下顺序查找：

| 优先级 | 来源 | 适用场景 |
|-------|------|---------|
| 1 | 需求文档元信息 `issue` 字段 | `/req:done`、`/req:commit`（有需求文档时） |
| 2 | 当前分支名的 `-iN` 后缀 | `/req:commit`、`/req:do`、`/req:fix` 完成时（无需求文档时） |

**解析正则**：`-i(\d+)$` 匹配分支名末尾的 issue 编号。

### Issue 在 commit message 中的关联

当检测到 issue 编号时，`/req:commit` 在 commit message 末尾追加 `closes #N`：

```
优化: 订单查询添加索引 closes #42
新功能: 实现用户积分规则 (REQ-001) closes #12
```

Git 平台（GitHub / Gitea）会自动将该 commit 关联到 issue，并在合并时关闭 issue。

### Issue 关闭策略

| 场景 | issue 来源 | 关闭方式 | 关闭时机 |
|------|-----------|---------|---------|
| `/req:new --from-issue` | 需求文档 `issue` 字段 | `/req:done` 询问 + API 关闭 | 需求完成时 |
| `/req:new-quick --from-issue` | 需求文档 `issue` 字段 | `/req:done` 询问 + API 关闭 | 需求完成时 |
| `/req:do --from-issue` | 分支名 `-iN` | `/req:do` 完成时询问 + API 关闭 | 任务完成时 |
| `/req:fix --from-issue` | 分支名 `-iN` | `/req:fix` 完成时询问 + API 关闭 | 修复完成时 |
| 以上所有 | commit message `closes #N` | Git 平台自动关闭 | PR 合并时 |

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
