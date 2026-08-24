---
name: done
description: 完成需求 - 标记完成并归档
---

# 完成需求

标记需求为已完成，归档文档。

> 存储路径和缓存同步规则见 _storage.md（见附录：_storage.md）
>
> **CLI 优先级**：GitHub 走 `gh`；Gitea 按 `_gitea_cli.md`（见附录：_gitea_cli.md） 检测 `tea`，可用即走 `tea pulls create` / `tea issues close`，否则回退本文 curl 示例。

## 命令格式

```
/req:done [REQ-XXX]
```

- 省略编号时自动选择「测试中」的需求
- 多个候选时交互式选择

---

## 执行流程

### 1. 选择需求

- 指定编号 → 使用该需求
- 未指定 → 扫描 `active/` 中状态为「测试中」的需求，唯一则直接使用，多个则列出让用户选

### 2. 前置检查

- 读取需求文档 YAML 元信息 + 「测试要点」章节
- 状态必须为「测试中」，否则报错退出
- 若测试要点中存在未勾选项（`- [ ]`），展示警告并要求用户确认继续

### 3. 更新需求文档

修改 YAML 元信息：
- `status: 已完成`
- `completedAt: YYYY-MM-DD`（今日）

勾选生命周期「已完成」对应的复选框。

### 4. 更新 PRD 索引

定位 `docs/requirements/PRD.md` 的「需求追踪」章节（`grep -n "需求追踪"`），更新对应需求所在行的「状态」和「完成日期」两列。PRD 不存在或无该章节时跳过。

### 5. 归档文档 + 同步缓存

将需求文档从 `active/` 移动到 `completed/`（使用 `git mv` 保留历史）。缓存同步由 PostToolUse Hook 自动处理，无需命令内显式调用。

### 6. 输出确认

```
REQ-XXX <标题> 已完成
   归档至 docs/requirements/completed/REQ-XXX-<slug>.md
```

### 7. 分支合并提醒

读取 `.claude/settings.local.json.branchStrategy` 和需求文档的 `branch` 字段。无 `branchStrategy` 或 `branch` 为空 → 跳过本步。

按 `repoType` 创建 PR，逻辑同 [pr.md](./pr.md)（push + 创建 PR + 提示 review-pr）。

**特殊情况**：
- `giteaToken` 缺失 → 提示手工 compare 链接
- Git Flow + hotfix 分支 → 需合并到 `main` 和 `develop` 两处，创建两个 PR

### 8. 关联 issue 关闭提醒

按 _issue.md 的 Issue 读取优先级（见附录：_issue.md） 获取 issue 编号：先查需求文档元信息 `issue` 字段，若为 `-` 或为空则查分支名 `-iN` 后缀。均未找到 → 跳过本步。

否则询问用户：

```
检测到关联 issue: #123
   是否关闭该 issue？(y/n)
```

**用户确认（y）** → 按 `repoType` 关闭 issue，逻辑同 [issue.md §5](./issue.md)。

**用户拒绝（n）**：跳过。

---

## 与 `/req:release` 的区别

`/req:done` 只做归档，不发版。发版用 `/req:release`（合并 SQL / 生成 changelog / 打 tag / 创建 Release）。

## 用户输入

$ARGUMENTS

---

# 附录（自动内联的共享约定）

> 以下内容由 command 引用的共享子文件自动内联，供不支持 slash 的 Claude 客户端离线阅读。请勿手动编辑本文件——改动应在对应 command 进行。

## 附录：_storage.md

# 公共逻辑参考 - 存储与配置

> 此文档定义 settings 文件写入、存储路径、缓存同步、需求编号、元信息等共用规则。
>
> 同伴文档（同目录，按需 Read；此处不用链接，避免生成器传递内联）：`_branch.md`（分支策略）、`_issue.md`（Issue 关联）、`_template.md`（模板与状态确认）、`_granularity.md`（需求粒度）、`_claude-md.md`（架构检查）。

## settings 文件写入规范

DevFlow 配置存储在项目根的 `.devflow/` 目录，按是否含密钥分两个文件：

| 字段 | 文件 | 纳入 git | 说明 |
|------|------|----------|------|
| `requirementProject` | `.devflow/settings.json` | ✅ | 团队共享配置 |
| `requirementRole` | `.devflow/settings.json` | ✅ | 团队共享配置 |
| `requirementsDir` | `.devflow/settings.json` | ✅ | 需求文档根目录，省略时默认 `docs/requirements` |
| `branchStrategy`（不含 token） | `.devflow/settings.json` | ✅ | 团队共享配置 |
| `giteaToken` | `.devflow/settings.local.json` | ❌ | 个人密钥，禁止提交 |

> **`.devflow/` 与 `.claude/` 的分工**：`.devflow/` 只放 DevFlow 业务配置（上表字段）；Claude Code 自身的 hooks、permissions 仍在 `.claude/settings.json`，两者互不迁移。项目级窄知识 skill 仍在 `.claude/skills/`。

**写入规则（强制）**：

1. **禁止独立配置文件**：DevFlow 字段一律合并进 `.devflow/settings.json` 或 `.devflow/settings.local.json`，禁止另建 `devflow.json`、`branchStrategy.json` 等
2. **合并写入**：先读取已有文件内容，合并需要更新的字段后写回，**不得覆盖已有字段**
3. **目录检查**：`.devflow/` 目录不存在时先创建
4. **读取合并顺序**：命令读配置时先读 `.devflow/settings.json`，再用 `.devflow/settings.local.json` 覆盖同名字段（`giteaToken` 以 local 为准）
5. **无写入权限的回退**：当 Write/Edit 工具被拒绝时，**不得**改写到其他文件，而应直接输出可复制执行的 shell 命令：

   ```bash
   # 写入 .devflow/settings.json（团队配置）
   python3 -c "import json,os; p='.devflow/settings.json'; os.makedirs('.devflow',exist_ok=True); d=json.load(open(p)) if os.path.exists(p) else {}; d['requirementProject']='my-project'; d['requirementRole']='primary'; json.dump(d,open(p,'w'),indent=2,ensure_ascii=False)"
   # 写入 .devflow/settings.local.json（本地密钥）
   python3 -c "import json,os; p='.devflow/settings.local.json'; os.makedirs('.devflow',exist_ok=True); d=json.load(open(p)) if os.path.exists(p) else {}; d['giteaToken']='YOUR_TOKEN'; json.dump(d,open(p,'w'),indent=2,ensure_ascii=False)"
   ```

```python
# 写入团队配置（.devflow/settings.json）
import json, os

path = ".devflow/settings.json"
os.makedirs(".devflow", exist_ok=True)
existing = json.load(open(path)) if os.path.exists(path) else {}
existing["requirementProject"] = "..."  # 只更新需要的字段
with open(path, "w") as f:
    json.dump(existing, f, indent=2, ensure_ascii=False)

# 写入本地密钥（.devflow/settings.local.json）
path = ".devflow/settings.local.json"
existing = json.load(open(path)) if os.path.exists(path) else {}
existing["giteaToken"] = "YOUR_TOKEN"
with open(path, "w") as f:
    json.dump(existing, f, indent=2, ensure_ascii=False)
```

### 读取惯例

命令读取 `requirementProject` / `requirementRole` / `requirementsDir` / `branchStrategy` 时，统一按以下顺序合并：

```
config = merge(.devflow/settings.json, .devflow/settings.local.json)
# .devflow/settings.local.json 中的同名字段覆盖 settings.json
```

**Legacy Claude 迁移（breaking change）**：v2.x 旧项目的 DevFlow 字段在 `.claude/settings.json(.local)`。**读取只认 `.devflow/`，不再回退 `.claude/`**——升级后未迁移的项目读不到配置。迁移方式（任选其一）：
- 运行 `scripts/migrate-config.sh`（搬运 DevFlow 字段到 `.devflow/`，密钥进 `settings.local.json`）
- 重新运行 `/req:init --reinit` 或 `/req:branch init`

> SessionStart hook 检测到 `.claude/` 存在 DevFlow 字段但 `.devflow/` 缺失时，会打印迁移提示。

---

## 存储路径解析

```
需求存储（唯一源，在 primary 仓库）: <requirementsDir>/   默认 docs/requirements/
modules/      # 模块文档
specs/        # 规范文档（数据类型、接口契约等，跨仓库共享）
active/       # 进行中需求
completed/    # 已完成需求
INDEX.md      # 索引
```

**无全局缓存**：需求文档只存在于 primary 仓库的 `requirementsDir`，是唯一事实源。readonly 仓库不复制、不缓存，直接读 primary 仓库目录。

**解析规则**：
1. 读 `.devflow/settings.json` 的 `requirementRole` / `requirementsDir` / `requirementSource`，再用 `.devflow/settings.local.json` 覆盖同名字段
2. `primary`：需求根目录 = 本仓 `requirementsDir`（省略时默认 `docs/requirements/`；下文 `docs/requirements/` 均指此解析结果）
3. `readonly`：需求根目录 = `requirementSource.path` 指向的主仓根 + 该主仓的 `requirementsDir`；未配置 `requirementSource` 时报错，提示先 `/req:use <primary-repo-path>` 绑定

**仓库角色**（`requirementRole` 字段）：

| 角色 | 值 | 说明 |
|------|------|------|
| 主仓库 | `primary` | 拥有本地 `requirementsDir`，可读写，写入即生效 |
| 只读仓库 | `readonly` | 无本地需求目录，经 `requirementSource.path` 直接读主仓，不可创建/编辑/变更状态 |

**读取策略**：
- `primary`：读写本仓 `requirementsDir`
- `readonly`：直接读 `requirementSource.path` 下的需求目录（实时，无副本）

## 写入规则（无缓存，主仓唯一源）

**核心原则**：需求文档**只有一份**，位于 primary 仓库的 `requirementsDir`。不存在缓存层，因此没有同步动作。

- **primary**：所有修改需求的命令（new、new-quick、edit、review、dev、test、done、upgrade、modules/specs/prd 编辑）直接写本仓 `requirementsDir`，写完即生效，**无任何后续同步或 cp**。
- **readonly**：禁止一切写操作（创建、编辑、状态更新）。仅读取 `requirementSource.path`。

> **历史说明（v2.x → v3 breaking change）**：v2.x 曾用 `~/.claude-requirements/` 全局缓存 + PostToolUse `sync-cache.sh` 单向同步，readonly 从缓存读。v3 起**移除缓存**：readonly 改为经 `requirementSource.path` 直读主仓，`sync-cache.sh` 不再注册。命令内**不应再有任何缓存读写、cp 到缓存、或全局索引（`~/.claude-requirements/index.json`）操作**。

## 需求编号生成

扫描 active/ 和 completed/ 目录，找最大编号 +1，格式 `REQ-XXX`

## 元信息字段

| 字段 | 说明 |
|------|------|
| 编号 | REQ-XXX |
| 类型 | 后端/前端/全栈 |
| 状态 | 当前状态 |
| 模块 | 所属模块 |
| 关联需求 | 前后端对应需求 |
| branch | 开发分支名（/req:dev 首次进入时生成） |
| issue | 关联的 Git 平台 issue 编号（如 `#123`），无关联为 `-`。`/req:new --from-issue` 自动填充，`/req:done` 读取后可选关闭 |

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
