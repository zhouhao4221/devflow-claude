---
name: fix
description: 轻量修复 - 无文档的 bug 修复流程，AI 辅助定位问题
---

# 轻量修复

创建修复分支，AI 辅助分析定位 bug，修复后直接提交和 PR。不创建需求文档。

> **Audience:** Engineer
> 此命令**不受仓库角色限制**，readonly 仓库也可执行。
> 不触发缓存同步（无需求文档）。
>
> **CLI 优先级**：GitHub 用 `gh`；Gitea 按 `_gitea_cli.md`（见附录：_gitea_cli.md） 检测 `tea`，可用即走 `tea`，否则回退本文 curl 示例。

## 命令格式

```
/req:fix <问题描述> [--from-issue=#编号] [--auto]
```

**`--auto` 非交互模式**：跳过修复方案确认、issue 关闭询问，修复完成后自动串联 `/req:commit` + `/req:pr`。
用于小 bug 一键走完，**代价是放弃方案/提交前的 review 机会**（git commit 的 hook 确认仍保留作为最后一道保险）。

示例：
- `/req:fix 登录超时后 token 未清除`
- `/req:fix 订单列表分页数据重复`
- `/req:fix 导出 Excel 中文文件名乱码`
- `/req:fix --from-issue=#42` - 从 issue 读取问题描述后分析
- `/req:fix 导出 Excel 中文文件名乱码 --auto` - 一键走完修复并创建 PR

---

## 执行流程

### 0. （可选）从 issue 读取问题描述

若命令带 `--from-issue=#N`，按 _issue.md 的 Issue 拉取规范（见附录：_issue.md） 拉取 issue，把 issue 标题 + 正文拼成用户问题描述传入步骤 1。

本命令不创建需求文档，issue 编号通过**分支名 `-iN` 后缀**持久化（步骤 2.3 创建分支时追加），供 `/req:commit`、步骤 5 关闭 issue 等后续操作识别。参见 _issue.md 的 Issue 与分支关联（见附录：_issue.md）。

用户同时提供了描述和 `--from-issue` 时，以用户描述为主，issue 内容作为补充上下文。

### 1. AI 辅助分析 bug

> 读取项目 CLAUDE.md 的「项目架构」章节，了解分层结构和目录布局。
> Read `docs/prompt/error-diagnosis.md`，存在则按其规范（必备输入、根因判定标准、常见失败模式）约束定位；缺失静默跳过。
> **此阶段在当前分支上进行，不创建新分支。**

根据用户描述的问题，AI 进行定位分析：

#### 1.1 问题分析

```
Bug 分析：登录超时后 token 未清除

问题理解：
- 现象：用户登录超时后，本地 token 未被清除，导致后续请求携带过期 token
- 影响范围：认证流程、请求拦截器

可能涉及的代码：
```

#### 1.2 定位相关文件

委派 `code-scout` subagent 搜索代码库（prompt 给：1.1 的现象与影响范围、报错信息/符号名、CLAUDE.md 架构章节的分层目录摘要），主会话拿到清单后只精读高/中相关的关键行段，用于 1.4 根因分析；规则见 `_delegate.md`（见附录：_delegate.md）。用户已指明具体文件时直接 Read，不委派。展示格式：

```
相关文件定位：

| 文件 | 相关度 | 原因 |
|------|-------|------|
| src/utils/auth.ts | 高 | token 存取逻辑 |
| src/interceptors/request.ts | 高 | 请求拦截，超时处理 |
| src/store/user.ts | 中 | 用户状态管理 |
```

#### 1.3 关联需求匹配（自动，低成本）

**目的**：找出可能引入此 bug 的需求，获取业务上下文辅助定位。

**流程**（只读索引 + 按需读正文，控制 token 消耗）：

1. 读 `docs/requirements/INDEX.md`（~500 token）
2. 用 bug 相关文件路径 + 关键词在 INDEX.md 中模糊匹配（标题含关键词 或 模块与 bug 相关 → 命中）
3. 命中时仅读该需求的「十一、实现方案 - 文件改动清单」（~1k token/个，最多 2 个）；未命中静默跳过

**命中时展示**：

```
关联需求：

| 需求 | 标题 | 关联原因 |
|------|------|---------|
| REQ-003 | 登录认证优化 | 修改了 src/interceptors/request.ts |

此 bug 可能由 REQ-003 引入，已读取其文件改动清单辅助定位。
```

**未命中时**：静默跳过，不输出任何内容，不消耗额外 token。

**成本控制**：

| 步骤 | Token 消耗 | 条件 |
|------|-----------|------|
| 读 INDEX.md | ~500 | 始终执行 |
| 匹配关键词 | ~0 | AI 内部处理 |
| 读命中需求节选 | ~1k/个 | 仅命中时，最多 2 个 |
| **总计** | **500 ~ 2500** | 远低于全量读取（~50k） |

#### 1.4 根因分析

AI 综合代码搜索结果和关联需求上下文，给出根因判断：

```
根因分析：

在 src/interceptors/request.ts:45，响应拦截器捕获 401 状态码时
调用了 router.push('/login')，但未调用 removeToken()。
（REQ-003 登录认证优化 新增了 401 拦截逻辑，但遗漏了 token 清除）

建议修复：在跳转登录页前清除 token。
```

#### 1.5 修复建议

```
修复建议：

1. src/interceptors/request.ts
   - 在 401 处理分支中，跳转前调用 removeToken()

2. 建议同时检查：
   - token 过期的其他入口（如定时刷新失败）

是否按以上方案修复？（可以补充说明或调整方向）
```

**`--auto` 模式**：跳过"等待用户确认"，直接展示方案后进入步骤 2。

**非 `--auto` 模式**：等待用户确认。用户可以：
- 确认方案 → 进入步骤 2
- 补充信息 / 调整方向 → AI 重新分析
- 放弃 → 结束，不创建分支

---

### 2. 创建修复分支

> **用户确认修复方案后**才创建分支，避免分析后放弃导致残留空分支。

#### 2.1 工作区检查

有未提交改动时终止，提示先 commit 或 stash。

#### 2.2 读取分支策略

从 `branchStrategy` 读取 `mainBranch`、`branchFrom`（缺省同 mainBranch）、`fixPrefix`（缺省 `fix/`）；未配置时自动检测主分支。

#### 2.3 创建分支

AI 根据问题描述生成英文 slug（lowercase kebab-case，最多 5 词）。

**有 `--from-issue=#N`**：分支名末尾追加 `-i<N>`（参见 _issue.md 的 Issue 与分支关联（见附录：_issue.md））。

```
创建修复分支：fix/login-token-not-cleared-i42
   基于：main（来源：branchStrategy.branchFrom）
```

**无 `--from-issue`**：不加 issue 后缀。

```
创建修复分支：fix/login-token-not-cleared
   基于：main（来源：branchStrategy.branchFrom）
```

fetch `branchFrom`，从远端创建并切换到新分支（有 issue 时分支名末尾追加 `-i<N>`）。

---

### 3. 执行修复

AI 按确认的方案修改代码。

修改完成后，若项目 `docs/prompt/testing.md`（或架构章节）定义了测试命令且存在与改动相关的测试，派 `test-runner` subagent 回归（规则见 `_delegate.md`（见附录：_delegate.md））；失败先修再进入步骤 4。无相关测试则跳过，不新建测试。

---

### 4. 修复完成提示

```
✅ 修复完成！

分支：fix/login-token-not-cleared
修改文件：
- src/interceptors/request.ts（+3 -1）

后续操作：
- /req:commit - 提交修复代码
- /req:pr - 创建 PR
```

若来自 `--from-issue=#N`，在后续操作提示中追加：
```
提交时建议在 commit message 末尾添加 closes #N 以自动关联 issue
```

---

### 4.5 （仅 `--auto` 模式）自动串联 commit + PR

非 `--auto` 模式跳过本步骤，结束命令。

`--auto` 模式下，步骤 4 展示完成提示后**立即继续执行**，不等待用户输入。

#### 4.5.0 建立 auto 标记（跳过 hook 确认）

在 commit/push/PR 前，先创建 `.claude/.req-auto` 标记文件，让 PreToolUse hook（`confirm-before-commit.sh`）在检测到该文件且 mtime 在 10 分钟内时自动放行，不再弹出原生确认对话框。

> **标记生命周期**：步骤 4.5 开始时创建，步骤 4.5 结束（成功或失败）时在 4.5.4 清理。若命令异常终止残留，10 分钟后 hook 自动忽略该标记，不会造成长期"默认放行"。

#### 4.5.1 调用 `/req:commit` 流程

参见 [commit.md](./commit.md)：

- 自动暂存所有变更
- 从当前分支名 `fix/<slug>-iN` 中不含 REQ/QUICK 编号 → commit message 不加 `(REQ-XXX)`
- 若有 `--from-issue=#N`，在 commit message 末尾自动追加 `closes #N`
- 使用 `修复:` 前缀（fix 命令语义固定为修复）
- 示例：`修复: 登录超时后 token 未清除 closes #42`
- 执行 `git commit`（hook 检测到 `.claude/.req-auto` 自动放行，无需用户确认）

#### 4.5.2 调用 `/req:pr` 流程

参见 [pr.md](./pr.md)：

- `git push -u origin <branch>`
- 按 `branchStrategy.repoType` 创建 PR：
  - `gitea` → 调用 Gitea API
  - `github` → `gh pr create`
  - `other` → 仅输出合并命令
- PR 标题：`fix: <问题描述>`（无 REQ 编号）
- PR body 包含：问题描述、根因分析（来自步骤 1.4）、修改文件清单；若有 `closes #N` 自动关联 issue

#### 4.5.3 失败处理

任何一步失败（commit/push/PR 创建）→ **立即停止**，先执行 4.5.4 清理 marker，然后展示错误和手动恢复命令，不跳过到下一步。

#### 4.5.4 清理 auto 标记

无论成功或失败，都必须在命令结束前删除 `.claude/.req-auto`。

**成功输出**：
```
✅ 一键修复完成！

  commit abc1234: 修复: 登录超时后 token 未清除 closes #42
  PR: <url>
```

---

### 5. （可选）关闭 issue

仅当命令带 `--from-issue=#N` **且非 `--auto` 模式**时执行本步骤。

> **`--auto` 模式跳过询问**：commit message 已包含 `closes #N`，PR 合并时 Git 平台会自动关闭 issue，不需要在 PR 未合并前主动关闭。

在步骤 4 展示完成提示后，询问用户：

```
本次修复来自 issue #N
   是否关闭该 issue？(y/n)
```

**用户确认（y）** → 按 `repoType` 关闭 issue，逻辑同 [issue.md §5](./issue.md)。

**用户拒绝（n）**：跳过。

> commit message 含 `closes #N` 时，PR 合并时 Git 平台会自动关闭 issue，无需手动操作。

---

## 与其他修复方式的区别

| 方式 | 命令 | 文档 | 分支 | 适用场景 |
|------|------|------|------|---------|
| 轻量修复 | `/req:fix` | 无 | fix/slug | 日常小 bug，改动 < 5 个文件 |
| 有记录的修复 | `/req:new-quick` | QUICK 文档 | fix/QUICK-XXX-slug | 需要记录的修复，方便追溯 |
| 紧急修复 | `/req:branch hotfix` | 无 | hotfix/slug | 线上紧急问题，从主分支拉 |

**选择依据：**
- 改完就忘的小 bug → `/req:fix`
- 需要测试和记录的修复 → `/req:new-quick`
- 线上出问题了 → `/req:branch hotfix`

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
