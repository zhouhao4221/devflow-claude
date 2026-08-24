---
name: prd-edit
description: 编辑 PRD - 修改和完善产品需求文档
---

# 编辑 PRD

AI 辅助分析和修改产品需求文档（PRD），支持按章节编辑和从现有需求反推内容。

> **Audience:** Product Manager
> 存储路径和缓存同步规则见 _storage.md（见附录：_storage.md）

## 命令格式

```
/req:prd-edit [章节名或编号]
```

**示例：**
- `/req:prd-edit` — 交互选择章节
- `/req:prd-edit 功能需求` — 直接编辑指定章节
- `/req:prd-edit 3` — 按编号编辑
- `/req:prd-edit 1,3,6` — 编辑多个章节

---

## 执行流程

### 1. 权限检查

读取 `settings.local.json` 的 `requirementRole`；若为 `readonly` 则报错退出，提示在主仓库执行。

### 2. 读取 PRD 文档和模板

检查 `docs/requirements/PRD.md` 是否存在，不存在则提示先执行 `/req:init`。

**必须先读取模板**作为格式基准：
```
优先级：
1. 本地模板：docs/requirements/templates/prd-template.md
2. 插件模板：<plugin-path>/templates/prd-template.md
```

**两个路径都不存在时，终止操作**：
```
❌ 未找到 PRD 模板文件

请执行 /req:update-template prd 恢复模板
```

### 3. 选择编辑章节

如果未通过参数指定章节，交互选择：

```
请选择要编辑的章节：

 1. 概述（背景、愿景、目标、范围）
 2. 用户研究（目标用户、用户旅程、竞品）
 3. 功能需求（功能概览、功能详情）
 4. 非功能需求（性能、可用性、安全、兼容）
 5. 数据需求（数据模型、采集、报表）
 6. 技术方案（架构、依赖、接口）
 7. 发布计划（版本、里程碑、灰度）
 8. 风险管理（风险、依赖、假设）
10. 附录（术语、参考、文档）

 a. AI 智能补充（基于现有需求反推）

请输入编号（可多选，如 1,3,6）：
```

**注意**：
- 第 9 章「需求追踪」不可手动编辑，由 `/req:new` 和 `/req:done` 自动维护
- 「修订历史」和「审批记录」不在选择列表中，修订历史由命令自动更新
- 章节名支持模糊匹配：`概述`、`用户`、`功能`、`非功能`、`数据`、`技术`、`发布`、`风险`、`附录`

### 4. 交互式编辑

对于用户选择的每个章节：

1. **展示当前内容**：
   - 已填写 → 展示实际内容
   - 未填写 → 标注「当前为模板占位文本」
2. **接收用户输入**：用户描述修改意图或直接提供内容
3. **AI 辅助补充**：基于用户输入，AI 补充和优化内容（触发 `prd-analyzer` 技能）

**格式约束（强制）：**
- 仅修改用户选择的章节内容，不得改变章节结构
- 章节标题、编号、层级必须与模板完全一致
- 不得新增、删除、合并或重命名模板中的章节
- 表格结构（列名、列数）必须与模板一致
- 即使某章节内容为空或占位文本，也不得删除该章节
- 第 9 章「需求追踪」禁止修改

### 5. AI 智能补充模式

当用户选择 `a`（AI 智能补充）时：

**数据采集**：

扫描 `docs/requirements/active/` 和 `completed/` 下的所有 REQ-*.md、QUICK-*.md，以及 `modules/*.md`。

**反推逻辑**：

| PRD 章节 | 数据来源 | 反推方式 |
|---------|---------|---------|
| 功能需求 | REQ 的「功能清单」 | 按模块归纳功能点，推导优先级 |
| 技术方案 | REQ 的「实现方案」 | 提取技术栈、架构模式、数据库 |
| 数据需求 | REQ 的「数据模型」 | 汇总核心实体和关系 |
| 用户研究 | REQ 的「使用场景」 | 提取用户角色和核心痛点 |
| 发布计划 | REQ 的状态和时间线 | 根据已完成/进行中需求推断里程碑 |
| 风险管理 | REQ 的「关联信息」 | 从依赖关系识别风险点 |

**输出格式**：
```
AI 智能分析完成

基于 X 个需求文档和 Y 个模块文档，建议更新以下章节：

【3. 功能需求】（当前未填写 → 建议填写）
  从 5 个 REQ 中归纳出 3 个功能模块...

【6. 技术方案】（当前已填写 → 建议补充）
  从实现方案中发现新增的技术依赖...

【5. 数据需求】（当前未填写 → 建议填写）
  从 3 个 REQ 的数据模型中汇总出 5 个核心实体...

```

展示具体建议后写入。

### 6. 变更预览

修改内容写入文档前，向用户展示变更摘要：

```
变更预览

【将修改的章节】：
- 3. 功能需求：新增 3 个功能模块概览
- 6. 技术方案：补充后端框架和数据库选型

【未修改的章节】：
- 1. 概述、2. 用户研究、4. 非功能需求...（保持不变）

【自动更新】：
- 修订历史：追加 v1.1 记录
- 最后更新日期：更新为今日
```

> 只修改用户明确要求的章节，严禁擅自修改其他章节内容。

### 7. 更新修订历史

自动在修订历史表追加记录：

```markdown
| v1.X | YYYY-MM-DD | | 更新章节：功能需求、技术方案 |
```

版本号规则：读取当前最大版本号，小版本 +1。

### 8. 更新元信息

更新元信息表中的「最后更新」字段为当前日期。

### 9. 保存并同步缓存

- 写入本地文件 `docs/requirements/PRD.md`
- **同步到主仓需求目录**（通过 PostToolUse Hook 自动触发）

### 10. 输出结果

```
✅ PRD 已更新
路径：docs/requirements/PRD.md
修改章节：功能需求、技术方案
版本：v1.0 → v1.1
缓存：已同步

下一步：
- /req:prd            查看 PRD 状态
- /req:prd-edit       继续编辑其他章节
- /req:new <标题>     从 PRD 派生具体需求
```

---

## 注意事项

- 编辑不会影响已有需求文档
- 第 9 章「需求追踪」由命令自动维护，不可手动编辑
- 所有变更都会记录到修订历史
- readonly 仓库不可编辑 PRD

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
