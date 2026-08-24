---
name: issue
description: Issue 工作流 - 创建/编辑/关闭/列表/查看/评论 issue
---

# Issue 工作流

统一管理 GitHub / Gitea issue 的全生命周期：创建、编辑、关闭、重开、列表、查看、评论。

> 不受仓库角色限制，readonly 也可执行。不触发缓存同步。
>
> **CLI 优先级**：GitHub 走 `gh`；Gitea 按 `_gitea_cli.md`（见附录：_gitea_cli.md） 检测 `tea`，可用即走 `tea`，否则回退 curl。`tea` 不支持的操作（评论列表、标签增删等）始终走 curl。

---

## 子命令路由

| 参数 | 功能 |
|------|------|
| `new` | 创建 issue |
| `edit` | 修改字段 |
| `close` | 关闭（可附留言） |
| `reopen` | 重开 |
| `list` | 列出 |
| `show` | 查看详情和评论 |
| `comment` | 添加或列出评论 |
| 无 / `help` | 打印摘要并终止 |

issue 编号支持 `#42` 和 `42` 两种写法。所有子命令都先执行前置检查。

---

## §1 前置检查

读取 `.claude/settings.local.json` 的 `branchStrategy`：

| repoType | 要求 | 失败时 |
|---------|------|-------|
| `gitea` | `giteaUrl` + `giteaToken` 非空；检测 `tea` 可用性 | 提示执行 `/req:branch init` 后终止 |
| `github` | `gh` CLI 已安装 | 提示安装 gh 后终止 |
| `other` / 未配置 | 无 | 写操作输出手动提示；list/show 报错 |

OWNER/REPO 从 `git remote get-url origin` 解析，支持 SSH 和 HTTPS 格式，见 _issue.md（见附录：_issue.md）。

---

## §2 共用行为

### 2.1 关联需求

写操作可自动附需求上下文。`--req=REQ-XXX` 显式指定，未指定时从当前分支名提取（匹配 `REQ-\d+` / `QUICK-\d+`）。命中后读需求文档，提取元信息（标题/类型/模块/状态）和功能清单首段作摘要。

### 2.2 标签匹配

**禁止硬编码中英文对照表**，始终从仓库拉取真实 labels 再匹配。

匹配顺序：完全匹配（忽略大小写）→ 去空格/连字符/下划线后匹配 → 子串包含。

无匹配时询问是否在仓库创建该标签；用户拒绝则跳过，不终止。

### 2.3 指派人解析

从仓库协作者列表匹配，匹配策略同 §2.2。`@me` 自动解析为当前登录用户（GitHub 原生支持，Gitea 需先 `GET /user`）。无匹配时跳过，不终止。

### 2.4 JSON 安全

**禁止字符串拼接构造 JSON**，含引号、换行、反斜杠的文本必须用 `python3 -c 'import json,sys; print(json.dumps(sys.stdin.read()))'` 或 `jq -Rs` 转义后再传入请求体。

### 2.5 错误处理

| 错误 | 提示 |
|------|------|
| 401 / 403 | 鉴权失败，检查 giteaToken 或 gh auth status |
| 404 | Issue 不存在或仓库路径错误 |
| 422 | 回显 API message 字段，标出不合法字段 |
| 423 locked | Issue 已锁定，无法评论/编辑 |
| curl 非 0 | 请求失败，检查网络后重试 |

### 2.6 `--auto` 模式

检测 `.claude/.req-auto` 且 mtime < 10 分钟时跳过交互确认。`new` 强制预览，不受影响。

---

## §3 new

```
/req:issue new <标题> [--body=] [--labels=a,b] [--assignees=u1,u2] [--req=REQ-XXX]
```

**正文生成**：有 `--body` 直接用；无则 AI 生成含「问题描述/复现步骤/预期行为/实际行为/环境信息」的结构化模板，环境信息从 `git branch --show-current` 和 `git rev-parse --short HEAD` 取值。关联需求时在末尾用 `---` 分隔附加需求上下文。

**防误关闭**：正文含 `closes #N` / `fixes #N` 时警告，确认后再提交。

**强制预览**，不受 `--auto` 影响：

```
Issue 草稿：
  仓库：owner/repo (gitea)
  标题：登录超时后 token 未清除
  标签：bug, authentication
  指派：@haiqing
  关联：REQ-001

  正文（前 10 行）：...

  是否提交？(y/n/e - 编辑某字段)
```

`e` 可选择修改字段，改完回到预览。

成功输出：

```
✅ Issue 已创建
  <url>
  #170 登录超时后 token 未清除

/req:fix --from-issue=#170   创建修复
/req:new --from-issue=#170   创建正式需求
```

---

## §4 edit

```
/req:issue edit #N [--title=] [--body=] [--add-labels=] [--remove-labels=] [--assignees=]
```

无字段参数时展示当前状态并提示可用字段，不修改。

**Gitea 限制**：labels 必须走独立端点（`POST /labels` 新增、`DELETE /labels/{id}` 逐个删除），不能通过 PATCH body 修改。title/body/assignees 走 PATCH。

预览变更后提交，`--auto` 跳过预览。

---

## §5 close

```
/req:issue close #N [--comment=<留言>] [--reason=completed|not_planned]
```

**Gitea 执行顺序**：先发评论再改状态——评论失败不阻止关闭，关闭失败时评论已留痕。

**Gitea 不支持 `--reason`**，首次遇到时静默忽略并提示一次（GitHub 专属字段）。

---

## §6 reopen

```
/req:issue reopen #N
```

无预览，直接执行。

---

## §7 list

```
/req:issue list [--state=open|closed|all] [--labels=] [--assignee=] [--limit=20] [--page=1]
```

**Gitea 注意**：`type=issues` 在部分版本未完全过滤 PR，需客户端二次过滤 `pull_request != null` 的条目。limit 上限 50。

输出格式：

```
Open issues @owner/repo（第 1 页 / 20 条）

  #    状态   标题                          标签       指派      更新
  
  170  open   登录超时后 token 未清除        bug        @haiqing  2h
  165  open   导出 Excel 中文乱码            bug, 紧急  -         1d

/req:issue list --page=2
```

---

## §8 show

```
/req:issue show #N
```

拉取 issue 主体和全部评论，渲染格式：

```
Issue #170 登录超时后 token 未清除
  状态：open  作者：@haiqing（2026-04-15 14:32）
  标签：bug   指派：@haiqing

正文 
...

评论（共 3 条）
[1] @alice（15:01）  我能复现。
[2] @haiqing（16:22）已定位到 src/interceptors/request.ts:45

/req:issue comment 170 <文本>
```

---

## §9 comment

```
/req:issue comment #N <评论文本>
/req:issue comment #N --list
```

`--list` 仅渲染评论列表，不显示 issue 主体。

add 模式：关联需求时评论末尾附需求摘要（用 `---` 分隔）。预览后提交，`--auto` 跳过预览。

---

## 与其他命令的分工

| 场景 | 命令 |
|------|------|
| 从 issue 派生需求 | `/req:new --from-issue=#N` |
| 从 issue 派生修复 | `/req:fix --from-issue=#N` |
| 从 issue 派生任务 | `/req:do --from-issue=#N` |
| 需求完成时关闭 issue | `/req:done` / `/req:fix` 结束时询问 |
| commit 自动关联 | message 末尾加 `closes #N` |

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
