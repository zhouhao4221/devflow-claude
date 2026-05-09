---
description: 初始化需求项目 - 创建本地存储和全局缓存
argument-hint: "<project-name>"
allowed-tools: Read, Write, Edit, Glob, Grep, Bash(mkdir:*, ls:*, cp:*)
model: claude-haiku-4-5-20251001
---

# 初始化需求项目

初始化需求项目，创建本地存储目录和全局缓存，并绑定当前仓库。

## 命令格式

```
/req:init <project-name> [--reinit]
```

## 参数

- `project-name`: 项目名称（建议使用 kebab-case，如 `my-saas-product`）
- `--reinit`: 重新初始化模式，为已有项目补充缺失的目录和文件（不覆盖已有内容）

---

## 执行流程

### 1. 解析参数

```
参数: $ARGUMENTS
项目名称: 从参数中提取（排除 --reinit）
重新初始化模式: 参数包含 --reinit 时为 true
本地存储路径: docs/requirements
全局缓存路径: ~/.claude-requirements/projects/<project-name>
```

**判断逻辑**：
- 若参数包含 `--reinit`，进入重新初始化模式
- 重新初始化模式下，只补充缺失内容，不覆盖已有文件

### 2. 创建本地存储目录（主存储）

```bash
# 在当前仓库创建本地需求目录
LOCAL_ROOT=docs/requirements
mkdir -p $LOCAL_ROOT/active
mkdir -p $LOCAL_ROOT/completed
mkdir -p $LOCAL_ROOT/modules
mkdir -p $LOCAL_ROOT/templates
```

### 3. 复制模板文件到本地

将所有模板文件复制到 `docs/requirements/templates/` 目录：

```bash
TEMPLATE_DIR=$LOCAL_ROOT/templates

# 仅当文件不存在时复制（--reinit 模式下保护已有文件）
if [ ! -f $TEMPLATE_DIR/requirement-template.md ]; then
  cp <plugin-path>/templates/requirement-template.md $TEMPLATE_DIR/requirement-template.md
fi

if [ ! -f $TEMPLATE_DIR/quick-template.md ]; then
  cp <plugin-path>/templates/quick-template.md $TEMPLATE_DIR/quick-template.md
fi

if [ ! -f $TEMPLATE_DIR/prd-template.md ]; then
  cp <plugin-path>/templates/prd-template.md $TEMPLATE_DIR/prd-template.md
fi
```

### 4. 生成 PRD 文档

从本地模板生成项目 PRD 文档，替换变量：

```bash
# 仅当 PRD.md 不存在时生成（--reinit 模式下保护已有文件）
if [ ! -f $LOCAL_ROOT/PRD.md ]; then
  cp $TEMPLATE_DIR/prd-template.md $LOCAL_ROOT/PRD.md
  # 替换模板变量
  sed -i 's/{{PROJECT_NAME}}/<project-name>/g' $LOCAL_ROOT/PRD.md
  sed -i 's/{{DATE}}/$(date +%Y-%m-%d)/g' $LOCAL_ROOT/PRD.md
fi
```

### 4.1 创建「快速修复」模块

自动创建「快速修复」模块文档，用于归档快速修复类需求：

```bash
# 仅当模块文档不存在时创建
QUICK_FIX_MODULE=$LOCAL_ROOT/modules/quick-fix.md
if [ ! -f $QUICK_FIX_MODULE ]; then
  cat > $QUICK_FIX_MODULE << 'EOF'
# 快速修复

## 概述

本模块用于归档所有快速修复类需求，包括：
- 小 bug 修复
- 小功能增强
- 代码优化
- UI 微调

这些改动通常不需要完整的需求评审流程，可快速完成。

---

## 核心功能

> 快速修复按时间顺序记录，无需细分功能点

| 编号 | 描述 | 状态 | 完成日期 |
|------|------|------|----------|
| - | 暂无记录 | - | - |

---

## 业务规则

| 规则 | 说明 |
|------|------|
| 改动范围 | 建议 <5 个文件 |
| 数据库变更 | 不涉及表结构变更 |
| 影响范围 | 不影响核心业务流程 |
| 验证方式 | 自测即可 |

---

## 相关需求

| 编号 | 标题 | 状态 | 更新时间 |
|------|------|------|----------|
| - | 暂无 | - | - |

---

## 变更记录

| 日期 | 变更内容 |
|------|----------|
| {{DATE}} | 初始版本 |
EOF
  # 替换日期
  sed -i 's/{{DATE}}/$(date +%Y-%m-%d)/g' $QUICK_FIX_MODULE
fi
```

### 5. 创建全局缓存目录（同步副本）

```bash
# 确保全局缓存目录存在
CACHE_ROOT=~/.claude-requirements/projects/<project-name>
mkdir -p $CACHE_ROOT/active
mkdir -p $CACHE_ROOT/completed
mkdir -p $CACHE_ROOT/modules

# 同步模板和 PRD 到缓存（仅当本地存在时）
mkdir -p $CACHE_ROOT/templates
[ -f $TEMPLATE_DIR/requirement-template.md ] && cp $TEMPLATE_DIR/requirement-template.md $CACHE_ROOT/templates/
[ -f $TEMPLATE_DIR/quick-template.md ] && cp $TEMPLATE_DIR/quick-template.md $CACHE_ROOT/templates/
[ -f $TEMPLATE_DIR/prd-template.md ] && cp $TEMPLATE_DIR/prd-template.md $CACHE_ROOT/templates/
[ -f $LOCAL_ROOT/PRD.md ] && cp $LOCAL_ROOT/PRD.md $CACHE_ROOT/PRD.md

# 同步快速修复模块到缓存
[ -f $LOCAL_ROOT/modules/quick-fix.md ] && cp $LOCAL_ROOT/modules/quick-fix.md $CACHE_ROOT/modules/
```

### 6. 更新全局索引

更新 `~/.claude-requirements/index.json`：

```json
{
  "projects": {
    "<project-name>": {
      "created": "2026-01-08",
      "primaryRepo": "/path/to/current/repo",
      "repos": ["/path/to/current/repo"]
    }
  }
}
```

### 7. 绑定当前仓库

> 写入规范见 [_storage.md](./_storage.md#settingslocaljson-写入规范)。

读取已有 `.claude/settings.local.json`，合并以下��段后写回（不覆盖已有的 `branchStrategy` 等字段）：

```json
{
  "requirementProject": "<project-name>",
  "requirementRole": "primary"
}
```

### 8. 生成项目架构文件

扫描项目现有结构，自动生成 `docs/prompt/architecture.md`，并在 CLAUDE.md 中添加引用。
`/req:dev` 和 `/req:test` 运行时会自动读取该文件，无需手动传入。

#### 8.1 检查是否已有架构文件

```
docs/prompt/architecture.md 已存在 → 跳过，不覆盖
CLAUDE.md 中已包含架构章节       → 跳过，不覆盖
```

#### 8.2 扫描项目结构

按以下优先级检测技术栈：

| 检测文件 | 推断技术栈 |
|---------|----------|
| `go.mod` | Go 后端 |
| `pom.xml` / `build.gradle` | Java 后端 |
| `package.json`（含 `next` / `nuxt` / `vite`） | 前端 |
| `package.json`（含 `express` / `fastify` / `nest`） | Node.js 后端 |
| `requirements.txt` / `pyproject.toml` | Python 后端 |
| `Cargo.toml` | Rust |
| 均未找到 | 通用 |

同时扫描：
- 顶层及二级目录结构（推断分层）
- 测试文件位置（`*_test.go` / `*.test.ts` / `tests/` 等）
- 已有代码风格样例（命名、错误处理模式）

#### 8.3 生成架构文件

基于扫描结果，AI 生成 `docs/prompt/architecture.md`，结构固定为：

```markdown
## 技术栈
<!-- AI 从扫描结果填入，如：Go 1.22 · Gin · GORM · MySQL 8 -->

## 分层架构
<!-- AI 从目录结构推断，按开发顺序排列 -->
| 层 | 目录 | 职责 |
|----|------|------|
| ...扫描到的分层... | | |

## 文件命名
<!-- AI 从现有文件推断 -->

## 开发规范
<!-- AI 从现有代码推断，无代码时留空占位 -->

## 测试规范
<!-- AI 从测试文件位置推断 -->
- 测试目录：...
- 运行命令：...
```

生成后展示内容，请用户确认：

```
📋 已扫描项目结构，生成架构文件草稿：

   技术栈：Go 1.22 · Gin · GORM · MySQL
   分层：Model → Store → Biz → Controller → Router
   测试：*_test.go，运行 go test ./...

   草稿已写入 docs/prompt/architecture.md

   内容是否准确？(y/n，默认 y，n 则打开文件手动修改)
```

#### 8.4 在 CLAUDE.md 中添加引用

在 CLAUDE.md 末尾追加一行引用（文件不存在时创建）：

```markdown
## 项目架构

详见 `docs/prompt/architecture.md`，`/req:dev` 和 `/req:test` 会自动读取。
```

CLAUDE.md 不包含架构内容本身，只持有指针。

#### 8.5 已有架构文件时

```
✅ docs/prompt/architecture.md 已存在，跳过生成
```

#### 8.6 创建 Prompt 库骨架

在 `docs/prompt/` 中创建通用 Prompt 文件骨架，仅当文件不存在时创建（--reinit 同样保护已有文件）：

| 文件 | 用途说明（写入 `>` 行） |
|------|------|
| `code-generation.md` | 根据接口定义生成实现代码 |
| `refactoring.md` | 在不改变行为的前提下重构代码结构 |
| `test-generation.md` | 为代码编写测试用例 |
| `error-diagnosis.md` | 分析错误根本原因并给出修复方向 |
| `pr-review.md` | PR 初轮 AI 审查 |
| `requirement-structuring.md` | 将模糊需求转为结构化输入 |

每个文件使用统一的 5 节骨架，节内容留空，由用户与 AI 协作填写：

```markdown
# <中文标题>

> <用途说明>

## 什么时候用

<!-- 适用场景 + 不适合的情况 -->

## 必备输入

<!-- 触发前需要准备的具体清单，这是最重要的部分 -->

## 触发方式

<!-- 单次任务模板（如何构造 prompt）+ 写入 CLAUDE.md 的推荐做法 -->

## 优质输出标准

<!-- 好的输出长什么样，用于质量判断 -->

## 常见失败模式

| 问题 | 原因 | 解决方案 |
|------|------|----------|
```

同时创建 `docs/prompt/prompt-craft.md`，说明上述格式规范本身（供团队成员新建 prompt 时参考）。

`architecture.md` 已由步骤 8.3 生成，此处跳过。

### 9. 项目 Skills 初始化

创建 `.claude/skills/` 目录（不存在时），并根据项目类型引导创建常用 Skill 文件。

#### 9.1 创建目录

```bash
mkdir -p .claude/skills
```

#### 9.2 引导创建 Skill 文件

**目录为空时**，根据步骤 8 选择的项目类型展示对应提示：

**后端项目（Go / Java / 其他服务端）**：

```
💡 后端项目通常需要声明 migration SQL 目录路径：

   .claude/skills/migration.md
   /req:dev 生成数据库变更 SQL 时会自动读取

   是否创建？(y/n，默认 y)
```

用户选择 `y` → 创建 `.claude/skills/migration.md`：

```markdown
# Migration Skill

声明项目的 migration SQL 存放目录，供 /req:dev 自动使用。

- **MIGRATIONS_DIR**: `db/migrations`
```

并提示用户修改路径：

```
✅ 已创建 .claude/skills/migration.md
   请将 MIGRATIONS_DIR 修改为项目实际路径，如：
   - db/migrations（GORM 默认）
   - database/migrations（Laravel 默认）
   - src/migrations（自定义）
```

**前端项目**：

```
✅ 已创建 .claude/skills/ 目录

   前端项目通常不需要预置 Skill 文件。
   如有项目特有约定（组件规范、接口路径约定等），
   可在此目录创建 .md 文件，/req:dev 会自动读取。
```

**自定义项目**：

```
✅ 已创建 .claude/skills/ 目录

   将项目特有知识写成 Skill 文件放在此目录，/req:dev 和 /req:test 会自动读取。
   示例：
   - migration.md  — 声明数据库 migration 目录
   - testing.md    — 声明项目特有的测试约定
```

**目录已有文件时**，列出现有 Skill 并跳过引导：

```
✅ .claude/skills/ 已有以下 Skill 文件：
   - migration.md
   跳过 Skills 引导
```

### 10. 输出结果

**初始化成功**：
```
✅ 项目 "<project-name>" 初始化成功！

📁 本地存储（主存储，纳入 git）:
   docs/requirements/
   ├── active/         # 进行中的需求
   ├── completed/      # 已完成的需求
   ├── modules/        # 模块文档
   │   └── quick-fix.md  # 快速修复模块（预置）
   ├── templates/      # 模板文件
   │   ├── requirement-template.md  # 需求模板
   │   ├── quick-template.md        # 快速修复模板
   │   └── prd-template.md          # PRD 模板
   └── PRD.md          # 产品需求文档

🔄 全局缓存（同步副本，跨仓库共享）:
   ~/.claude-requirements/projects/<project-name>/

🔗 当前仓库已绑定到此项目

📋 已生成 PRD 文档: docs/requirements/PRD.md
   请填写以下关键内容:
   - 产品愿景和目标用户
   - 核心功能列表（P0/P1/P2 优先级）
   - 技术架构选型
   - 版本规划和里程碑

💡 下一步:
   1. 检查 docs/prompt/architecture.md 内容是否准确
   2. 确认 .claude/skills/migration.md 中的路径是否正确（如已创建）
   3. 按需补充 docs/prompt/ 中各 Prompt 文件的内容（与 AI 协作填写）
   4. 编辑 PRD.md 完善产品规划
   5. /req:branch init  配置分支策略
   6. /req:new <标题>   创建具体需求
```

**重新初始化成功**（使用 `--reinit` 参数）：
```
✅ 项目 "<project-name>" 重新初始化完成！

📁 检查并补充缺失内容:
   ✓ docs/requirements/active/      目录已存在
   ✓ docs/requirements/completed/   目录已存在
   ✓ docs/requirements/modules/     目录已存在
   + docs/requirements/templates/   模板目录
   + docs/requirements/templates/requirement-template.md  已复制
   + docs/requirements/templates/quick-template.md        已复制
   + docs/requirements/templates/prd-template.md          已复制
   + docs/requirements/modules/quick-fix.md  已生成（新增）
   + docs/requirements/PRD.md       已生成（新增）
   ✓ docs/prompt/architecture.md    已存在（或缺失时触发扫描+生成，见步骤 8）
   ✓ docs/prompt/ 通用 Prompt 文件  已检查（6 个骨架 + prompt-craft.md，缺失时补创建）
   ✓ .claude/skills/                已检查（如为空可按引导创建 Skill 文件）

🔗 当前仓库已绑定到此项目

📋 已生成 PRD 文档: docs/requirements/PRD.md
   请填写以下关键内容:
   - 产品愿景和目标用户
   - 核心功能列表（P0/P1/P2 优先级）
   - 技术架构选型
   - 版本规划和里程碑

💡 提示: --reinit 模式不会覆盖已有文件，仅补充缺失内容
```

**项目已存在时**（未使用 `--reinit`）：
```
⚠️ 项目 "<project-name>" 已存在

📊 项目状态:
   - 活跃需求: X 个
   - 已完成: Y 个
   - 主仓库: /path/to/primary/repo
   - 关联仓库: Z 个

💡 若要为历史项目补充缺失文件，请使用:
   /req:init <project-name> --reinit
```

---

## 错误处理

| 错误场景 | 处理方式 |
|---------|---------|
| 未提供项目名 | 提示：请提供项目名称，如 `/req:init my-project` |
| 项目名包含非法字符 | 提示：项目名只能包含字母、数字、连字符 |
| 本地目录已存在（无 --reinit） | 提示：本地需求目录已存在，可使用 `--reinit` 补充缺失文件 |
| 权限不足 | 提示：无法创建目录，请检查权限 |

---

## 用户输入

$ARGUMENTS
