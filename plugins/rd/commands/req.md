---
description: 需求工作流管理 - 列出所有需求及其状态
argument-hint: "[子命令] [--module=模块名] [--type=后端|前端|全栈]"
allowed-tools: Read, Glob, Grep, Bash(ls:*)
model: claude-haiku-4-5-20251001
---

# 需求工作流管理

需求全流程管理主入口，列出所有需求及其状态。

## 命令格式

```
/rd:req [子命令] [参数] [--module=模块名] [--type=类型]
```

## 子命令

| 子命令 | 说明 | 示例 |
|-------|------|------|
| (空) | 列出所有需求 | `/rd:req` |
| `new` | 创建新需求 | `/rd:new 用户积分系统` |
| `edit` | 编辑需求 | `/rd:edit REQ-001` |
| `review` | 评审需求 | `/rd:req-review REQ-001` |
| `dev` | 开发需求 | `/rd:dev REQ-001` |
| `test` | 测试需求 | `/rd:test REQ-001` |
| `done` | 完成需求 | `/rd:done REQ-001` |
| `status` | 查看状态 | `/rd:status REQ-001` |
| `init` | 初始化项目 | `/rd:init my-project` |
| `use` | 绑定主仓（设为 readonly） | `/rd:use ../backend` |
| `projects` | 查看当前需求项目 | `/rd:projects` |
| `migrate` | 迁移本地需求到主仓需求目录 | `/rd:migrate my-project` |
| `modules` | 列出所有模块 | `/rd:modules` |
| `branch` | 分支管理 | `/rd:branch init` |
| `commit` | 规范提交 | `/rd:commit` |
| `changelog` | 生成版本说明 | `/rd:changelog v1.0.0` |

---

## 需求存储路径解析

读取 `.devflow/settings.json` 的 `requirementRole` / `requirementsDir`（`.devflow/settings.local.json` 同名字段覆盖），确定需求根目录：

- `primary` / 未配置角色：本仓 `requirementsDir`（缺省 `docs/requirements/`）
- `readonly`：`<requirementSource.path>/<主仓 requirementsDir>/`，无本地副本、直读主仓；未配置 `requirementSource` 时提示先 `/rd:use <primary-repo-path>` 绑定

### 目录结构

```
<需求根目录>/
modules/       # 模块文档
  user.md   # 用户模块
  order.md  # 订单模块
active/        # 进行中的需求
completed/     # 已完成的需求
templates/     # 需求模板
```

索引不落盘：本命令按 `active/`、`completed/` 实时渲染，没有需要维护的 `INDEX.md`。

---

## 执行流程（列表模式）

### 0. 解析需求路径

按上文「需求存储路径解析」确定需求根目录，扫描其 `active/` 与 `completed/`。

### 1. 扫描需求目录

列出 `active/` 下的全部需求文件，以及 `completed/` 中最近的 10 个（按元信息「完成日期」，缺该行时按文件最后一次 git 提交时间）。

### 2. 解析每个需求文档

提取元信息（REQ 与 QUICK 同时纳入）：
- 编号（REQ-XXX / QUICK-XXX）
- 标题
- 类型（REQ 取「类型」，QUICK 取「端类型」）
- 模块
- 状态
- 进度（REQ 为功能点完成数，QUICK 为「验证方式」勾选数）
- 更新时间
- 关联需求

### 2.5 筛选（可选）

支持按模块和类型筛选：

```bash
/rd:req --module=用户模块           # 只看用户模块的需求
/rd:req --type=后端                 # 只看后端需求
/rd:req --type=前端 --module=用户模块  # 组合筛选
```

### 3. 展示需求列表

头部显示插件版本和项目配置状态，然后按状态分组输出需求：开发中 / 测试中 / 评审通过 / 待评审 / 评审驳回 / 草稿 / 已完成（最近 10 条）——覆盖 `_storage.md`「双轨状态机」的全部状态，REQ 与 QUICK 混排，空分组不输出。

**头部信息**（每次 `/rd:req` 都展示）：

从 `${CLAUDE_PLUGIN_ROOT}/.claude-plugin/plugin.json` 读取版本号，从 `settings.local.json` 读取 `requirementProject`、`requirementRole`、`branchStrategy`，检查 CLAUDE.md 是否含架构描述关键词。

```
需求工作流 v<version> | 项目：<project> (<role>)
   分支策略：<strategy.model 或 "未配置"> | CLAUDE.md 架构：✅ 或 ⚠️ 未配置



活跃需求列表

开发中
| 编号 | 标题 | 类型 | 模块 | 进度 | 关联 |
|------|------|------|------|------|------|
| REQ-001 | 用户积分-后端 | 后端 | 用户模块 | 4/6 | REQ-002 |
| REQ-002 | 用户积分-前端 | 前端 | 用户模块 | 2/4 | REQ-001 |
| QUICK-003 | 修复登录验证码失效 | 后端 | 快速修复 | 验证 1/3 | - |

测试中
| 编号 | 标题 | 类型 | 模块 | 验证进度 |
|------|------|------|------|----------|
| REQ-005 | 订单导出 | 后端 | 订单模块 | 6/8 |

待评审
| 编号 | 标题 | 类型 | 模块 | 功能点 |
|------|------|------|------|--------|
| REQ-003 | 订单导出 | 后端 | 订单模块 | 3 |

草稿
| 编号 | 标题 | 类型 | 模块 | 创建时间 |
|------|------|------|------|----------|
| REQ-004 | 支付对账 | 全栈 | 支付模块 | 2026-01-08 |

已完成（最近 10 条）
| 编号 | 标题 | 模块 | 完成日期 |
|------|------|------|----------|
| REQ-003 | 订单导出 | 订单模块 | 2026-01-05 |
```

### 4. 提示可用操作

```
可用命令：
- /rd:new <标题> - 创建新需求
- /rd:dev REQ-001 - 进入开发
- /rd:status REQ-001 - 查看详情
```

---

## 子命令路由

根据参数路由到对应子命令：

```
参数解析：
- 无参数 → 列表模式
- new → /rd:new
- edit REQ-XXX → /rd:edit REQ-XXX
- review REQ-XXX → /rd:req-review REQ-XXX
- dev REQ-XXX → /rd:dev REQ-XXX
- test REQ-XXX → /rd:test REQ-XXX
- done REQ-XXX → /rd:done REQ-XXX
- status REQ-XXX → /rd:status REQ-XXX
- init <project-name> → /rd:init <project-name>
- use <project-name> → /rd:use <project-name>
- projects → /rd:projects
- migrate <project-name> → /rd:migrate <project-name>
- modules → /rd:modules
```

## 用户输入

$ARGUMENTS
