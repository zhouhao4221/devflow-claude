---
name: new-quick
description: 快速修复 - 创建小bug修复或小功能的快速需求
---

# 快速修复需求

> **Audience:** Engineer

用于小bug修复或小功能开发，简化流程：方案确认即可开发。

## 命令格式

```
/req:new-quick [标题]
```

---

## 简化生命周期

```
草稿 → ✅ 方案确认 → 开发中 → 已完成
```

（跳过：评审、测试阶段）

---

## 执行流程

### 0. 解析存储路径

本地主存储为 `docs/requirements/active/` 和 `docs/requirements/completed/`，确保目录存在。读取 `settings.local.json` 的 `requirementProject`；有绑定则同时准备缓存路径 `<requirementSource.path>/<requirementsDir>/`。

### 1. 生成需求编号

格式：`QUICK-XXX`（三位数字，如 QUICK-001）

扫描本地 active/completed 和缓存 active/completed 中所有 QUICK-XXX 文件，取两边最大编号中的较大值，加 1 生成新编号。

### 1.5 （可选）从 issue 导入

若命令带 `--from-issue=#N`，按 _issue.md 的 Issue 拉取规范（见附录：_issue.md） 拉取 issue：
- issue 标题作为默认标题
- issue 正文作为「问题/需求描述」的初始输入
- 元信息 `issue` 字段填 `#N`（否则填 `-`）

`repoType` 为 `other` 或未配置时提示并退出。

### 2. 收集基本信息

如果未提供标题，询问用户：

**需要收集的信息：**
- 问题/需求描述（必填）
- 类型：bug修复 / 小功能 / 优化（默认：bug修复）
- 优先级（P1/P2/P3，默认 P2）
- **模块**：自动设为「快速修复」（无需用户选择）

### 3. 读取模板

**必须先读取快速修复模板**，确定文档结构：

```
优先级：
1. 本地模板：docs/requirements/templates/quick-template.md
2. 插件模板：<plugin-path>/templates/quick-template.md
```

**两个路径都不存在时，终止操作**：
```
❌ 未找到快速修复模板文件

请执行 /req:update-template quick 恢复模板
```

读取后解析模板的完整章节结构，后续创建文档**必须严格保留模板中的所有章节、层级和格式**。

### 4. 创建简化文档

**步骤 4.1：严格按模板结构创建**

使用快速需求模板创建文件：`$LOCAL_ACTIVE/QUICK-XXX-标题.md`

**格式约束（强制）：**
- 章节标题、层级必须与模板完全一致
- 不得新增、删除、合并或重命名模板中的章节
- 未填写的章节保留模板中的占位文本，不得删除
- 表格结构（列名、列数）必须与模板一致

**初始化内容：**
- 填充元信息（编号、标题、类型、状态=草稿、日期）
- **模块字段设为「快速修复」**
- `issue` 字段：从 issue 导入时填 `#N`，否则填 `-`
- 生命周期勾选「草稿」

**步骤 4.2：同步到主仓需求目录**

若已绑定项目，将新建文档同步复制到 `$CACHE_ACTIVE/`。

### 5. 快速分析并生成方案

AI 分析问题/需求，生成实现方案：

#### 4.1 问题分析（如果是bug）
- 分析错误信息/现象
- 定位问题根因
- 确定影响范围

#### 4.2 代码定位
- 搜索相关代码
- 确定涉及的文件
- 理解现有实现

#### 4.3 生成实现方案
- 具体的改动说明
- 涉及文件清单
- 预估改动量（小/中）

### 6. 方案确认

显示方案摘要，等待用户确认：

```
快速需求：QUICK-001 修复xxx问题

类型：bug修复
优先级：P2

问题分析：
  [问题根因分析]

实现方案：
  [具体实现方案]

涉及文件：
  - internal/xxx/biz/xxx.go（修改）
  - internal/xxx/store/xxx.go（修改）

改动量：小（约 20 行）

```

### 7. 方案确认检查

在确认前检查：
- [ ] 改动范围可控（建议 <5 个文件）
- [ ] 不涉及数据库结构变更
- [ ] 不影响其他核心功能
- [ ] 可快速验证

**如果任一不满足**，建议用户升级为正式需求：

```
⚠️ 此改动可能超出快速修复范围：
- 涉及 8 个文件
- 需要修改数据库表结构

建议使用正式需求流程：/req:new [标题]

```

### 8. 确认后进入开发

用户确认后：

1. 更新状态为「方案确认」→「开发中」
2. 更新需求文档（先本地，后缓存）
3. 使用 TodoWrite 生成开发任务
4. 按照 dev-guide 技能引导开发

```
✅ 方案已确认，开始开发

开发任务：
1. [ ] 修改 internal/xxx/biz/xxx.go
2. [ ] 修改 internal/xxx/store/xxx.go
3. [ ] 自测验证

开始执行第一个任务...
```

### 9. 开发完成

完成所有改动后：

1. 更新状态为「已完成」
2. 移动文档到 completed 目录
3. 同步缓存

```
快速修复完成！

QUICK-001 修复xxx问题
状态：已完成
改动文件：2 个
耗时：约 15 分钟

文档归档：docs/requirements/completed/QUICK-001-修复xxx问题.md

下一步（可选）：
- 代码审查：/code-reviewer
- 提交代码：git add . && git commit
```

---

## 适用场景

### 适合快速修复的情况

- 简单的 bug 修复（逻辑错误、空指针等）
- 小功能增强（新增字段、调整参数等）
- 代码优化（性能优化、代码整理等）
- UI 微调（文案修改、样式调整等）

### 不适合快速修复的情况

建议使用 `/req:new` 创建正式需求：

- 涉及数据库表结构变更
- 涉及多个模块的联动修改
- 需要新增 API 接口
- 影响核心业务流程
- 需要多人协作或评审

---

## 与正式需求的区别

| 对比项 | 快速修复 (QUICK) | 正式需求 (REQ) |
|-------|-----------------|---------------|
| 编号格式 | QUICK-XXX | REQ-XXX |
| 生命周期 | 4 阶段 | 6 阶段 |
| 评审环节 | 无 | 有 |
| 测试环节 | 自测 | 完整测试 |
| 文档详细度 | 简化 | 完整 |
| 适用场景 | 小改动 | 中大型需求 |

---

## 用户输入

$ARGUMENTS

---

# 附录（自动内联的共享约定）

> 以下内容由 command 引用的共享子文件自动内联，供不支持 slash 的 Claude 客户端离线阅读。请勿手动编辑本文件——改动应在对应 command 进行。

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
