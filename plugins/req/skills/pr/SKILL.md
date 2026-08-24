---
name: pr
description: 创建 PR - 根据仓库类型自动创建 Pull Request
---

# 创建 Pull Request

根据分支策略中的仓库类型，自动推送分支并创建 PR。

> **Audience:** Engineer
> 不受仓库角色限制，readonly 也可执行。不触发缓存同步。
>
> **CLI 优先级**：GitHub 走 `gh pr create`；Gitea 按 `_gitea_cli.md`（见附录：_gitea_cli.md） 检测，可用 `tea` 时走 `tea pulls create --base <target> --head <branch> --title ... --description ...`，否则回退本文 curl 示例。

## 命令格式

```
/req:pr [REQ-XXX] [--title=自定义标题] [--base=目标分支]
```

- 省略编号时根据当前分支名匹配需求
- `--title`、`--base` 覆盖自动值

---

## 执行流程

### 1. 识别需求和分支

- 指定编号 → 读取该需求的 `branch` 字段，按逗号拆分得到分支列表
- 未指定 → `git branch --show-current`，从分支名提取 `REQ-XXX` / `QUICK-XXX`
- 两者都失败 → 提示 `请指定需求编号：/req:pr REQ-XXX` 退出

**多分支处理**：`branch` 字段含多个分支时，为**每个分支各创建一个 PR**，依次执行步骤 2–8：

```
此需求有 2 个开发分支，将分别创建 PR：
  [1/2] feat/REQ-025-backend  → main
  [2/2] feat/REQ-025-frontend → main
```

若只需对当前分支创建 PR，直接运行（不传编号），命令自动匹配当前分支。

### 2. 前置检查

`git status --porcelain` 有未提交改动时，自动串联执行 `/req:commit` 流程（分支检查 + 生成提交信息 + 提交），成功后继续。

### 3. 读取策略配置 + 推导合并目标

读取 `.claude/settings.local.json.branchStrategy`：
- `model`（`git-flow` / `github-flow` / `trunk-based`，缺省 `github-flow`）
- `mainBranch`（缺省 `main`）
- `developBranch`（缺省 `develop`，git-flow 专用）
- `mergeTarget`（兜底值，缺省 `main`）
- `repoType`（缺省 `other`）
- `giteaUrl`、`giteaToken`（仅 gitea 需要）
- `deleteBranchAfterMerge`（缺省 `true`）
- `reviewers`（数组，缺省 `[]`；非空则自动设置审核人，无需确认）

无 `branchStrategy` → 按 `other` 处理，`reviewers` 视为空。

**合并目标推导**（`--base` 可覆盖最终结果）：

```
branch = 当前分支名

if model == "git-flow":
    if branch 以 "hotfix/" 开头:
        targets = [mainBranch, developBranch]   # 步骤 7 双 PR
    elif branch 以 "release/" 或 "chore/release-" 开头:
        targets = [mainBranch]                  # release 合入主线
    else:                                       # feat/ fix/ 等功能分支
        targets = [developBranch]               # 功能合入 develop
elif model in ("github-flow", "trunk-based"):
    targets = [mainBranch]
else:
    targets = [mergeTarget]                     # 兜底
```

`--base` 存在时直接覆盖 `targets = [args.base]`，跳过上述推导。

### 4. 生成 PR 标题和 Body

**标题**（`--title` 覆盖）：
- REQ-XXX → `feat(REQ-XXX): <标题>`
- QUICK-XXX → `fix(QUICK-XXX): <标题>`
- hotfix 分支 → `hotfix: <描述>`

**Body**（Markdown）：
```
## 需求
- 编号 / 标题 / 状态（从需求文档 YAML 元信息读取）

## 功能清单
（从需求文档「二、功能清单」提取）

## 变更文件
（从「十一、实现方案.文件改动清单」提取；无则跳过）
```

### 5. 推送分支

推送当前分支到 origin 并设置上游追踪。

### 6. 按 repoType 创建 PR

#### gitea

1. 解析 `git remote get-url origin` 得到 `OWNER/REPO`（SSH/HTTPS 均支持）
2. `giteaToken` 缺失 → 提示配置方式，给出手动 compare 链接退出
3. 先查 `GET /api/v1/repos/{OWNER}/{REPO}/pulls?state=open&head={OWNER}:{branch}&base={target}` 是否已有 PR；有 → 输出现有 PR 链接，跳到步骤 8
4. 无 → `POST /api/v1/repos/{OWNER}/{REPO}/pulls`，参数 `title/body/head/base`
5. **设置审核人**（`reviewers` 非空时，**不询问**直接执行）：
   - `POST /api/v1/repos/{OWNER}/{REPO}/pulls/{N}/requested_reviewers`，body `{"reviewers": [...]}`
   - tea CLI 无对应子命令，统一走 curl
   - 单个失败（用户名不存在 / 权限不足）不阻塞主流程，输出 ⚠️ 提示后继续

成功输出：
```
✅ PR 已创建
   <url>
已请求审核：@user1, @user2     ← reviewers 非空时输出
/req:review-pr review / merge，或 /req:done 归档
```

#### github

检查 `command -v gh`。可用 → `gh pr create --title "..." --body "..." --base <target>`，`reviewers` 非空时追加 `--reviewer <逗号分隔列表>`（**不询问**直接执行）。不可用 → 提示命令 + 浏览器 compare 链接。

#### other

不创建 PR，输出：
```
分支已推送：<branch> → <target>
合并命令：git checkout <target> && git merge <branch>
```

### 7. 多目标处理

`targets` 包含多个分支时（当前仅 git-flow hotfix 场景），对每个 target 各执行一次步骤 6，输出对应 PR 链接 / 命令。

### 8. 分支清理提示

**auto 模式跳过**：若项目内存在 `.claude/.req-auto` 且 mtime 在 10 分钟内（由 `/req:fix --auto` 等上游命令创建），直接跳过本步骤，不询问也不切分支——PR 刚创建还没合并，此时删本地分支不合理，合并后用 `/req:review-pr merge` 自然处理。

非 auto 模式下，`deleteBranchAfterMerge != false` 时询问：
```
是否切回 <target> 并删除本地分支 <branch>？
```
确认 → 切回 target 并删除本地分支（用 `-d` 而非 `-D`，未合并时会被 git 拒绝）。当前已在目标分支则跳过切换。远程分支不删。

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
