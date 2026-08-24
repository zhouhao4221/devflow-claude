---
name: branch
description: 分支管理 - 配置分支策略、查看分支状态、创建紧急修复
---

# 分支管理

管理项目的 Git 分支策略，与需求流程（dev/commit/done）联动。

> 不受仓库角色限制，readonly 可执行。不触发缓存同步。写入规范见 `_storage.md`（见附录：_storage.md）。

## 命令格式

```
/req:branch [子命令] [参数]
```

| 子命令 | 说明 |
|--------|------|
| (空) | 等同于 `status` |
| `init` | 交互式配置分支策略 |
| `status` | 查看当前策略和分支状态 |
| `hotfix [描述]` | 从主分支创建紧急修复分支 |

---

## init

交互式选择分支策略。`branchStrategy` 写入 `.claude/settings.json`，`giteaToken` 写入 `.claude/settings.local.json`。

### 流程

1. **选择策略模型**：GitHub Flow（推荐）/ Git Flow / Trunk-Based。三种策略的默认配置差异见 `model`、`mainBranch`、`developBranch`、`branchFrom`、`mergeTarget` 等字段。
2. **确认或自定义**：生成默认配置展示，可调整各项参数。
3. **自动检测主分支**：从 `origin/HEAD` 检测，不存在时按序探测 `main`/`master`。与默认值不同时自动更新。
4. **选择仓库类型**：GitHub (`gh` CLI) / Gitea (REST API) / 其他（仅展示命令）。Gitea 需额外输入实例 URL 和 API Token。
5. **配置默认审核人**：逗号分隔的用户名，写入 `reviewers` 数组。留空不设置。`/req:pr` 创建时自动请求审核。
6. **Git Flow 额外步骤**：检查 develop 分支，不存在从 main 创建。
7. **写入配置**：输出策略摘要（模型、仓库类型、分支前缀、合并目标、审核人等）。禁止创建独立的 `branchStrategy.json`。

---

## status

1. 读取配置（未配置时提示执行 `init`）
2. 展示策略信息表
3. 展示当前分支
4. 扫描活跃需求文档，展示分支状态和是否当前
5. 检查分支健康（是否在需求分支、与主分支冲突、是否需 rebase）

---

## hotfix

从主分支创建紧急修复分支。

### 流程

1. 工作区检查（未提交改动则终止）
2. 收集问题描述（必填）
3. 生成分支名 `hotfix/<slug>`（英文翻译，kebab-case，最多 5 词）
4. 基于 `branchStrategy.mainBranch` 创建分支（fetch 后从 main 拉）
5. **Git Flow 额外提醒**：hotfix 完成后需合并到 main 和 develop

---

## 策略对各命令的影响

### `/req:dev` 分支创建
`branchFrom` 决定基准分支，`featurePrefix`/`fixPrefix` 决定分支前缀。

### `/req:commit` 分支检查

| 场景 | 行为 |
|------|------|
| 在 mainBranch 上，有活跃需求 | 警告建议切换 |
| 在 developBranch 上（Git Flow） | 警告应在功能分支 |
| 在需求/hotfix 分支上 | 正常提交 |

### `/req:pr` 审核人
`reviewers` 非空时创建 PR 后自动请求审核（GitHub `gh pr create --reviewer ...`，Gitea `POST /pulls/<N>/requested_reviewers`），不询问用户。

### `/req:done` 合并方式

| 仓库类型 | 行为 |
|---------|------|
| `gitea` | 推送 + API 创建 PR |
| `github` | 提示 `gh pr create` |
| `other` | 展示 `git merge` 命令 |

合并目标：GitHub Flow → `main`，Git Flow → `develop`（hotfix 额外 → main）。

---

## 配置兼容性

未配置策略时保持默认行为（`feat/`/`fix/` 前缀，不做分支检查，通用合并提醒），不会报错。

配置文件：`branchStrategy` 写入 `.claude/settings.json`（团队共享），`giteaToken` 写入 `.claude/settings.local.json`（不提交）。

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
