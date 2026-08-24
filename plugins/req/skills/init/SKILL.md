---
name: init
description: 初始化需求项目 - 创建本地存储和主仓需求目录
---

# 初始化需求项目

初始化需求项目，创建本地存储目录和主仓需求目录，并绑定当前仓库。

> 模板源文件：`plugins/req/templates/`，写入规范：`_storage.md`（见附录：_storage.md），索引格式：[`index-template.md`](../templates/index-template.md)，架构片段：[`claude-md-snippets/`](../templates/claude-md-snippets/)，release 模板：[`release-prompt-template.md`](../templates/release-prompt-template.md)，Prompt 库骨架：[`prompt-snippets/`](../templates/prompt-snippets/)

## 命令格式

```
/req:init <project-name> [--reinit] [--readonly]
```

- `project-name`: 项目名称（kebab-case）
- `--reinit`: 补充缺失内容，不覆盖已有文件
- `--readonly`: 只读仓库角色，不创建本地需求目录和主仓需求目录

---

## 执行流程

### 1. 参数解析

仓库角色优先级：`--readonly` 参数 → `.devflow/settings.json` 中已有 `readonly` → 默认 `primary`。

### 2. 创建目录结构

**primary**：`docs/requirements/` 下创建 `active/`、`completed/`、`modules/`、`templates/`

**readonly**：仅 `docs/requirements/templates/`

### 3. 复制模板文件

复制到 `docs/requirements/templates/`（仅当目标不存在时，`--reinit` 保护已有）：
`requirement-template.md`、`quick-template.md`、`prd-template.md`、`module-template.md`

### 4. 生成 PRD（仅 primary）

从 `prd-template.md` 复制，替换 `{{PROJECT_NAME}}`、`{{DATE}}` 变量。

### 5. 创建「快速修复」模块（仅 primary）

`docs/requirements/modules/quick-fix.md` 不存在时，生成含概述、核心功能、业务规则、相关需求、变更记录的模块文档。

### 6. 绑定当前仓库

> 写入规范见 _storage.md（见附录：_storage.md）。无主仓需求目录：需求文档只存在于 primary 仓库的 `requirementsDir`。

在 `.devflow/settings.json` 写入 `requirementProject`、`requirementRole`、`requirementsDir`（合并写入，不覆盖 `branchStrategy` 等既有字段）。

- **primary**：`requirementRole: "primary"`，需求存本仓 `requirementsDir`，写入即生效、无同步、无缓存
- **readonly**：`/req:init --readonly` 仅建本地模板目录、不建需求存储；随后用 `/req:use <primary-repo-path>` 绑定主项目（写 `requirementSource` 到 `.devflow/settings.local.json`）

### 7. 生成架构文件

`docs/prompt/architecture.md` 已存在则跳过。否则扫描项目结构检测技术栈（go.mod → Go · pom.xml/build.gradle → Java · package.json 按依赖判断前后端 · requirements.txt/pyproject.toml → Python · Cargo.toml → Rust · 否则通用），同时扫描目录分层、测试文件位置、代码风格，生成架构文件草稿，用户确认后写入。在 CLAUDE.md 末尾追加仅一行指针引用。

### 8. 创建 Prompt 库骨架（仅当目标文件不存在）

从 `templates/prompt-snippets/` **复制**到 `docs/prompt/`（逐文件检查，已存在则跳过，`--reinit` 保护已有）：
`code-generation.md`、`refactoring.md`、`test-generation.md`、`testing.md`、`error-diagnosis.md`、`pr-review.md`、`requirement-structuring.md`、`prompt-craft.md`。

> 用复制而非现场生成，确保各项目骨架结构一致（统一 5 节：什么时候用 / 必备输入 / 触发方式 / 优质输出标准 / 常见失败模式）。骨架节内容为占位注释，供用户按项目填充；消费命令（`/req:dev`、`/req:do`、`/req:fix`、`/req:review-pr` 等）在运行时按需 Read 对应文件，缺失即降级为通用行为。

### 9. 生成 release.md

`docs/prompt/release.md` 已存在则跳过。不存在时扫描项目（版本号文件、test/build/lint 命令、CI 配置、构建产物目录），生成预填充草稿，用户确认后写入。

### 10. Skills 初始化

创建 `.claude/skills/` 目录，根据项目类型引导创建 Skill：
- **后端**：引导创建 `migration.md`（声明 migration SQL 目录）
- **前端**：提示无需预置
- **自定义**：提示按需创建

---

## 输出要点

成功时输出：目录结构树、已生成文件列表、下一步操作提示（检查架构文件 → 发版配置 → PRD → 分支策略 → 创建需求）。

`--reinit` 标注「已存在」和「新增/补充」的区别。`--readonly` 说明从主仓需求目录只读。

---

## 错误处理

| 场景 | 处理 |
|------|------|
| 未提供项目名 | 提示 `/req:init my-project` |
| 项目名含非法字符 | 仅允许字母、数字、连字符 |
| 本地目录已存在（无 --reinit） | 提示用 `--reinit` 补充 |
| readonly 本地缓存缺失 | 警告不阻塞，继续初始化 |
| 权限不足 | 提示检查目录权限 |

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
