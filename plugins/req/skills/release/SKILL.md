---
name: release
description: 颁布版本 - 合并 SQL、生成回滚、打 tag、创建 Release
---

# 颁布版本

准备发版产物（SQL 合并、回滚脚本、changelog、commit、PR）并**默认创建 draft Release**。加 `--tag` 额外创建 annotated git tag；加 `--no-draft` 直接正式发布。

> **Audience:** Engineer
> readonly 仓库可用。不触发缓存同步。
> CLI 优先：GitHub → `gh`；Gitea → 检测 `tea`，不支持的接口回退 curl。详见 `_gitea_cli.md`（见附录：_gitea_cli.md）。
> 设计原理和边界情况详见 `release-rationale.md`（见附录：release-rationale.md）。
> **发布前置（REQ-003）**：先运行 `python3 scripts/gen-skills.py --check` 校验 skill 与 command 一致；若报漂移，运行 `python3 scripts/gen-skills.py` 重新派生并纳入本次发布。skill 由 command 单源派生，禁止手改。

## 参数

| 参数 | 说明 |
|------|------|
| `<version>` | 可选，如 `v1.2.0`。不传则自动推导（见步骤 2） |
| `--bump=major\|minor\|patch` | 显式 bump 等级，与 `<version>` 互斥 |
| `--from=<ref>` | 起始点，默认上一个 git tag |
| `--to=<ref>` | 结束点，默认 HEAD |
| `--tag` | **额外**创建并推送 annotated git tag（Release 始终创建） |
| `--no-draft` | 创建正式 Release（默认 draft） |
| `--no-release` | 跳过创建平台 Release，仅准备产物和 PR |
| `--main=<branch>` | 临时覆盖 `branchStrategy.mainBranch` |

示例：
- `/req:release`（准备产物 + PR + draft Release，不打 tag）
- `/req:release --tag`（同上 + annotated tag）
- `/req:release --no-draft`（正式 Release，无 tag）
- `/req:release --tag --no-draft`（正式 Release + tag）
- `/req:release v1.2.0`（显式版本 + draft Release）

## 起步分支速查

| 策略 | 必须从此分支运行 | 流程模式 | PR2 回流 |
|------|----------------|---------|---------|
| `git-flow`（develop 起步） | `developBranch` | cross-branch | ❌ 无需（develop 已有准备 commit） |
| `git-flow`（发布分支起步） | `release/*` / `chore/release-*` | release-branch | ✅ release → develop |
| `github-flow` / `trunk-based` | `mainBranch` | direct | ❌ 无需回流 |
| 未配置 | 按当前分支名判断 | 同上规则 | ❌ 无需回流 |

---

## 执行流程

### 步骤 0：角色检查 + 目录配置 + 项目发版规则

**读取项目发版规则**：若 `docs/prompt/release.md` 存在，立即 Read 并提取三个变量（后续步骤使用）：

- `PRE_RELEASE_CHECKS`：「发版前检查」章节的内容，步骤 0.5 执行
- `POST_RELEASE_NOTES`：「发版后步骤」章节的内容，步骤 16 追加到最终报告
- `EXTRA_ASSETS`：「额外附件」章节的 glob 列表，步骤 12 上传时合并进去

文件不存在时三个变量均为空，跳过对应行为，不打印任何提示。

读取 `.claude/settings.local.json` 中的 `requirementRole`：

- **readonly**：
  - 从主仓需求目录 `<requirementSource.path>/<requirementsDir>/` 读取需求文档
  - **禁止修改任何 `docs/requirements/` 下的文件**（包括状态更新、关联信息追加等）
  - SQL 合并（`<MIGRATIONS_DIR>/released/`）和 changelog（`docs/changelogs/`）的写入**不受此限**——这些是版本产物，不是需求文档；目录不存在时自动创建
  - 其余步骤（git commit、PR、tag）照常执行
- **primary / 未配置**：正常读写本地 `docs/requirements/`

**目录变量解析**：

- `CHANGELOG_DIR`：固定为 `docs/changelogs`，不需要配置
- `MIGRATIONS_DIR`：按优先级解析，后续步骤统一使用此变量

| 优先级 | 来源 | 方式 |
|--------|------|------|
| 1 | 项目内配置 | Read `.claude/skills/migration.md`，解析其中的 `MIGRATIONS_DIR` 行 |
| 2 | 自动检测 | 扫描 `db/migrations`、`database/migrations`、`migrations`、`src/migrations`，取第一个存在的 |
| 3 | 兜底默认 | `docs/migrations` |

**「后端项目 + 未配置优先级 1」时**，打印一次警告（非阻塞，继续执行）：

> 后端项目判断依据：存在 `.sql` 文件或 migration 相关目录。

```
⚠️  未找到 .claude/skills/migration.md，当前使用 MIGRATIONS_DIR=<auto-detected or default>
    如需固定路径，创建 .claude/skills/migration.md 并写入：
    - **MIGRATIONS_DIR**: `<路径>`
```

### 步骤 0.5：发版前检查（仅 `PRE_RELEASE_CHECKS` 非空时执行）

逐条执行检查命令，打印每条结果（✅ 通过 / ❌ 失败）。**任意一条失败则硬停止**，不进入后续步骤。

```
发版前检查：
  ✅ npm test
  ❌ npm run build（exit 1）

发版中止。请修复后重新运行。
```

### 步骤 1：参数校验 + 分支判定

1. `<version>` 与 `--bump` 互斥，否则报错退出
2. `create_tag = bool(args.tag)`；`skip_release = bool(args.no_release)`
3. 读 `branchStrategy`：`strategy_model / main_branch / develop_branch / repo_type`
4. **策略合规检查**（无确认，直接阻止）：
   - `git-flow` + 当前在 `main_branch`：自动 `git checkout <develop_branch>`，提示重跑，exit
   - `github-flow` / `trunk-based` + 当前不在 `main_branch`：硬阻止
5. **流程模式**：当前 == `main_branch` → `direct`；`release/*` / `chore/release-*` → `release-branch`；`develop_branch` → `cross-branch`；其他 → 硬阻止
6. **draft 初始化**（`skip_release=false` 时执行）：
   - `is_draft = not args.no_draft`
   - `repoType=other` + draft：询问是否降级 `--no-draft`（**强制交互**）
   - cross/release-branch + `--no-draft`：额外确认（**强制交互**）
   - `repoType=gitea` + draft + `!create_tag`：Gitea draft Release 要求 tag 先存在，但未指定 `--tag`；询问（**强制交互**）：
     - [1] 改用 `--no-draft`：Gitea API 自动从 `target_commitish` 生成 lightweight tag，创建正式 Release
     - [2] 加 `--tag`：额外创建 annotated tag，继续 draft Release
     - [3] 取消

打印：`当前分支 / 策略 / 流程模式 / create_tag / skip_release / is_draft`

### 步骤 2：确定版本号和 git 范围

**基线版本来源**（按优先级，取第一个成功的）：

1. **平台 Release**：查询最新已发布 Release 的 tag
   - GitHub：`gh release list --limit 1 --exclude-drafts --exclude-pre-releases`，取 `Tag` 列
   - Gitea：调用 `/releases?limit=1&draft=false&pre-release=false`，取 `tag_name`
   - 查询失败（网络、未初始化）→ 打印一行警告，降级到来源 2
2. **git tag**：`git tag --sort=-v:refname` 中最新的 semver tag
3. **兜底**：视为首次发版

**范围**：`FROM_REF`（基线 tag，无则仓库首次 commit）→ `TO_REF`（`--to` 或 HEAD）

**版本推导**（未传 `<version>` 时执行）：
- 无基线 → 首发 `v0.1.0`
- 基线 tag 非 X.Y.Z semver → 阻断，提示显式传版本号
- 扫描 `FROM_REF..TO_REF` commits，按优先级 bump：`!:` / `BREAKING CHANGE` → major；`feat:` → minor；`fix:/perf:/refactor:` → patch；仅 chore/docs/style/test/ci → 阻断
- `--bump` 存在时直接用，跳过扫描
- 打印 `基线来源（Release/tag/首次）/ 基线版本 / 推导版本 / 推导依据`，**自动使用推导结果**（如需覆盖请显式传参）

### 步骤 2.5：更新版本号文件

读取 `docs/prompt/release.md` 中的「版本号文件」章节，按其规则更新对应文件并暂存（在步骤 10 的统一 commit 中一起提交）。章节不存在时跳过。

### 步骤 3：扫描候选需求

扫描 `$FROM_REF..$TO_REF` 范围内（不含 merge commit）的 commit subject + body，提取所有 `REQ-XXX` / `QUICK-XXX` 编号（去重）。读取每个需求文档，提取标题/类型/状态/关联 SQL 文件数。
- **primary**：从 `docs/requirements/` 读取
- **readonly**：从 `<requirementSource.path>/<requirementsDir>/` 读取；不存在则跳过该需求，继续纯 commit changelog 流程

### 步骤 4：扫描 migration SQL

扫描 `$MIGRATIONS_DIR`（不含 `released/` 子目录）下的 `.sql` 文件，文件名含 `REQ-XXX` / `QUICK-XXX` 即归属对应需求。

### 步骤 5：自动选择需求

- `已完成` 需求：自动纳入，打印清单
- 其他状态：展示后询问一次 `[y/N]`（本步唯一交互点）
- 无需求：继续纯 commit changelog 流程

### 步骤 6：打印产物预览，自动继续

打印：`flow_mode / draft / create_tag / bump_reason / 将产出的文件 / 分支操作计划 / tag + Release 计划`

自动继续（如需中止请按 Ctrl+C）。

### 步骤 7：合并 SQL（有 SQL 时执行）

输出 `$MIGRATIONS_DIR/released/<version>.sql`，文件头注释含 Release/Date/Range/Includes，每段前加来源注释，按选中顺序排列。

**写入成功后立即 `git rm` 所有已合并的源 SQL 文件**（详见 rationale §10），放入暂存区由后续 commit 统一提交。

### 步骤 8：生成回滚 SQL

输出 `$MIGRATIONS_DIR/released/<version>.rollback.sql`，按倒序排列（后建的先回滚）。对每条 DDL 生成语义相反的回滚语句；INSERT / UPDATE / DELETE / DROP / 复杂 ALTER 无法自动推导的，输出 `-- ⚠️ 需手动补充：<原语句首 80 字>`。记录待补充数量，最终报告中提示。

### 步骤 9：生成 changelog

执行 `/req:changelog` 核心逻辑，写入 `docs/changelogs/<version>.md`（已存在则覆盖）。

### 步骤 10：提交产物 + 推送 + PR

**direct**：暂存所有产物 → commit（消息：`chore(release): prepare <version>`），进入步骤 11。

**cross-branch**：
1. commit（同上）+ push `<develop_branch>`
2. 创建 PR：`<develop_branch>` → `<main_branch>`（复用 `state=open` 的 PR，不复用 merged/closed，详见 rationale §7.3）；`other` → 打印命令后终止
   - Body：需求清单 + changelog 摘要
3. **自动合并 PR**；合并失败（分支保护/CI 未通过）→ 打印 PR URL，等待用户手动合并后回复「继续」（**强制交互**）
4. 切到 `<main_branch>` 并 fast-forward pull（验证 `docs/changelogs/<version>.md` 存在，异常见 rationale §7.4）
5. 继续步骤 11（若 `create_tag`）和步骤 12（若 `!skip_release`）

**release-branch**：同 cross-branch，但 PR1 是 `<release_branch>` → `<main_branch>`，PR2（步骤 14）同样自动合并。

### 步骤 10.9：主分支强制验证（步骤 11/12 前必须通过）

**无论 flow_mode 是 direct / cross-branch / release-branch，执行 tag 或 Release 前必须硬性确认当前在 `main_branch` 上。** 若不在，打印错误（当前分支 / 主分支名 / 手动切换命令），硬停止——不自动切换。

`target_commitish` 后续所有步骤统一使用 `main_branch`，**不使用 develop / release 分支**。

### 步骤 11：创建 Git Tag（仅 `--tag`）

确认当前在 `main_branch`（步骤 10.9 已保证）。`push_tag_first` 决策（详见 rationale §6）：

| 组合 | push_tag_first | 行为 |
|------|---------------|------|
| draft + gitea | true | annotated tag + push（Gitea draft 要求先存在） |
| draft + github | false | 不创建，gh release 懒创建 |
| 正式 + gitea | false | 不创建，API 从 target_commitish 生成 |
| 正式 + github / other | true | annotated tag + push |

### 步骤 12：创建平台 Release（`skip_release=false` 时执行）

Release notes 取 `docs/changelogs/<version>.md`。**`target_commitish` 固定为 `main_branch`（由步骤 10.9 保证），绝不使用 develop / release 分支。**

- **gitea**：解析 remote URL，读 `branchStrategy.giteaToken`，调用 Releases API；body 必须用 `jq --rawfile` 从文件构造（不手工拼接字符串，避免 emoji 编码损坏，详见 rationale §11）；`target_commitish` 固定为 `main_branch`；成功后上传 SQL 资产
- **github**：`gh release create`，带 `--target <main_branch>` 和 changelog 文件，酌情加 `--draft` 和 SQL 附件
- **other**：打印手动命令

已存在（HTTP 409）时打印链接，不重复创建。

### 步骤 13：切回起始分支

切回步骤 0 记录的起始分支。

### 步骤 14：PR2 回流到 `developBranch`（仅 release-branch 模式）

**触发条件**：`flow_mode == "release-branch"`。

**PR2 方向**：`<release_branch>` → `<develop_branch>`

- 标题：`chore(release): backmerge <version> → <develop_branch>`
- Body：说明回流目的（使下次 release 不重复产物）+ tag 已落在 `<main_branch>`
- 等待用户确认（**非阻塞**，可跳过）；跳过时最终报告标记 

### 步骤 15：清理 release 分支（仅 release-branch）

PR2 merged → 删除本地和远程 release 分支（remote ref 不存在视为成功）。PR2 pending 时保留分支。

### 步骤 16：最终报告

**16a 正式 Release（`--no-draft`）**：
```
✅ 版本 <version> 已颁布！
需求清单 / SQL 脚本 / 版本说明
<若 --tag：✅ annotated tag 已推送 | 否则：— 无本地 tag（平台自动生成 lightweight tag）>
<Release URL>
检查回滚 SQL：cat $MIGRATIONS_DIR/released/<version>.rollback.sql
```

**16b draft Release（默认）**：
```
⚠️ DRAFT：<version> 草稿已创建，需手工 Publish
//同上
<若 --tag：gitea: ✅ annotated tag 已推 | github: ⚠️ publish 时生成 | 否则：— 无本地 tag>
<Draft Release URL>（仅作者/管理员可见）
⚠️ 未 publish 前：CI/CD 不触发，release 不可见
放弃：gitea 需删 draft（若有 tag 一并删）；github 只删 draft
```

**16c 跳过 Release（`--no-release`）**：
```
✅ 版本 <version> 产物已就绪！
//同上
<若 --tag：✅ tag 已推送 | 否则：— 无 tag>
— 已跳过（--no-release）
PR: <PR URL>（等待合并到 <main_branch>）
```

**发版后步骤**（`POST_RELEASE_NOTES` 非空，且非 draft 模式时追加）：
```
发版后待办：
  <POST_RELEASE_NOTES 内容逐条列出>
```

---

## 边界情况

完整速查见 rationale §12（见附录：release-rationale.md）：

| 场景 | 处理 |
|------|------|
| feat/fix/hotfix/* 等分支 | 硬阻止 |
| git-flow + 在主分支 | 自动切 develop，提示重跑 |
| github-flow/trunk-based + 非主分支 | 硬阻止 |
| PR 未合并用户中止 | 保留已生成产物，不打 tag |
| 无 candidate 需求 / 全跳过未完成 | 继续纯 commit changelog |
| `--no-draft` 未指定 `--tag` | 正常执行，Release 公开，平台生成 lightweight tag |
| 未指定 `--tag` | 仅跳过步骤 11（annotated tag），Release 照常创建 |
| `--no-release` | 跳过步骤 12，仅准备产物和 PR |
| `repoType=gitea` + draft + 无 `--tag` | 步骤 1 强制交互，选择降级 --no-draft 或补 --tag |
| git-flow + release-branch | 步骤 14 自动创建 PR2：`release分支 → developBranch`，同步准备 commit |
| git-flow + cross-branch | 步骤 14 跳过，develop 已有准备 commit，无需回流（`main → develop` 会产生循环 merge） |
| Gitea draft 422（Release is has no Tag） | 详见 rationale §12 |
| `--draft`（老语法） | 接受但忽略（默认已是 draft） |

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

## 附录：release-rationale.md

# /req:release 设计原理与边界情况

> 本文档是 `release.md` 的伴随文档。记录复杂决策的"为什么"和完整的边界情况查询表。
>
> **正常发版流程不需要读本文档**。AI 在以下情况按需查阅：
> - 用户追问"为什么这样设计"
> - 出错时根据 §6 边界情况速查表定位处理方式
> - 修改 release 命令前需要理解决策依据

---

## 1. 为什么 draft 是默认模式

从 v2 开始 `/req:release` 默认创建 Gitea / GitHub draft release——对外不可见、CI/CD 不触发，需手工在平台点 Publish 才正式发版。

**设计原因**：
- 发布的大部分步骤不可逆（commit、push、tag、平台 Release），人工 gate 让用户最后有机会检查 release notes / 资产文件 / 版本范围
- 与 git-flow cross-branch 流程天然配合——一次 PR gate（merge 到主分支）+ 一次 draft gate（平台 publish），两道闸门都过了才真正对外发版

不想 draft 就加 `--no-draft`。老的 `--draft` 作为冗余别名接受但无效果（向前兼容）。

---

## 2. 为什么不静默降级 `repoType=other` 的 draft

旧版本会在 `repoType=other` 时静默把 `is_draft` 改成 false。这会让用户在"以为创建了 draft，实际已经 push 了 tag 并创建了正式 release"的状态下惊讶。

v3.0.0+ 改为强制交互确认，把"我要放弃 draft 闸门"这个决定变成明确的用户动作，避免发版事故。

---

## 3. 流程模式（cross-branch vs release-branch）选择

| 维度 | cross-branch | release-branch |
|------|-------------|---------------|
| 起步分支 | `developBranch` | `release/<version>` 或 `chore/release-*` |
| PR 数量 | 1（develop → main） | 2（release → main，release → develop 回流） |
| 适用场景 | develop 到 main 的 delta 就是本次要发的全部内容 | develop 上已积累未准备发布的 feature，需要隔离发布内容 |
| tag 落点 | 主分支 HEAD | 主分支 HEAD（PR1 合并后） |

**判断方法**：如果 develop 到 main 的 delta 没有未准备发布的 feature 堆积，cross-branch 更简单；否则必须用 release-branch 隔离要发的部分，否则 tag 会带上未准备发布的代码。

---

## 4. 为什么 git-flow 的主分支不允许 direct 模式

git-flow 的 `mainBranch` 通常设有保护规则。step 8.8 的 `chore(release): prepare` 提交会被直接 push 拒绝，用户被迫手动 reset → 切 develop → cherry-pick → 新 PR → 等合并 → 回主分支 → tag，绕一大圈。

步骤 1（策略合规检查）的守门会把这种"误起步"在最早环节挡下，给出 cross-branch / release-branch 两种推荐路径。

---

## 5. draft 模式行为矩阵详解

| `is_draft` | 最终行为 | 典型触发 | 不可逆程度 |
|----|----|----|----|
| `false` | 本地创建 annotated tag → push tag → 平台正式 Release（对外可见） | `--no-draft` | **最强**，tag + 外部 release 双重不可逆 |
| `true` | 平台 **draft** Release（作者可见，需手工 publish）；Gitea 需先 push tag，GitHub 懒创建 tag | **默认行为** | Gitea 中（需清理 tag + draft）/ GitHub 低（仅删 draft） |

### 5.1 draft 模式下的 tag 行为按 `repoType` 分叉

- **gitea**：Release API 要求 tag 必须先存在（否则返回 `Release is has no Tag`），所以 **draft 模式也会先 push annotated tag**。放弃 draft 时需一并清理 tag：`git push --delete origin <tag> && git tag -d <tag>`
- **github**：`gh release create --draft --target <SHA>` 懒创建 tag（publish 时平台创建 lightweight tag），本地 + 远程都没有 tag，放弃仅需删 draft
- **other**：draft 模式在 step 1.5 已降级为 `--no-draft`，不进入该分叉

### 5.2 危险组合：`is_draft=false` 在 developBranch / release 分支

意味着你正在跳过 draft 闸门直接走 cross-branch / release-branch 发布。是合法但少见的组合，step 1.6 末尾的额外 y/n 就是为它准备的闸门。

常见误操作：原本只是想 dry-check 发版流程却覆盖了 draft 默认。

---

## 6. `push_tag_first` 决策矩阵的四个为什么

矩阵本身见 release.md §9。这里解释每个分支的设计依据。

### 6.1 为什么非 draft + github 要先 push tag

GitHub Release API 在 tag 不存在时会用 `target_commitish` 现场创建 tag。如果 `target_commitish` 缺省为默认分支（可能是 develop），tag 就被打错。先推已存在的 annotated tag，API 直接引用，不再创建。

### 6.2 为什么非 draft + gitea 不 push tag

Gitea Release API 在 `draft=false` 时会从 `target_commitish` 现场生成 lightweight tag，而步骤 12（创建平台 Release）显式把 `target_commitish` 设为 `tag_target`（主分支名），不会打错分支。

本地再 push annotated tag 是**冗余**——会出现"本地 annotated、远程 lightweight"两种类型 tag 同名冲突（或者被 push 覆盖）。省掉这一步既简化流程、又与用户直觉一致（tag 在创建 Release 时一并出现）。

### 6.3 为什么 Gitea 的 draft 模式反而要先 push tag

Gitea Release API 在 `draft=true` 时不会为你创建 tag——必须先存在，否则返回 `422 Release is has no Tag`。

步骤 11（创建 Git Tag）的本地 `git push origin <tag>` 如果失败或未执行，就会触发此错误。排查：`git ls-remote --tags origin | grep <version>` 确认远程是否有 tag；检查 Gitea 对 tag 是否配了保护规则。

这是 Gitea 与 GitHub 的关键差异（GitHub 的 draft release 可以引用未来的 tag，Gitea 不可以）。因此 Gitea 上的 draft 闸门价值比 GitHub 弱一些：放弃 draft 需同时清理 tag。

### 6.4 为什么 GitHub 的 draft 模式不 push tag

1. GitHub Release API / `gh --draft` 允许 tag 在 publish 时才创建——这是 draft 的核心价值
2. draft 的 `target_commitish` 传主分支名（`tag_target`），publish 时 tag 打在该分支最新 HEAD 上。比 SHA 更直观方便，适合 draft 创建后很快 publish 的场景
3. 本地如果先 `git tag -a` 会和平台最终创建的 lightweight tag 类型冲突，push 时还会被拦或产生 divergent 状态——干脆完全不碰本地 tag

---

## 7. 跨分支 / 发布分支流程的设计要点

### 7.1 cross-branch：提交顺序的关键性

必须先完成"提交产物到 develop 并 push"，再创建/复用 PR。这样 PR 的 head 就包含 changelog，合并后主分支就有 changelog，不会出现 step 8.5 步骤 4 的 "changelog 不存在" 错误。

### 7.2 release-branch：为什么 PR1 在前，PR2 在后

先合 PR1 保证 tag 落在干净的 main HEAD 上（只含本次发布内容）；PR2 把 changelog/SQL/回滚脚本回流到 develop，让下次 release 不重复产出这些文件。

顺序颠倒会导致 tag 被 develop 上未准备发布的 feature 污染。

### 7.3 PR 复用的状态过滤

查询 PR 必须过滤 `state=open` 才能复用。`merged`/`closed` 状态的 PR 编号 **绝不能复用**——会出现"复用了已合并 PR 编号但 head 指向旧 commit"的情况，导致主分支拉下来缺 changelog。

### 7.4 PR 合并后主分支验证

`git pull --ff-only` 之后必须验证 `test -f docs/changelogs/<version>.md`。若文件不存在说明 PR 未真正合并或合并的是旧版本。此时：

- **不得**尝试 `git checkout develop -- docs/changelogs/<version>.md` 这种补丁式操作
- **不得**直接 push 主分支
- 警告用户 PR 状态异常，回到创建 PR 步骤重新创建新 PR

---

## 8. 版本号自动推导背景

v3.0.0 前版本号必须由用户手写，容易出错——尤其 minor vs patch 的判断、格式 `v` 前缀一致性。step 2.5 基于最近一个 git tag + 范围内 conventional commits 自动推导下一个 semver，同时保留 `<version>` / `--bump` 两级覆盖路径。

### 8.1 v 前缀规范化规则

- 基线 `v3.0.0` + 用户输入 `3.1.0` → 自动补齐为 `v3.1.0`
- 基线 `3.0.0` + 用户输入 `v3.1.0` → 自动去除为 `3.1.0`
- 首发场景（`base_tag is None`，默认 `has_v_prefix=True`）→ 按 v 前缀规范化

同一仓库不混用两种格式。

### 8.2 仅识别严格 X.Y.Z core semver

不识别 prerelease 后缀（如 `v1.2.0-rc.1`）。带 prerelease 后缀的基线 tag 会被拒绝，需要显式指定版本号或先打一个规范 tag 作为基线。

### 8.3 chore-only 范围拒绝自动发版

若 `base_tag..to_ref` 范围内 commits 只包含 chore/docs/style/test/ci 类型，拒绝自动发版以避免无意义的版本号累积。用户可显式指定 `<version>` 或 `--bump=patch` 强制发版。

---

## 9. 步骤 6 产物预览的存在意义

发布的大部分动作都不可逆（提交、push、tag、平台 Release）。用户必须在实际执行前看清所有将要发生的事——尤其是在 `--no-draft`、`cross-branch` 这些会改变最终行为的条件下，用户的心智模型和命令默认行为常常不一致。明确的预览消除"以为会 X，实际做了 Y"的事故。

预览**必须完整渲染**，但不等待用户 y/n 确认——自动继续执行 step 6+。用户如需中止请按 Ctrl+C。如需覆盖版本号请在命令中显式传参（`/req:release v1.4.0` 或 `--bump=minor`）。

---

## 10. SQL 文件删除的设计

step 6.5 在合并 SQL 后立即 `git rm` 源文件。设计原因：

- 已合并的 SQL 不应保留在 `docs/migrations/` 顶层，否则下次 release 会重复扫描到
- 用 `git rm` 而非 `rm` 是为了把删除放进暂存区，让步骤 10 各分支流程（direct/cross-branch/release-branch）一次性 commit 干净
- 仅删除**被选中并成功合并**的文件，未选中需求的 SQL 保留——给用户"分批发版"的灵活性
- 若 `released/<version>.sql` 写入失败则不得执行，避免源文件丢失

---

## 11. Gitea Release API 的 emoji 处理

body 必须用 `jq --rawfile body <path>` 从文件构造 JSON，**不要手工拼接 JSON 字符串**，否则 emoji（、、等 4 字节 UTF-8）会在 shell 双引号转义过程中退化成 `�` replacement char。

curl 用 `--data-binary @file` 上传，按二进制流，不做换行/编码转换。Header 显式声明 `Content-Type: application/json; charset=utf-8`。

---

## 12. 边界情况速查表

| 场景 | 处理方式 |
|------|---------|
| 当前在 feat/* / fix/* / hotfix/* 等 | **硬阻止**，提示切换到 `mainBranch` / `release/*` / `chore/release-*` / `developBranch` |
| 在 `release/*` / `chore/release-*` | 走 release-branch 流程，双 PR：release→main 先合+打 tag，release→develop 后合回流 |
| 在 `developBranch` | 走 cross-branch 流程，单 PR：develop→main，合并后在主分支打 tag |
| 跨分支流程中 PR 未合并用户中止 | 保留已生成的 SQL/changelog/PR，不打 tag |
| 跨分支流程中主分支 pull 后找不到合并提交 | 警告后重新等待用户确认 |
| release-branch 流程 PR1 未合并用户中止 | 保留已生成的 SQL/changelog/PR1，不打 tag，PR2 也不发 |
| release-branch 流程 PR2 用户选"跳过" | tag 和 Release 已完成，命令直接进入最终报告；PR2 保留等用户手动合并，报告中标记 待合并 |
| 没有 git tag | 从首次提交开始，显示警告 |
| 范围内无 commit | 终止操作 |
| 范围内无候选需求 | 提示后自动继续（仅打 tag + 纯 commit changelog） |
| git 范围内只有未完成需求 | 询问一次是否纳入；全部跳过则继续纯 commit changelog 流程 |
| 选中需求都无 SQL | 跳过 SQL 步骤，仅执行 changelog/tag/release |
| `docs/migrations/released/<version>.sql` 已存在 | Hook 弹确认 |
| `docs/changelogs/<version>.md` 已存在 | Hook 弹确认 |
| git tag 已存在 | 提示已存在，询问是否跳过 tag 步骤继续 |
| Gitea token 缺失 | 跳过 Release，保留 tag |
| gh CLI 缺失 | 输出命令让用户手动执行 |
| `repoType` 未配置 | 仅输出手动命令 |
| 默认 draft 模式 + `repoType == other` | 步骤 1（参数校验）强制交互确认降级为 `--no-draft`（不再静默降级），用户取消则中止 |
| draft 模式 draft 创建成功但 release notes 错误 | 在平台编辑 draft，或删除 draft 后重跑命令（gitea 场景需同时删 tag：`git push --delete origin <version> && git tag -d <version>`；github 场景 draft 一删即清） |
| draft 模式下 draft 创建后用户迟迟未 publish | 命令已终止，责任在用户。建议记在团队 checklist 里，或用 cron 巡检未 publish 的 draft |
| Gitea Release API 返回 `Release is has no Tag`（422） | 仅发生在 **draft + gitea** 场景（此时 `PUSH_TAG_FIRST=true`）。步骤 11（创建 Git Tag）的本地 `git push origin <tag>` 失败或未执行。排查：`git ls-remote --tags origin \| grep <version>` 确认远程是否有 tag；检查 Gitea 对 tag 是否配了保护规则拦截了 push。非 draft + gitea 不会触发此错（API 从 target_commitish 自己生成 tag） |
| `--no-draft` 在受保护主分支 + cross-branch/release-branch 流程 | **按 repoType 分叉**：<br>• **github**：步骤 11 会本地 `git tag -a` + `git push origin <tag>`；若 GitHub 对 tag 配了保护规则，push 会失败。改默认 draft 模式同样 push（draft+github 是 `PUSH_TAG_FIRST=false`，不 push）——**推荐回到默认 draft 以绕开 tag 保护**<br>• **gitea**：步骤 11 **不** push tag（`PUSH_TAG_FIRST=false`），API 在服务器侧创建 lightweight tag。若 Gitea 对 tag 有保护规则，API 会返回权限错误。改回默认 draft 模式**无效**（draft+gitea 反而要 push tag），需先解除 tag 保护或用其他路径<br>• **other**：步骤 11 本地 + push，同 github 处理 |
| 用户传 `--draft`（老语法） | 接受但不报错，冗余别名；`args.draft` 变量不参与逻辑，`is_draft` 只看 `args.no_draft` |
| 未指定 `--tag` | 仅跳过步骤 11（annotated tag），Release（步骤 12）照常创建；最终报告走 §16b（draft）或 §16a（--no-draft） |
