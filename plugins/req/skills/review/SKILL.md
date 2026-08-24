---
name: review
description: 需求评审 - 提交或记录评审结果
---

# 需求评审

提交需求评审或记录评审结果。

> **Audience:** Product Manager
> 存储路径和缓存同步规则见 _storage.md（见附录：_storage.md）

## 命令格式

```
/req:review [REQ-XXX] [pass|reject]
```

- 省略编号时自动选择「草稿」「评审驳回」或「待评审」的需求
- 多个候选时让用户选择

---

## 执行流程

### 根据当前状态执行不同操作

---

## 场景一：提交评审（草稿/评审驳回 → 待评审）

当需求状态为「草稿」或「评审驳回」时：

### 1. 完整性检查

检查必填章节是否完整：

```
需求完整性检查

✅ 需求描述 - 已填写
✅ 功能清单 - 3 个功能点
✅ 业务规则 - 5 条规则
✅ 数据模型 - 1 张新表
✅ 接口需求 - 3 个接口能力
✅ 文件改动清单 - 8 个文件
✅ 实现步骤 - 9 个步骤
✅ 测试要点 - 8 个测试点

检查结果：✅ 通过
```

如果有缺失：
```
❌ 需求完整性检查失败

缺失内容：
- ❌ 业务规则 - 未填写
- ❌ 实现步骤 - 未填写

请先完善需求文档：/req:edit REQ-XXX
```

### 2. 生成评审摘要

```markdown
## 需求评审摘要

### 基本信息
- 编号：REQ-001
- 标题：部门渠道关联
- 优先级：P1
- 功能点数：6

### 需求概述
在组织部门管理中，实现部门和分组与渠道的关联功能...

### 影响范围
- 模块：sys（系统）、oms（订单）、dashboard（看板）
- 文件数：12 个
- 新增表：1 张

### 风险评估
- 中等风险：涉及权限控制逻辑变更

### 工作量评估
- 功能点：6 个
- 预计涉及文件：12 个
```

### 3. 更新状态并同步缓存

- 修改元信息状态为「待评审」
- 勾选生命周期「待评审」
- **同步到主仓需求目录**

### 4. 提示

```
✅ 需求已提交评审

REQ-001 部门渠道关联
状态：待评审

评审通过后执行：/req:review REQ-001 pass
评审驳回执行：/req:review REQ-001 reject
```

---

## 场景二：评审通过（待评审 → 评审通过）

当参数包含 `pass` 时：

### 1. 状态检查

```
if 状态 != "待评审":
    错误：当前状态不是「待评审」，无法执行评审操作
    退出
```

### 2. 收集评审信息

```
评审人：<git config user.name 的值>（如需修改请输入）
评审意见：（可选）
```

- **评审人**（必填）：默认取 `git config user.name`，展示给用户确认，用户可修改
- **评审意见**：可选

### 3. 记录评审结果并同步缓存

- 更新「评审记录」章节
- 修改元信息状态为「评审通过」
- 勾选生命周期「评审通过」
- **同步到主仓需求目录**

### 4. 提示

```
✅ 评审通过

REQ-001 部门渠道关联
状态：✅ 评审通过

开始开发：/req:dev REQ-001
```

---

## 场景三：评审驳回（待评审 → 评审驳回）

当参数包含 `reject` 时：

### 1. 收集评审信息

```
评审人：<git config user.name 的值>（如需修改请输入）
驳回原因（必填）：
```

- **评审人**（必填）：默认取 `git config user.name`，展示给用户确认，用户可修改
- **驳回原因**（必填）：必须填写

### 2. 记录评审结果并同步缓存

- 更新「评审记录」章节（驳回原因必填）
- 修改元信息状态为「评审驳回」
- **同步到主仓需求目录**

### 3. 提示

```
❌ 评审驳回

REQ-001 部门渠道关联
状态：❌ 评审驳回

驳回原因：接口需求需要补充异常场景说明

修改需求：/req:edit REQ-001
重新提审：/req:review REQ-001
```

---

## 状态流转图

```
草稿 → 待评审 → 评审通过
  ↑                                  
                ↓                    ↓
  评审驳回              开发中
```

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
