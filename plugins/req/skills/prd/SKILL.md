---
name: prd
description: 查看 PRD 状态 - 产品需求文档概览和章节填充分析
---

# 查看 PRD 状态

查看产品需求文档（PRD）的填充情况、各章节完成度、需求追踪统计。

> **Audience:** Product Manager
> 存储路径规则见 _storage.md（见附录：_storage.md）

## 命令格式

```
/req:prd [--section=章节名]
```

**示例：**
- `/req:prd` — 查看 PRD 整体状态概览
- `/req:prd --section=概述` — 查看指定章节详情
- `/req:prd --section=功能需求` — 查看功能需求章节

---

## 执行流程

### 1. 解析存储路径（按角色）

读取 `.claude/settings.local.json` 的 `requirementProject` 和 `requirementRole`，按角色确定 PRD 路径：
- `readonly`：`<requirementSource.path>/<requirementsDir>/PRD.md`
- `primary`：`docs/requirements/PRD.md`，本地不存在时回退到缓存
- 未绑定：`docs/requirements/PRD.md`

### 2. 检查 PRD 存在性

如果 PRD.md 不存在：

```
❌ 未找到 PRD 文档

可用操作：
- /req:init <project-name>  初始化项目（自动生成 PRD）
```

### 3. 读取 PRD 模板（作为基准）

```
优先级：
1. 本地模板：docs/requirements/templates/prd-template.md
2. 插件模板：<plugin-path>/templates/prd-template.md
```

**两个路径都不存在时，终止操作**：
```
❌ 未找到 PRD 模板文件，无法进行章节比对

请执行 /req:update-template prd 恢复模板
```

将模板中各章节的占位文本作为「未填写」的判断基准。

### 4. 分析各章节填充状态

逐章节比对 PRD 内容与模板占位文本：

**判断逻辑**：
- 章节内容与模板完全一致（仅变量替换差异） → 未填写
- 章节内容有实质性修改（非变量替换差异） → 已填写
- 第 9 章「需求追踪」单独处理 → 解析表格统计

**需要比对的章节**：

| 编号 | 章节名 | 子章节 |
|------|--------|--------|
| 1 | 概述 | 背景与问题、产品愿景、目标与成功指标、范围定义 |
| 2 | 用户研究 | 目标用户、用户旅程、竞品分析 |
| 3 | 功能需求 | 功能概览、功能详情 |
| 4 | 非功能需求 | 性能、可用性、安全、兼容性 |
| 5 | 数据需求 | 数据模型、数据采集、数据报表 |
| 6 | 技术方案 | 系统架构、第三方依赖、接口设计 |
| 7 | 发布计划 | 版本规划、里程碑、灰度策略 |
| 8 | 风险管理 | 风险识别、依赖项、假设与约束 |
| 9 | 需求追踪 | （自动维护，统计需求数量和状态） |
| 10 | 附录 | 术语表、参考资料、相关文档 |

### 5. 统计需求追踪（第 9 章）

解析「需求追踪」表格，按状态（草稿/待评审/评审通过/开发中/测试中/已完成）逐行统计数量并求总计。

### 6. 输出概览报告

```

PRD 状态：<project-name>


基本信息
产品名称：<product-name>
文档版本：v1.0
最后更新：2026-01-08
数据来源：本地 (primary)
状态：草稿

章节填充情况（N/10 已填写）

| 章节 | 状态 | 说明 |
|------|------|------|
| 1. 概述 | ✅ 已填写 | 背景、愿景、目标已完善 |
| 2. 用户研究 | ❌ 未填写 | 保持模板占位 |
| 3. 功能需求 | ✅ 已填写 | N 个功能模块 |
| 4. 非功能需求 | ❌ 未填写 | 保持模板占位 |
| 5. 数据需求 | ❌ 未填写 | 保持模板占位 |
| 6. 技术方案 | ✅ 已填写 | 架构已确定 |
| 7. 发布计划 | ❌ 未填写 | 保持模板占位 |
| 8. 风险管理 | ❌ 未填写 | 保持模板占位 |
| 9. 需求追踪 | 自动维护 | N 个需求 |
| 10. 附录 | ❌ 未填写 | 保持模板占位 |

需求追踪统计
总计：N 个需求
草稿：X
待评审：X
✅ 评审通过：X
开发中：X
测试中：X
已完成：X

建议优先填写：
- <优先级最高的未填写章节及理由>

可用操作：
- /req:prd-edit             编辑 PRD
- /req:prd --section=概述    查看指定章节详情
```

**建议优先填写的逻辑**：
- 有需求但「功能需求」未填写 → 优先建议
- 「概述」未填写 → 优先建议（基础信息）
- 「技术方案」未填写 → 其次建议
- 其他章节按编号顺序建议

---

## --section 模式

指定章节名时，输出该章节的完整内容：

```
/req:prd --section=功能需求
```

输出：
```

PRD 章节详情：3. 功能需求


状态：✅ 已填写

--- 章节内容 ---

### 3.1 功能概览

| 优先级 | 功能模块 | 功能描述 | 用户价值 | MVP |
|-------|---------|---------|---------|-----|
| P0 | 用户积分 | 积分规则管理 | 激励用户活跃 | 是 |
| P1 | 积分兑换 | 积分兑换商品 | 提升用户粘性 | 否 |

### 3.2 功能详情
...

--- 章节内容结束 ---

可用操作：
- /req:prd-edit 功能需求   编辑此章节
- /req:prd                返回概览
```

章节名支持模糊匹配：`概述`、`用户`、`功能`、`非功能`、`数据`、`技术`、`发布`、`风险`、`追踪`、`附录`。

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
