# Requirement Workflow Plugin

需求全流程工作流管理插件 - 从需求分析到测试的完整生命周期管理。

## 功能特性

- **需求生命周期管理**：草稿 → 待评审 → 评审通过 → 开发中 → 测试中 → 已完成
- **智能需求分析**：自动引导完善需求文档各章节
- **开发引导**：按项目架构逐层引导代码实现
- **测试验证**：API 自动测试 + 交互式业务验证
- **变更追踪**：自动分析变更影响，记录变更历史

## 安装

### 方式一：本地开发测试

```bash
claude --plugin-dir /path/to/requirement-workflow
```

### 方式二：项目集成

将插件目录复制到项目的 `.claude/plugins/` 目录：

```bash
cp -r requirement-workflow /your-project/.claude/plugins/
```

## 命令列表

| 命令 | 说明 |
|------|------|
| `/req` | 列出所有需求 |
| `/req new [标题]` | 创建新需求 |
| `/req edit <REQ-XXX>` | 编辑需求 |
| `/req review <REQ-XXX>` | 提交/通过评审 |
| `/req dev <REQ-XXX>` | 启动开发 |
| `/req test <REQ-XXX>` | 启动测试 |
| `/req done <REQ-XXX>` | 完成需求 |
| `/req status <REQ-XXX>` | 查看状态 |

## 快速开始

### 1. 创建需求

```
/req new 用户积分系统
```

插件会引导你完成：
- 需求描述
- 功能清单
- 业务规则
- 数据模型
- API 设计
- 实现步骤

### 2. 提交评审

```
/req review REQ-001
```

检查需求完整性，生成评审摘要。

### 3. 评审通过

```
/req review REQ-001 pass
```

### 4. 启动开发

```
/req dev REQ-001
```

按项目架构逐层引导开发：
- Model → Store → Biz → Controller → Router

### 5. 执行测试

```
/req test REQ-001
```

自动执行 API 测试，引导业务验证。

### 6. 完成需求

```
/req done REQ-001
```

归档文档，生成完成报告。

## 需求生命周期

```
📝 草稿 ──────→ 👀 待评审 ──────→ ✅ 评审通过 ──────→ 🔨 开发中
    │              │    ↑              │                    │
    │              │    │              │                    ↓
    │              ↓    │              │               🧪 测试中
    │           ❌ 评审驳回 ───────────┘                    │
    │              │                                        ↓
    └──────→ 🗑️ 已废弃 ←────────────────────────────────── 🎉 已完成
```

## 智能技能（Skills）

插件包含以下自动触发的智能技能：

| Skill | 触发场景 |
|-------|---------|
| `requirement-analyzer` | 创建/编辑需求时 |
| `code-impact-analyzer` | 需求变更时 |
| `dev-guide` | 开发过程中 |
| `test-guide` | 测试阶段 |

## 目录结构

```
requirement-workflow/
├── .claude-plugin/
│   └── plugin.json           # 插件清单
├── commands/                  # 命令定义
│   ├── req.md
│   ├── req-new.md
│   ├── req-edit.md
│   ├── req-review.md
│   ├── req-dev.md
│   ├── req-test.md
│   ├── req-done.md
│   └── req-status.md
├── skills/                    # 智能技能
│   ├── requirement-analyzer/
│   ├── code-impact-analyzer/
│   ├── dev-guide/
│   └── test-guide/
├── hooks/                     # 事件钩子
│   └── hooks.json
├── templates/                 # 模板文件
│   └── requirement-template.md
├── scripts/                   # 辅助脚本
│   ├── validate-requirement.sh
│   ├── check-requirement-link.sh
│   ├── parse-requirement.sh
│   └── update-status.sh
└── README.md
```

## 配置

插件默认配置（在 plugin.json 中）：

```json
{
  "config": {
    "requirementDir": "docs/requirements",
    "activeDir": "docs/requirements/active",
    "completedDir": "docs/requirements/completed",
    "templateFile": "docs/requirements/template.md"
  }
}
```

## 与其他工具集成

| 工具 | 集成点 |
|------|-------|
| `code-reviewer` | 开发完成后自动触发代码审查 |
| `api-tester` | 测试阶段自动执行接口测试 |
| `git-commit` | 提交时关联需求编号 |

## 需求文档位置

```
docs/requirements/
├── active/              # 进行中的需求
├── completed/           # 已完成的需求
└── template.md          # 需求模板
```

## 版本历史

### v1.0.0

- 初始版本
- 完整的需求生命周期管理
- 4 个智能技能
- 8 个命令

## 许可证

MIT
