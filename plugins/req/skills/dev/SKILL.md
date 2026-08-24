---
name: dev
description: 需求开发 - 启动或继续开发
---

# 需求开发

启动或继续需求开发，先生成实现方案，确认后逐步实现。

> **Audience:** Engineer
> 存储路径规则见 _storage.md（见附录：_storage.md）

## 命令格式

```
/req:dev [REQ-XXX] [--reset]
```

- 省略编号时自动选择「评审通过」或「开发中」的需求
- `--reset` 强制从头开始

---

## 执行流程

### 1. 选择需求

- 指定编号 → 使用该需求
- 未指定 → 查找可开发需求（状态为评审通过/开发中）
- 多个候选 → 交互式选择（列出编号列表，用户输入编号）

### 2. 前置检查（严格执行）

**根据需求类型区分检查规则**：

#### 正式需求 (REQ-XXX) - 必须通过评审

| 当前状态 | 处理方式 |
|---------|---------|
| 草稿 | 拒绝开发，提示：`需求尚未评审，请先执行 /req:review 提交评审` |
| 待评审 | 拒绝开发，提示：`需求正在评审中，请等待评审通过后再开发` |
| 评审驳回 | 拒绝开发，提示：`需求评审未通过，请先修改后重新提审：/req:edit → /req:review` |
| 评审通过 | 允许开发 |
| 开发中 | 允许继续开发 |
| 测试中 | 允许开发（可能是修复测试问题） |
| 已完成 | **readonly 仓库**：允许开发（需求在主仓库已完成，只读仓库可基于其开发）；**primary 仓库**：警告提示：`需求已完成，如需修改请创建新需求` |

#### 快速修复 (QUICK-XXX) - 跳过评审

| 当前状态 | 处理方式 |
|---------|---------|
| 草稿 | 允许开发（方案确认后直接开发） |
| 方案确认 | 允许开发 |
| 开发中 | 允许继续开发 |
| 已完成 | **readonly 仓库**：允许开发；**primary 仓库**：警告提示：`需求已完成，如需修改请创建新需求` |

**重要**：正式需求 (REQ) 未通过评审**不能**开始开发；快速修复 (QUICK) 跳过评审环节；readonly 仓库允许开发已完成的需求。

### 2.5 分支管理

> 仅 `primary` 仓库执行，`readonly` 仓库跳过此步骤。
> 分支策略配置见 _branch.md（见附录：_branch.md）。

#### 工作区检查

执行 `git status --porcelain`，若有未提交的改动：
- 列出改动文件，提示用户先 commit 或 stash
- **终止流程**，不得静默跳过

#### 读取分支策略

```python
strategy = read_settings("branchStrategy")

if strategy:
    MAIN_BRANCH = strategy["mainBranch"]
    BRANCH_FROM = strategy["branchFrom"]  # 功能分支的拉取基准
    FEATURE_PREFIX = strategy["featurePrefix"]
    FIX_PREFIX = strategy["fixPrefix"]
else:
    # 未配置策略，使用默认行为
    MAIN_BRANCH = detect_main_branch()  # 自动检测
    BRANCH_FROM = MAIN_BRANCH
    FEATURE_PREFIX = "feat/"
    FIX_PREFIX = "fix/"
```

**自动检测主分支**（未配置策略时的回退逻辑）：
1. `git symbolic-ref refs/remotes/origin/HEAD` → 提取分支名
2. 失败 → `git rev-parse --verify origin/main`，再失败 → `origin/master`
3. 都失败 → 回退 `main`

#### 分支处理

**情况 A：需求文档元信息 `branch` 字段有值（非 `-`）**

1. 读取 `branch` 字段值，按逗号拆分得到分支列表
2. **单个分支**：直接 checkout
   - 本地存在 → `git checkout <branch>`
   - 仅远程存在 → `git checkout -b <branch> origin/<branch>`
   - 都不存在 → `git checkout -b <branch> <BRANCH_FROM>`
3. **多个分支**：展示列表，让用户选择切入哪一个：
   ```
   此需求有多个开发分支，请选择：
   1. feat/REQ-025-backend
   2. feat/REQ-025-frontend
   （输入编号，或输入新分支名新建）
   ```
   选择后按单分支逻辑处理

**情况 B：`branch` 字段为 `-` 或缺失（首次进入）**

1. AI 根据需求标题生成英文 slug（lowercase kebab-case，最多 5 词，仅 ASCII）
2. 拼接分支名（使用策略配置的前缀）：
   - REQ-XXX → `<FEATURE_PREFIX>REQ-XXX-<slug>`（默认 `feat/REQ-XXX-<slug>`）
   - QUICK-XXX → `<FIX_PREFIX>QUICK-XXX-<slug>`（默认 `fix/QUICK-XXX-<slug>`）
3. 若需求文档元信息 `issue` 字段非 `-` 且非空（如 `#12`），在分支名末尾追加 `-i<N>`（如 `-i12`），参见 _issue.md 的 Issue 与分支关联（见附录：_issue.md）
4. 展示分支名供用户确认（可修改）：
   ```
   将创建开发分支：feat/REQ-001-user-points-i12
   基于分支：main（来源：branchStrategy.branchFrom）
   ```
4. 用户确认后：
   - `git checkout -b <branch> <BRANCH_FROM>`
   - 将分支名写入需求文档元信息的 `branch` 字段

### 3. 加载上下文

读取需求文档的需求定义章节：需求描述、功能清单、业务规则、使用场景、接口需求、测试要点

### 4. 生成实现方案（Plan Mode）

> **前置**：读取项目 CLAUDE.md 的「项目架构」章节，获取分层架构、目录结构、开发规范。
> 缺少时发出警告（见 _claude-md.md（见附录：_claude-md.md））。

进入 Plan Mode，基于需求文档和 CLAUDE.md 架构信息生成实现方案，填充「十一、实现方案」章节：

> **定位现有代码先委派**：方案需要参照的既有实现（相似模块、要改动的调用方、现有数据模型/接口）先派 `code-scout` subagent 定位（prompt 给：功能清单关键词、接口路径/实体名、architecture.md 的分层目录摘要），主会话只按其返回的 `file:line` 精读高/中相关片段，不自己全库 grep。候选路径已明确且 ≤ 3 个文件时可直接 Read。规则见 `_delegate.md`（见附录：_delegate.md）。

- **11.1 数据模型**：新增/修改的表、字段说明、实体关系
- **11.2 API 设计**：基于第五章接口需求 + 项目代码 + CLAUDE.md API 风格，生成具体接口方案（路径、方法、请求/响应字段、错误码）
- **11.3 文件改动清单**：按 CLAUDE.md 分层架构表的顺序列出需要新增/修改的文件
- **11.4 实现步骤**：按 CLAUDE.md 分层架构的顺序拆解开发步骤

如果需求文档「十一、实现方案」已有完整内容（非占位文本），直接展示并请用户确认。

### 5. 更新状态和实现方案

> 仅 `primary` 仓库执行，`readonly` 仓库跳过此步骤（不修改需求文档）。

1. 首次进入 → 状态改为「开发中」
2. 将实现方案写回需求文档的「十一、实现方案」章节（11.1 数据模型、11.2 API 设计、11.3 文件改动清单、11.4 实现步骤）

### 6. 显示开发概览

```
REQ-001 部门渠道关联

进度：2/6 功能点已完成
功能清单：
- [x] Model/Store 层
- [x] 渠道范围校验
- [ ] 获取可选渠道接口 ← 当前
- [ ] 订单数据过滤
...
```

### 7. 生成任务

根据实现步骤生成 TodoWrite 任务列表

### 8. 逐步实现

按 CLAUDE.md 分层架构表定义的顺序逐层开发。

实时检查（根据 CLAUDE.md「开发规范」章节）：
- 文件命名规范
- CLAUDE.md 中定义的其他规范项

### 9. 开发中修改需求文档

> 仅 `primary` 仓库执行，`readonly` 仓库跳过此步骤（不修改需求文档）。

开发过程中用户可能需要修改需求文档，支持两种方式：

**方式一：用户主动提出**

用户在开发过程中说"更新一下功能清单"、"业务规则要加一条"、"接口需求有变化"等，直接修改对应章节。

**方式二：AI 发现偏差时主动提示**

开发过程中 AI 发现实际情况与需求文档不一致时，主动提示用户：

| 发现场景 | 提示内容 |
|---------|---------|
| 代码中发现需求未描述的业务规则 | `发现新的业务规则：xxx，是否补充到第三章？` |
| 实现方案需要新增功能点 | `实现中需要额外功能点：xxx，是否补充到第二章？` |
| 接口设计与需求描述不符 | `接口需求有调整：xxx，是否更新第五章？` |
| 实现步骤需要调整 | 直接更新第十一章，无需确认 |

**修改规则**：
- **一~六章（需求定义）**：修改后提示用户确认，并在第八章变更记录中追加一条
- **十章（实现方案）**：开发过程中可直接更新，不需要变更记录
- **格式约束不变**：修改仍须遵循模板结构，不得增删章节

### 10. 进度更新

每完成一步：更新任务状态（TodoWrite）。`primary` 仓库同时更新需求文档 checkbox，`readonly` 仓库仅更新任务状态，不修改需求文档。

### 11. 开发完成

```
开发完成！
- 功能点：6/6
- 新增/修改文件统计

下一步：
- /req:pr REQ-001 - 创建 PR（根据仓库类型自动创建或提示命令）
- /req:test REQ-001 - 进入测试
- /req:commit - 提交代码
```

> 如果配置了 `branchStrategy.repoType`（gitea/github），会提示可以创建 PR。
> 未配置时不显示 PR 相关提示。

---

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

## 附录：_branch.md

# 公共逻辑参考 - 分支策略

> 此文档定义分支策略配置（`branchStrategy`）的结构、预设和读取规则。
>
> 同伴文档（同目录，按需 Read；此处不用链接，避免生成器传递内联）：`_storage.md`、`_issue.md`、`_template.md`、`_granularity.md`、`_claude-md.md`。

## 分支策略配置

分支策略存储在 `.devflow/settings.json` 的 `branchStrategy` 字段中，通过 `/req:branch init` 初始化。`giteaToken` 敏感字段单独存入 `.devflow/settings.local.json`（不纳入 git）。

### 配置结构

`settings.json`（团队共享，纳入 git）：
```jsonc
{
  "branchStrategy": {
    "model": "github-flow",       // github-flow | git-flow | trunk-based
    "repoType": "github",         // github | gitea | other（仓库托管类型）
    "giteaUrl": null,             // Gitea 实例地址（repoType=gitea 时必填，如 https://git.example.com）
    "mainBranch": "main",         // 生产分支
    "developBranch": null,        // git-flow 模式下的开发分支
    "featurePrefix": "feat/",     // REQ-XXX 分支前缀
    "fixPrefix": "fix/",          // QUICK-XXX 分支前缀
    "hotfixPrefix": "hotfix/",    // 紧急修复前缀
    "branchFrom": "main",         // 功能/修复分支的拉取基准
    "mergeTarget": "main",        // 默认合并目标
    "mergeMethod": "merge",       // 合并方式：merge | squash | rebase
    "deleteBranchAfterMerge": true
  }
}
```

`settings.local.json`（本地私有，禁止提交）：
```jsonc
{
  "giteaToken": null             // Gitea API Token（tea 未配置时的 curl 回退凭据）
}
```

### 三种策略预设

| 配置项 | GitHub Flow | Git Flow | Trunk-Based |
|--------|------------|----------|-------------|
| branchFrom | main | develop | main |
| mergeTarget | main | develop | main |
| developBranch | null | develop | null |
| hotfix 合并目标 | main | main + develop | main |

### 读取规则

1. 先读 `.devflow/settings.json` 的 `branchStrategy`，再用 `.devflow/settings.local.json` 中同名字段覆盖（`giteaToken` 以 local 为准）
2. **有配置** → 使用配置值
3. **无配置** → 使用默认行为（`feat/`、`fix/` 前缀，自动检测主分支）

### 各命令的策略消费

| 命令 | 读取的配置 | 用途 |
|------|-----------|------|
| `/req:dev` | `branchFrom`、`featurePrefix`、`fixPrefix` | 创建分支时的基准和前缀 |
| `/req:commit` | `mainBranch`、`developBranch` | 检查当前分支是否合规 |
| `/req:done` | `mergeTarget`、`deleteBranchAfterMerge`、`repoType`、`giteaUrl` | 合并提醒、PR 创建（Gitea）|
| `/req:branch hotfix` | `mainBranch`、`hotfixPrefix` | 从主分支创建紧急修复 |
| `/req:branch status` | `repoType` | 显示仓库托管类型 |

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

## 附录：_claude-md.md

# 公共逻辑参考 - CLAUDE.md 架构检查

> 此文档定义命令对项目 CLAUDE.md「项目架构」章节的依赖检查规则。
>
> 同伴文档（同目录，按需 Read；此处不用链接，避免生成器传递内联）：`_storage.md`、`_branch.md`、`_issue.md`、`_template.md`、`_granularity.md`。

## CLAUDE.md 架构检查

### 为什么需要

插件不硬编码任何项目架构细节（如分层顺序、目录结构、命名规范）。这些信息由项目自己的 CLAUDE.md 提供。dev-guide、test-guide 等 skill 读取 CLAUDE.md 后适配引导。

### 检查时机

以下命令执行前检查 CLAUDE.md 是否包含架构信息：

| 命令 | 依赖的架构信息 | 缺失时影响 |
|------|--------------|-----------|
| `/req:dev` | 分层架构、目录结构 | 无法生成准确的实现方案和文件清单 |
| `/req:test`、`/req:test_new` | 测试规范、测试目录 | 无法定位测试文件和生成测试代码 |
| `/req:new`（后端/全栈类型） | API 风格 | 无法生成准确的接口需求章节 |

### 检查规则

```python
claude_md_path = "CLAUDE.md"  # 项目根目录
architecture_keywords = [
    "分层架构", "目录结构", "技术栈", "项目架构",
    "Architecture", "Tech Stack", "Project Structure"
]

if os.path.exists(claude_md_path):
    content = read_file(claude_md_path)
    has_architecture = any(kw in content for kw in architecture_keywords)
else:
    has_architecture = False
```

### 缺失时的提醒（非阻断，仅警告）

```
⚠️ CLAUDE.md 中未检测到项目架构描述

   /req:dev 需要架构信息来生成实现方案（分层顺序、目录结构、开发规范）
   /req:test 需要测试规范来定位测试文件和生成测试代码

   添加方式：
   - /req:init <project> --reinit  交互式生成架构片段
   - 手动在 CLAUDE.md 中添加「项目架构」章节

   继续执行，但生成的方案可能不够准确。
```

### 架构片段模板

插件提供预置模板供用户选择（存放在 `templates/claude-md-snippets/`）：

| 模板 | 文件 | 适用场景 |
|------|------|---------|
| Go 后端 | `go-backend.md` | Gin + GORM 分层架构 |
| Java 后端 | `java-backend.md` | Spring Boot 分层架构 |
| 前端 React | `frontend-react.md` | React/Next.js + TypeScript |
| 通用 | `generic.md` | 空白模板，手动填写 |

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
