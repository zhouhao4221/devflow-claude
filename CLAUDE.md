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

### 插件配置

需求存储支持两种模式：

**1. 全局缓存模式（推荐，支持跨仓库共享）**
- 全局缓存目录：`~/.claude-requirements/`
- 项目需求路径：`~/.claude-requirements/projects/<project-name>/`
- 仓库绑定配置：`.claude/settings.local.json` 中的 `requirementProject`

**2. 本地模式（单仓库）**
- 需求存储目录：`docs/requirements/`
- 进行中的需求：`docs/requirements/active/`
- 已完成的需求：`docs/requirements/completed/`
- 模板文件：`docs/requirements/template.md`

### 命令结构

命令通过 `/req` 子命令模式调用：

**需求管理命令：**
- `/req` - 列出所有需求
- `/req new [标题]` - 创建新需求
- `/req edit <REQ-XXX>` - 编辑需求
- `/req review <REQ-XXX>` - 提交/通过评审
- `/req dev <REQ-XXX>` - 启动开发
- `/req test <REQ-XXX>` - 启动测试
- `/req done <REQ-XXX>` - 完成需求
- `/req status <REQ-XXX>` - 查看需求状态

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
~/.claude-requirements/
└── projects/
    └── my-saas-product/          # 项目需求（前后端共享）
        ├── active/
        │   └── REQ-001-用户积分.md
        ├── completed/
        └── template.md

~/backend/                         # 后端仓库
└── .claude/settings.local.json    # { "requirementProject": "my-saas-product" }

~/frontend/                        # 前端仓库
└── .claude/settings.local.json    # { "requirementProject": "my-saas-product" }
```

**使用流程：**
1. 在任意仓库执行 `/req init my-saas-product` 创建项目
2. 在其他仓库执行 `/req use my-saas-product` 绑定同一项目
3. 所有仓库共享相同的需求文档

## 目标项目架构

本插件针对分层架构的 Go 项目设计：
```
Model → Store → Biz → Controller → Router
```

文件命名规范：kebab-case（如 `sys-dept-channel.go`）