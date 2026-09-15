# DevFlow

🌐 [English](README.en.md) | [中文](README.md) | [한국어](README.ko.md)

AI 驱动的软件全生命周期管理工具集，覆盖需求分析、开发引导、测试验证、项目管理、API 对接等完整流程。基于 Claude Code 插件体系构建。

## 插件列表

| 插件 | 说明 |
|------|------|
| **rd**（R&D，研发） | 研发工作流 — 需求分析、评审、开发、测试、归档 + 分支/PR/issue/版本（原 req 插件） |
| **pm** | 项目管理助手 — 周报、月报、统计、风险扫描、方案生成 |
| **api** | API 对接工具 — Swagger 解析、字段映射、代码生成 |
| **diag** | 生产诊断 — 只读 SSH 拉日志、解析堆栈、关联代码、给修复建议 |

> 各插件当前版本以 `claude plugins list` 或仓库内 `plugins/<插件>/.claude-plugin/plugin.json` 为准。
>
> 原 `req` 插件已更名为 `rd`（R&D 研发）：已安装 `req@devflow` 的用户请卸载后安装 `rd@devflow`，再在项目中执行 `/rd:migrate` 清理旧前缀引用。

---

## 安装

> 要求：Claude Code v1.0.33 或更高版本（推荐 v2.1+）

```bash
# 从 GitHub 安装
claude plugins marketplace add https://github.com/zhouhao4221/devflow-claude
claude plugins install rd@devflow    # 需求管理
claude plugins install pm@devflow     # 项目管理助手
claude plugins install api@devflow    # API 对接工具
claude plugins install diag@devflow   # 生产诊断
```

```bash
# 插件管理
claude plugins list                   # 查看已安装插件
claude plugins update rd@devflow     # 更新插件
claude plugins uninstall rd@devflow  # 卸载插件
```

---

## 智能模型分级

命令按推理强度分三档，通过 frontmatter 的 `model` 字段声明，平衡响应速度与推理质量：

| 档位 | 定位 | 典型命令 |
|------|------|---------|
| **Haiku** | 纯查询 / 展示 / 配置 / 规则明确的状态流转 | `/rd:req`、`/rd:status`、`/rd:show`、`/rd:commit`、`/pm:standup`、`/api:help` |
| **Sonnet** | 数据聚合 + 成文 | `/pm:weekly`、`/pm:monthly`、`/pm:stats`、`/pm:risk` |
| **会话模型**（不指定） | 分析代码 / 生成方案 / 多轮需求讨论 | `/rd:new`、`/rd:dev`、`/rd:fix`、`/rd:do`、`/rd:review-pr`、`/api:gen`、`/pm:plan` |

开发类命令还会把定位代码、跑测试、压缩大 diff 等高吞吐步骤委派给 subagent，原始输出不进主会话上下文。

每个命令还通过 `allowed-tools` 只预授权必需的工具；只读命令若调用写入类工具，会先弹出权限确认。

---

## rd 插件（R&D 研发）— 需求与研发流程

覆盖从需求分析、评审、开发、测试到归档的完整生命周期。

### 核心特性

- **自然语言指令**：直接用中文描述意图，自动映射到 `/rd:*` 命令（如"修个登录超时的 bug"→ `/rd:fix`、"开始开发025"→ `/rd:dev REQ-025`，支持粘贴 issue/PR URL 自动识别）
- **一键模式**：`/rd:fix --auto` 跳过所有确认交互，自动串联 commit → push → PR（通过 `.claude/.req-auto` marker 放行 git 确认弹框）
- **AI 提问式需求分析**：AI 逐轮提问收集信息，一次性生成完整需求文档
- **完整生命周期**：草稿 → 待评审 → 评审通过 → 开发中 → 测试中 → 已完成
- **双轨需求**：正式需求（REQ）和快速修复（QUICK）两套流程
- **智能开发**：`/rd:do` 描述意图即可开发，AI 自动分析、选流程、建分支、生成方案
- **开发引导**：读取项目 CLAUDE.md 的分层架构，按配置顺序逐层引导（支持任意技术栈）
- **开发中文档维护**：AI 发现偏差时主动提示更新需求文档
- **分支管理**：GitHub Flow / Git Flow / Trunk-Based 三种策略
- **前后端协作**：前端 REQ 描述交互逻辑，dev 阶段自动匹配后端接口
- **PR 审查与合并**：AI 代码审查、自动提交评论、一键合并
- **Git issue 集成**：`--from-issue=#N` 直接从 Gitea/GitHub issue 创建需求，分支/commit/done 全链路自动关联和关闭 issue
- **跨仓库共享**：前后端多仓库共享同一套需求（主仓唯一存储，只读仓库直读，无缓存无同步）
- **规范提交**：自动关联需求编号的 Conventional Commits
- **版本说明**：基于 Git 记录自动生成 Changelog

### 快速开始

**新项目只需两步启动**（插件会在每次会话开始时主动引导，缺一不可）：

```bash
# 1. 初始化项目（创建 docs/requirements/、生成 PRD、绑定仓库）
/rd:init my-project

# 2. 配置分支策略（GitHub Flow / Git Flow / Trunk-Based + 仓库托管类型）
/rd:branch init
```

随后进入日常工作流：

```bash
# 3. 创建需求（AI 提问收集信息 → 一次性生成文档）
/rd:new 用户积分系统

# 4. 评审
/rd:review pass

# 5. 开发（AI 生成实现方案，按分层架构引导）
/rd:dev

# 6. 测试
/rd:test

# 7. 完成归档
/rd:done
```

### 命令一览

#### 需求管理

| 命令 | 说明 |
|------|------|
| `/rd:req` | 列出所有需求，支持 `--type` 和 `--module` 筛选 |
| `/rd:new [标题]` | 创建正式需求（AI 提问 → 生成文档） |
| `/rd:new-quick [标题]` | 创建快速修复（小 bug / 小功能） |
| `/rd:do <描述>` | 智能开发（优化/重构/升级/小调整，无文档） |
| `/rd:fix <描述>` | 轻量修复（bug 修复，无文档） |
| `/rd:edit [REQ-XXX]` | 编辑需求文档 |
| `/rd:show [REQ-XXX]` | 查看需求详情（只读） |
| `/rd:status [REQ-XXX]` | 查看需求状态 |
| `/rd:review [pass\|reject]` | 提交 / 通过 / 驳回评审 |
| `/rd:dev [REQ-XXX]` | 启动或继续开发 |
| `/rd:test [REQ-XXX]` | 综合测试验证 |
| `/rd:test_regression` | 运行已有自动化测试 |
| `/rd:test_new` | 为新功能创建测试用例 |
| `/rd:done [REQ-XXX]` | 完成需求并归档 |
| `/rd:upgrade <QUICK-XXX>` | 快速修复升级为正式需求 |
| `/rd:split [描述]` | 需求粒度分析和拆分建议 |

#### PR 审查与合并

| 命令 | 说明 |
|------|------|
| `/rd:pr [REQ-XXX]` | 创建 PR（自动适配 GitHub / Gitea） |
| `/rd:review-pr` | 查看 PR 状态 |
| `/rd:review-pr review` | AI 代码审查，提交评论 |
| `/rd:review-pr merge` | 合并 PR（支持 merge/squash/rebase） |

#### 文档管理

| 命令 | 说明 |
|------|------|
| `/rd:prd` | 查看 PRD 状态概览 |
| `/rd:prd-edit [章节]` | 编辑 PRD 文档 |
| `/rd:modules` | 列出所有模块 |
| `/rd:specs` | 规范文档管理（数据类型、接口契约等） |

#### 版本与分支

| 命令 | 说明 |
|------|------|
| `/rd:commit [消息]` | 规范提交，自动关联需求编号 |
| `/rd:changelog <version>` | 生成版本升级说明 |
| `/rd:branch init` | 配置分支策略 |
| `/rd:branch hotfix [描述]` | 创建紧急修复分支 |

#### 项目配置

| 命令 | 说明 |
|------|------|
| `/rd:init <项目名>` | 初始化项目 |
| `/rd:use <主仓路径>` | 绑定主仓库，当前仓库设为只读 |
| `/rd:projects` | 查看当前需求项目 |
| `/rd:migrate` | 从 v2 布局迁移到 `.devflow/` |
| `/rd:update-template` | 同步插件最新模板 |

### 需求生命周期

```
正式需求（REQ）：草稿 → 待评审 → 评审通过 → 开发中 → 测试中 → 已完成
快速修复（QUICK）：草稿 → 方案确认 → 开发中 → 已完成
```

### 需求文档结构

| 区域 | 章节 | 填充方式 |
|------|------|---------|
| 需求定义 | 一~六（需求描述、功能清单、业务规则、使用场景、数据与交互、测试要点） | AI 提问收集 → 一次性生成 |
| 流程记录 | 七~九（评审记录、变更记录、关联信息） | 各命令自动填充 |
| 实现方案 | 十（数据模型、API 设计、文件改动、实现步骤） | `/rd:dev` 阶段 AI 分析代码生成 |

### 跨仓库共享

```
~/backend/   (primary)  → docs/requirements/  唯一存储，纳入 git，写入即生效
~/frontend/  (readonly) → /rd:use ~/backend 绑定后直读主仓需求，dev 阶段自动匹配后端接口
```

配置在 `.devflow/settings.json`（团队共享，入 git）与 `.devflow/settings.local.json`（密钥与本机路径，不入 git）。从 v2 升级的项目执行 `/rd:migrate`。

### AI 技能（自动触发）

| 技能 | 触发场景 |
|------|---------|
| `requirement-analyzer` | 创建/编辑需求时，AI 提问收集 → 生成文档 |
| `dev-guide` | 开发阶段，按分层架构引导 + 开发中文档维护 |
| `quick-fix-guide` | 快速修复，快速分析并生成方案 |
| `test-guide` | 测试阶段，回归测试和新建测试 |
| `prd-analyzer` | 编辑 PRD 时，辅助完善各章节 |
| `code-impact-analyzer` | 需求变更时，分析代码影响范围 |
| `changelog-generator` | 生成版本说明 |

---

## pm 插件 — 项目管理助手

从 PRD、需求文档和 Git 记录中提取项目数据，按不同场景和受众生成汇报、统计、方案等内容。

- **只读消费**：读取 rd 插件产出的数据，不修改需求文档
- **无需 rd 即可工作**：没有需求数据时仍可使用 Git 统计和自由提问
- **可选保存**：所有输出均可保存到 `docs/reports/`

| 命令 | 说明 |
|------|------|
| `/pm` | 项目概况仪表盘 |
| `/pm:weekly` | 周报 |
| `/pm:monthly` | 月报 |
| `/pm:milestone <版本>` | 里程碑总结 |
| `/pm:stats` | 多维度数据统计 |
| `/pm:progress` | 项目总进度 |
| `/pm:plan <主题>` | 方案文档（排期/技术/资源） |
| `/pm:risk` | 风险扫描 |
| `/pm:standup` | 站会摘要 |
| `/pm:ask <问题>` | 基于项目数据自由提问 |

---

## api 插件 — API 对接工具

前端 API 对接工具，支持 Swagger/OpenAPI 解析、字段映射、代码生成。

| 命令 | 说明 |
|------|------|
| `/api:import` | 导入 Swagger 文档 |
| `/api:search <关键词>` | 搜索接口 |
| `/api:gen` | 生成 TypeScript 类型和请求函数 |
| `/api:map` | 字段映射分析 |

---

## diag 插件 — 生产诊断

用自然语言描述线上报错，插件经 SSH 只读拉取日志、解析堆栈、关联本地代码并给出修复建议。**全程只读**：SSH 主机白名单、命令动词白名单、写操作阻断、敏感输入拦截等风控 Hook 全部强制执行，所有 SSH 命令审计落盘。

| 命令 | 说明 |
|------|------|
| `/diag:init` | 配置服务清单（主机、日志路径） |
| `/diag:diagnose <报错描述>` | 拉日志 → 解析堆栈 → 关联代码 → 修复建议 |
| `/diag:audit` | 查询审计记录 |

详见 [plugins/diag/README.md](plugins/diag/README.md)。

---

## 使用教程

完整的分步教程见 [docs/tutorial.md](docs/tutorial.md)。

## 许可证

[Apache License 2.0](LICENSE)
