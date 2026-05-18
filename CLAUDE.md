# CLAUDE.md

## 项目概述

DevFlow：Claude Code 插件工具集，通过 `marketplace.json` 统一管理。

```
plugins/
├── req/    # 需求管理（commands/ skills/ hooks/ scripts/ templates/）
├── api/    # API 对接（commands/ skills/ scripts/）
├── pm/     # 项目管理助手（commands/ skills/ scripts/）
└── diag/   # 生产诊断（commands/ skills/ hooks/ scripts/ templates/）
```

## 存储架构

需求双存储：主存储 `docs/requirements/`（纳入 git，primary 仓库）+ 全局缓存 `~/.claude-requirements/projects/<name>/`（跨仓库共享）。

**仓库角色**（`requirementRole` in `settings.local.json`）：`primary` 读写本地并自动同步缓存；`readonly` 仅读缓存，禁止写操作。

**同步**：Write/Edit 触发 PostToolUse Hook，以本地为准覆盖缓存，无冲突检测。范围：REQ-XXX、QUICK-XXX、modules/、specs/、PRD.md。

## 命令结构

命令文件（`commands/*.md`）YAML frontmatter：

```yaml
---
description: 命令简介
argument-hint: "[参数] [--选项=值]"
allowed-tools: Read, Glob, Grep
model: claude-haiku-4-5-20251001   # 省略则继承会话模型
---
```

**模型分级**：

| 策略 | 适用 | 做法 |
|------|------|------|
| 显式 haiku | 读取/展示/机械操作/规则明确的状态流转 | `model: claude-haiku-4-5-20251001` |
| 不指定 | 深度理解/架构设计/需求生成/内容创作 | 省略 `model` |

> 避免显式 sonnet：其 1M context 变体会触发 extra-usage 付费墙；Haiku 200K 对机械命令足够，复杂命令由用户会话模型决定档位。

haiku 命令：`/req`、`/req:status/show/prd/projects/cache/use/done/update-template/changelog/help/commit/review/upgrade/branch/release/modules/specs/init/migrate/test_regression`、`/api:api/search/help`、`/pm:pm/standup/export/help`

默认命令：`/req:new/do/fix/dev/test/test_new/review-pr/prd-edit/edit/new-quick/pr/issue/split`

**allowed-tools**：只读命令不触发 Write/Edit/Bash。**Token 节约**：单文件 < 30 KB；> 50 KB 拆主+rationale；详见 [`docs/design/token-optimization.md`](./docs/design/token-optimization.md)。

**命令文件写法原则**：只写 Claude 不能从训练数据推断的内容——平台差异约束、非显而易见的业务规则、输出格式。不写 curl/gh/tea 的完整实现命令、Python 代码、URL 模板。判断标准：这条内容 Claude 能从 API 文档或常识推断吗？能 → 不写；不能（如"Gitea labels 必须走独立端点"）→ 写。

## 技能与钩子

**自动触发技能**：`requirement-analyzer`（新建/编辑需求）· `dev-guide`（`/req:dev`）· `prd-analyzer`（`/req:prd-edit`）· `code-impact-analyzer`（需求变更）· `test-guide`（测试命令）· `changelog-generator`（`/req:changelog`）· `natural-language-dispatcher`（自然语言操作）· `version-bumper`（`/req:release`，步骤 2.5 同步插件版本号）

**钩子**（`plugins/req/hooks/hooks.json`）：

| 时机 | 行为 |
|------|------|
| SessionStart | 注入需求上下文；未初始化时输出引导 |
| PreToolUse | 默认直通；`.claude/.req-confirm-commit` 存在时拦截 git commit/mv/rm 需求文件 |
| PostToolUse | 验证文档格式（5s）+ 强制同步缓存（5s） |

交互型 hook 超时 120s，自动执行 5s。写需求文档的命令触发缓存同步，只读命令不触发。

## Git 分支管理

`/req:branch init` 配置策略：`github-flow`（main↔main）· `git-flow`（develop↔develop）· `trunk-based`（短期分支）。

分支命名：`<prefix>REQ-XXX-<slug>[-iN]`（slug ≤5 词 kebab-case，`-iN` 为关联 issue 后缀）。

配置存 `settings.local.json` → `branchStrategy`（`repoType`、`mainBranch`、`developBranch`、`reviewers` 等）。CLI 优先：GitHub → `gh`；Gitea → `tea` 优先，回退 `curl + giteaToken`。

---

## 需求生命周期

`📝 草稿 → 👀 待评审 → ✅ 评审通过 → 🔨 开发中 → 🧪 测试中 → 🎉 已完成`

状态流转由命令驱动：`/req:review pass/reject` · `/req:dev`（自动，REQ 须先评审） · `/req:test`（自动）· `/req:done`（必须 y/n 确认）。

Write/Edit/Bash 默认全部直通。用户说"开启提交确认"→ Claude 创建 `.claude/.req-confirm-commit`；说"关闭"→ 删除。

---

## 核心概念

**跨仓库**：primary 仓库写本地并同步缓存，readonly 仓库直接读缓存。`/req:init <name>` 初始化，`/req:use <name>` 绑定，readonly 可用 `/req:specs show` 查看规范文档。

**模块 vs 需求**：模块是技术架构维度的功能域（稳定），需求是业务维度的可交付单元（不断新增）。一个 REQ 对应一个可独立交付的功能，不按技术层拆分。

**PRD vs REQ**：PRD 是项目级产品文档，REQ 从中派生。`/req:new` 自动追加索引，`/req:done` 自动更新状态。

**前后端需求**：分开创建（类型：后端/前端/全栈），通过「关联需求」字段互相引用。筛选：`/req --type=后端 --module=用户`。

---

## 项目架构适配

插件不内置项目架构细节，从项目的 `docs/prompt/` 和 `.claude/skills/` 读取。

**项目架构文件**：`/req:init` 扫描项目结构自动生成 `docs/prompt/architecture.md`（技术栈、分层架构、文件命名、开发规范、测试规范），`/req:dev`、`/req:test` 运行时显式 Read 此文件。CLAUDE.md 只保留一行引用指针，不内嵌架构内容。

**项目级 Skill 扩展**：插件命令不硬编码项目特有知识，由项目在 `.claude/skills/` 下创建 skill 文件注入（单一职责的具体约定，如路径变量）。

| 位置 | 内容 | 加载方式 |
|------|------|---------|
| `CLAUDE.md` | AI 行为指令（通用规则、引用指针） | 每次会话自动加载 |
| `docs/prompt/architecture.md` | 项目架构知识（分层、规范、技术栈） | 命令显式 Read |
| `docs/prompt/release.md` | 项目发版规则（版本号文件、前置检查、发版后步骤、额外附件） | `/req:release` 步骤 0 Read |
| `docs/requirements/specs/` | 项目级公共知识层（枚举、规则、契约等散落代码知识的摘要） | 命令按仓库角色注入 |
| `settings.local.json` | 结构化配置（分支策略、仓库角色、token） | 命令读取配置字段 |
| `.claude/skills/<concern>.md` | 具体约定（路径变量等窄知识） | 命令扫描全量注入 |

规范：skill 文件名反映关注点（`migration.md` ✅，`config.md` ❌）；`docs/prompt/` 文件按需显式 Read，缺失时打印创建提示（非阻塞）。

**Prompt 文件结构验证**：插件在 `plugins/req/schemas/prompt-schema.md` 中定义各命令期望的 `docs/prompt/` 文件结构（必需章节 / 推荐章节 / 可选文件）。`/req:update` 拉取新版本后自动对照 schema 检查项目 prompt 文件是否覆盖，缺失必需章节时报错，推荐章节缺失时警告。

现有示例：`.claude/skills/migration.md` → 声明 `MIGRATIONS_DIR`（migration SQL 存放目录），供 `/req:dev` 写入、`/req:release` 扫描合并。Changelog 目录固定为 `docs/changelogs/`，不参与配置。

---

## pm 插件

req 产出数据的只读消费者（不触发缓存同步），从 PRD/需求文档/Git 记录生成汇报、统计、方案。primary/readonly 均可用。命令：`/pm` · `weekly` · `monthly` · `milestone` · `stats` · `progress` · `plan` · `brief` · `risk` · `standup` · `ask` · `export`。输出到 `docs/reports/`。

## uat 插件

UI 验收测试，从 v2.32.0 起由 `qa` 重命名。在项目本地存储测试流程和报告，不依赖需求缓存。

存储：`docs/uat/flows/`（测试流程文档）· `docs/uat/reports/`（测试报告）。

命令：`/uat:init` · `/uat:new [module]` · `/uat:run [module]` · `/uat:report` · `/uat:bug`。技能：`uat-executor`。

## diag 插件

只读诊断 + 修复建议，与 [claude-safe-ops](https://github.com/zhouhao4221/claude-safe-ops) 互补。边界：SSH/容器只读 ✅ · DB SELECT ✅ · `/tmp` 临时写 ⚠️ · 其他写操作/Edit/Write ❌。

风控 Hook（全部 `deny` 阻断）：敏感输入拦截 · Hook 完整性校验 · SSH 主机白名单 · 命令动词白名单 · 写操作阻断 · JSONL 审计（30 天）。

命令：`/diag:init` · `/diag:diagnose` · `/diag:audit`。技能：`stack-analyzer`。存储：`~/.claude-diag/`。依赖：`python3` · `jq` · `yq`/`pyyaml` · `ssh`。
