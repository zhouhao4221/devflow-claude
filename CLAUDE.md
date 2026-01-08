# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

这是一个 Claude Code 插件，用于需求全流程工作流管理。提供命令、技能和钩子来管理软件需求从草稿到完成的完整生命周期。

## 架构

插件遵循 Claude Code 的插件结构：

```
.claude-plugin/plugin.json    # 插件清单和配置
commands/                     # 命令定义（Markdown 文件）
skills/                       # 自动触发的 AI 技能（SKILL.md 文件）
hooks/hooks.json             # 工具拦截的事件钩子
scripts/                     # 验证和工具脚本
templates/                   # 需求文档模板
```

### 存储架构（本地优先 + 缓存同步）

需求采用**双存储**架构，本地为主、缓存为辅：

**1. 项目本地存储（主存储）**
- 存储目录：`docs/requirements/`
- 进行中的需求：`docs/requirements/active/`
- 已完成的需求：`docs/requirements/completed/`
- 模板文件：`docs/requirements/template.md`
- 优势：纳入 git 版本控制，团队可审查

**2. 全局缓存（同步副本）**
- 缓存目录：`~/.claude-requirements/`
- 项目缓存路径：`~/.claude-requirements/projects/<project-name>/`
- 仓库绑定配置：`.claude/settings.local.json` 中的 `requirementProject`
- 优势：支持跨仓库共享同一套需求

**更新策略：**
1. 创建/修改需求 → 先写入本地 `docs/requirements/`
2. 本地写入成功 → 同步到全局缓存
3. 读取需求 → 优先读本地，本地不存在时从缓存读取

### 命令结构

命令通过 `/req` 子命令模式调用：

**需求管理命令（编号可选，自动识别当前需求）：**
- `/req` - 列出所有需求
- `/req new [标题]` - 创建新需求
- `/req edit` - 编辑需求
- `/req review [pass|reject]` - 提交/通过评审
- `/req dev` - 启动开发
- `/req test` - 启动测试
- `/req done` - 完成需求
- `/req status` - 查看需求状态

**项目管理命令（全局缓存模式）：**
- `/req init <project-name>` - 初始化项目，创建全局缓存
- `/req use <project-name>` - 切换当前仓库绑定的项目
- `/req projects` - 列出所有项目
- `/req migrate <project-name>` - 将本地需求迁移到全局缓存
- `/req cache <action>` - 缓存管理（info/clear/clear-all/rebuild/export）

### 技能（自动触发）

- `requirement-analyzer` - 创建/编辑需求时触发，帮助完善文档各章节
- `dev-guide` - 执行 `/req dev` 时触发，按分层架构引导代码实现
- `code-impact-analyzer` - 需求变更时触发，分析受影响的代码
- `test-guide` - 执行 `/req test` 时触发，引导测试流程

### 钩子

在 `hooks/hooks.json` 中配置的前置/后置钩子：
- 写入 `docs/requirements/**/*.md` 时验证需求文档
- 提交代码时检查需求关联

## 需求生命周期状态

```
📝 草稿 → 👀 待评审 → ✅ 评审通过 → 🔨 开发中 → 🧪 测试中 → 🎉 已完成
```

## 跨仓库共享需求

支持前后端等多个仓库共享同一套需求：

```
~/backend/                         # 后端仓库（主仓库）
├── docs/requirements/             # 本地存储（主存储，纳入 git）
│   ├── active/
│   │   └── REQ-001-用户积分.md
│   └── completed/
└── .claude/settings.local.json    # { "requirementProject": "my-saas-product" }

~/frontend/                        # 前端仓库（关联仓库）
└── .claude/settings.local.json    # { "requirementProject": "my-saas-product" }

~/.claude-requirements/            # 全局缓存（同步副本）
└── projects/
    └── my-saas-product/
        ├── active/
        │   └── REQ-001-用户积分.md  # 从主仓库同步
        └── completed/
```

**使用流程：**
1. 在主仓库执行 `/req init my-saas-product` 初始化项目
2. 创建需求时：先写入 `docs/requirements/` → 同步到全局缓存
3. 在其他仓库执行 `/req use my-saas-product` 绑定同一项目
4. 关联仓库读取需求时从全局缓存获取

## 目标项目架构

本插件针对分层架构的 Go 项目设计：
```
Model → Store → Biz → Controller → Router
```

文件命名规范：kebab-case（如 `sys-dept-channel.go`）