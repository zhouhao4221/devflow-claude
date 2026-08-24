---
name: edit
description: 编辑需求 - 修改已有需求文档
---

# 编辑需求

编辑已有需求文档，仅修改内容，不触发开发流程。

> 存储路径和缓存同步规则见 _storage.md（见附录：_storage.md）

## 命令格式

```
/req:edit [REQ-XXX]
```

- 省略编号时自动选择最近活跃的需求
- 多个候选时让用户选择

---

## 执行流程

### 1. 选择需求

- 指定编号 → 使用该需求
- 未指定 → 查找活跃需求（按修改时间排序）
- 本地不存在时经 requirementSource.path 直读

### 2. 读取模板

**必须先读取对应类型的模板文件**，作为格式基准：

```
正式需求（REQ-XXX）：
  1. 本地模板：docs/requirements/templates/requirement-template.md
  2. 插件模板：<plugin-path>/templates/requirement-template.md

快速修复（QUICK-XXX）：
  1. 本地模板：docs/requirements/templates/quick-template.md
  2. 插件模板：<plugin-path>/templates/quick-template.md
```

**两个路径都不存在时，终止操作**：
```
❌ 未找到对应类型的模板文件

请执行 /req:update-template <requirement|quick> 恢复模板
```

读取后解析模板的完整章节结构，编辑时**必须严格保持模板中的所有章节、层级和格式**。

### 3. 功能扩展判断

如果用户意图是**新增功能点**（而非修改已有内容），先判断是否应新建 REQ：

```
检测到您要新增功能点

核心问题：去掉这个功能点，原需求还能独立交付吗？

- 能独立交付 → 建议执行 /req:new 创建新需求，在关联信息中引用当前 REQ
- 不能独立交付 → 继续在当前 REQ 中补充
```

**自动判断规则：**
- 原 REQ 已 `已完成` → 必须新建，提示用户执行 `/req:new`
- 原 REQ 在 `开发中`/`测试中` 且新功能影响已写代码 → 建议新建，避免范围蔓延
- 新功能是原需求的自然延伸 → 继续编辑

> 详细规则见 _granularity.md（见附录：_granularity.md） 「已有需求的功能扩展」

### 4. 状态提示

如果需求已在开发中或测试中：

```
⚠️ 警告：需求 REQ-XXX 当前状态为「开发中」
修改需求可能影响已完成的开发工作。
```

### 5. 选择编辑章节

询问用户要编辑的内容：

```
请选择要编辑的章节：
1. 需求描述
2. 功能清单
3. 业务规则
4. 使用场景
5. 数据模型
6. 接口需求
7. 文件改动清单
8. 实现步骤
9. 测试要点
10. 全部重新分析

请输入编号（可多选，如 1,2,4）：
```

> 编辑 1（需求描述）或 4（使用场景）后，AI 会自动重新生成功能清单和业务规则。

### 6. 交互式编辑

根据选择进入对应章节的编辑模式：
- 展示当前内容
- 与用户多轮讨论修改方向和细节，**不限讨论轮数**
- **意图澄清**：分析用户真实意图，用户说改 A 但实际应改 B 时主动指出并确认
- **关联分析**：修改某章节可能导致其他章节不一致时，主动提示是否一并修改
- 用户明确确认修改内容后（如"可以了"、"就这样改"），再进入变更预览

**格式约束（强制）：**
- 仅修改用户选择的章节内容，不得改变章节结构
- 章节标题、编号、层级必须与模板完全一致
- 不得新增、删除、合并或重命名模板中的章节
- 表格结构（列名、列数）必须与模板一致
- 即使某章节内容为空或占位文本，也不得删除该章节

### 7. 变更预览

修改内容写入文档前，向用户展示变更摘要：

```
变更预览

【将修改的章节】：
- 使用场景：新增"批量导入"场景

【未修改的章节】：
- 需求描述、功能清单、业务规则...（保持不变）
```

> 只修改用户明确要求的章节，严禁擅自修改其他章节内容。

### 8. 变更影响分析

如果需求已在开发中，分析变更影响：

```
变更影响分析

修改内容：
- 接口需求：新增渠道关联能力

影响评估：
- 直接影响：Controller、API 层需要修改
- 间接影响：前端需配合调整

受影响文件：
- internal/sys/controller/v1/sys_dept.go
- pkg/api/core/v1/sys_dept.go

建议：完成当前开发后再进行变更
```

### 9. 保存并同步缓存

- 更新「变更记录」章节
- 写入本地文件
- **同步到主仓需求目录**

### 10. 输出结果

```
✅ 需求已更新：REQ-XXX
路径：docs/requirements/active/REQ-XXX-标题.md
缓存：已同步

下一步：
- /req:edit REQ-XXX - 继续编辑
- /req:review - 提交评审
```

---

## 注意事项

- 编辑不会改变需求状态
- 已开发的需求变更需谨慎
- 所有变更都会记录到变更历史

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

## 附录：_granularity.md

# 公共逻辑参考 - 需求粒度

> 此文档定义需求粒度规则、REQ 与 QUICK 的选择、前后端拆分规则。
>
> 同伴文档（同目录，按需 Read；此处不用链接，避免生成器传递内联）：`_storage.md`、`_branch.md`、`_issue.md`、`_template.md`、`_claude-md.md`。

## 需求粒度规则

### 基本原则

一个 REQ **对应一个可独立交付的业务功能**，不按技术层拆分，不按开发步骤拆分。

判断标准：**这个需求完成后，用户能感知到一个完整的功能变化吗？** 如果能，粒度合适；如果不能，说明拆得太细。

### 粒度参考

| 粒度 | 是否合适 | 说明 |
|------|---------|------|
| 「用户积分系统」含积分规则+积分查询+积分兑换+积分排行 | 太大 | 拆为多个 REQ |
| 「用户积分-积分规则管理」含 CRUD + 规则校验 | 合适 | 一个完整功能 |
| 「用户积分-积分规则-新增接口」仅一个 API | 太小 | 合并到功能级 REQ |
| 「用户积分-新增 model 层」按技术层拆分 | 错误 | 按功能拆，不按层拆 |

### 拆分建议

**应该拆分的情况：**
- 功能可独立上线、独立使用（如：积分规则管理 vs 积分兑换）
- 不同功能由不同人负责
- 功能之间无强时序依赖（可并行开发）
- 单个需求涉及文件超过 15 个

**不应该拆分的情况：**
- CRUD 属于同一业务实体（增删改查放一个 REQ）
- 功能之间强耦合，必须同时上线
- 拆开后单个 REQ 无法独立验证

### 已有需求的功能扩展

当 REQ 已存在，需要新增功能点时，按以下规则判断是修改原 REQ 还是新建：

**核心问题：去掉这个功能点，原需求还能独立交付吗？**
- **能** → 新建 REQ，通过关联字段链接
- **不能** → 修改原 REQ（`/req:edit`），在功能清单中补充

| 场景 | 建议 | 原因 |
|------|------|------|
| 新功能是原需求的自然延伸，缺少则不完整 | 修改原 REQ | 属于同一个可交付单元 |
| 新功能可独立上线，不依赖原 REQ | 新建 REQ | 独立交付，独立测试 |
| 原 REQ 已 `已完成` | 必须新建 REQ | 已归档需求不应回退状态 |
| 原 REQ 在 `开发中`/`测试中`，新功能会影响已写代码 | 新建 REQ | 避免范围蔓延，保持进度可控 |

**修改原 REQ 时**：使用 `/req:edit`，在变更记录章节说明新增内容。
**新建 REQ 时**：使用 `/req:new`，在关联信息中填写原 REQ 编号。

### 前后端拆分

前后端按类型字段区分，不按 REQ 编号拆分同一端的功能：

```
正确：
  REQ-001 用户积分规则管理-后端    （含 CRUD 全部接口）
  REQ-002 用户积分规则管理-前端    （含 CRUD 全部页面）

错误：
  REQ-001 用户积分规则-新增接口
  REQ-002 用户积分规则-查询接口
  REQ-003 用户积分规则-修改接口
```

### REQ 与 QUICK 的选择

| 场景 | 使用 | 理由 |
|------|------|------|
| 新业务功能（CRUD、新页面） | REQ | 需完整设计和评审 |
| 已有功能的小调整（加字段、改逻辑） | QUICK | 改动范围小、风险低 |
| Bug 修复 | QUICK | 除非修复涉及重构 |
| 重构/优化（不改变功能） | QUICK 或 REQ | 按改动范围判断，超过 5 个文件用 REQ |

### 创建时的 AI 辅助判断

`/req:new` 创建需求时，AI 应根据以上规则辅助判断粒度是否合适：
- 标题过于宽泛（如「XX系统」「XX模块」） → 建议拆分，列出子功能
- 标题过于具体（如「新增XX接口」「修改XX字段」） → 建议合并或改用 QUICK
- 不确定时询问用户业务目标，再给出建议
