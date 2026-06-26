# CLAUDE.md

## 项目本质

DevFlow 是一个 **Claude Code 插件市场（marketplace）**，对外发布 5 个插件，覆盖软件研发全生命周期。

> 在本仓库工作 = **开发/维护这些插件本身**，而非使用它们。下游用户安装插件后在他们自己的项目里跑 `/req:*`、`/pm:*` 等命令。本仓库里出现的 `docs/requirements/`、`docs/reports/` 等是插件自身的 dogfooding 产物（DevFlow 用自己的 req 插件管理自己的需求）。

面向**下游用户**的文档是 `README.md`（+ 英/韩双语）和 `docs/tutorial.md`；本文件（CLAUDE.md）面向**在本仓库工作的 AI 与维护者**。

## 核心心智模型（最重要）

1. **命令/技能文件是「给 Claude 的指令文档」，不是可执行代码。** `commands/<name>.md` 与 `skills/<name>/SKILL.md` 是自然语言指令，运行时由 Claude 解读执行。**改流程 = 改 `.md`**，通常无需动脚本。
2. **脚本（`scripts/`）只做确定性的副作用**：缓存同步、文档校验、状态字段写入、Hook 拦截、外部数据解析（如 Swagger）。不承载业务判断。
3. **共享逻辑抽到 `commands/_*.md`**（下划线前缀），命令用 Markdown 链接引用，避免重复、控制 token。新命令链接到具体专题文件（`_storage.md`/`_branch.md`/`_issue.md`/`_gitea_cli.md`/`_granularity.md`/`_template.md`），不要链 `_common.md`（它只是索引）。
4. **只写 Claude 推不出来的内容**：平台差异约束、非显而易见的业务规则、输出格式。不写 curl/gh/tea 完整命令、Python 实现、URL 模板。判断标准：能从 API 文档或常识推断 → 不写；不能（如「Gitea labels 必须走独立端点」）→ 写。

## 插件全景

| 插件 | 版本 | 职责 | 目录构成 |
|------|------|------|---------|
| **req** | 3.23.0 | 需求全流程：分析→评审→开发→测试→归档 + 分支/PR/issue/版本 | commands skills hooks scripts templates schemas |
| **pm** | 0.5.0 | 项目管理助手：周报/月报/统计/风险/方案（只读消费 req 数据） | commands skills scripts |
| **api** | 0.4.0 | 前端 API 对接：Swagger 解析、字段映射、TS 代码生成 | commands skills scripts docs tests |
| **diag** | 0.2.0 | 生产诊断（**全程只读**）：SSH 拉日志→解析堆栈→关联代码→修复建议 | commands skills hooks scripts templates tests |
| **uat** | 1.3.0 | UI 验收测试：AI 按流程文档逐场景执行界面操作（前身 `qa`） | commands skills templates |

整体版本 `marketplace.json` = 2.36.0。**事实源是各 `plugin.json` + `marketplace.json`，不是 README**——README/tutorial 的版本号已过时，且只覆盖 req/pm/api，未收录 diag/uat（已知文档债务，非功能不成熟；diag 由 REQ-001、uat 由 REQ-002 完整交付）。

## 命令与技能结构

每个能力同时以两种形态分发，**command 为唯一权威源，skill 由 `scripts/gen-skills.py` 自动派生**（REQ-003）：

- **`commands/<name>.md`**：权威完整版。frontmatter 含 `description`/`argument-hint`/`allowed-tools`/`model`，可引用同目录共享子文件（`_storage.md`、`_gitea_cli.md`、`release-rationale.md` 等）。
- **`skills/<name>/SKILL.md`**：由 `scripts/gen-skills.py` 从同名 command 自动派生，供不支持 slash 的 Claude 客户端使用。**禁止手改**——改动应在 command 进行后重新生成。派生规则：frontmatter 降级为仅 `name` + `description`（无 `model`/`allowed-tools`/`argument-hint`，故继承会话模型）；command 引用的共享子文件（含其传递依赖）内联为文末「附录」，使 skill 自包含、无悬空链接。

命令 frontmatter：

```yaml
---
description: 命令简介
argument-hint: "[参数] [--选项=值]"
allowed-tools: Read, Glob, Grep
model: claude-haiku-4-5-20251001   # 省略则继承会话模型
---
```

**模型分级**（实际只有两档；README 的 Haiku/Sonnet/Opus 三档表已过时）：

| 策略 | 适用 | 做法 |
|------|------|------|
| 显式 haiku | 纯查询/展示/格式化输出/配置/规则明确的状态流转 | `model: claude-haiku-4-5-20251001` |
| 不指定 | 分析代码/生成方案/多轮需求讨论/AI 审查/架构理解 | 省略 `model` |

> 避免显式 sonnet：其 1M context 变体会触发 extra-usage 付费墙；Haiku 200K 对机械命令足够，复杂命令交给会话模型。
> 模型分级**仅对 `commands/*.md` 命令调用生效**；以技能形态调用时无 `model` 字段，一律继承会话模型。
> 边界例外：`done`/`review`/`upgrade`/`release` 虽含写操作，但流程被模板和显式参数高度约束，仍用 haiku。

**allowed-tools**：只读命令不声明 Write/Edit/Bash。**Token 节约**：单文件 < 30 KB；> 50 KB 拆主文件 + rationale；详见 [`docs/design/token-optimization.md`](./docs/design/token-optimization.md)。

## 自动触发技能（helper skill）

`skills/` 里大多数与命令同名（镜像入口）；少数是**真正的 helper skill**——被命令运行时按 `description` 自动激活，提供细化引导，不与命令同名：

| 插件 | helper skill |
|------|-------------|
| req | `requirement-analyzer`（new/edit）· `prd-analyzer`（prd-edit）· `dev-guide`（dev，读 architecture.md 分层引导）· `test-guide`（test*）· `quick-fix-guide`（new-quick）· `issue-guide`（issue）· `changelog-generator`（changelog）· `version-bumper`（release，按 semver 推导各插件版本）· `code-impact-analyzer`（需求变更/影响评估）· `natural-language-dispatcher`（自然语言意图→命令映射）· `release-rationale`（release 设计原理速查） |
| pm | `report-generator`（各生成类命令，整合数据为面向受众的文档，禁用 emoji 便于导出） |
| diag | `stack-analyzer`（仅 diagnose 期间，多语言堆栈解析为结构化 YAML） |
| uat | `uat-executor`（仅 run 期间，意图驱动执行界面操作） |
| api | `api-field-mapper`（编辑前端 `.ts/.tsx/.vue` 时被动提示字段映射） |

> `natural-language-dispatcher` 是 req 的关键入口：用户用中文自然语言（非斜杠命令）表达意图时自动激活，识别意图→映射命令。`requirement-analyzer`/`prd-analyzer` 受 Memory 隔离约束：禁止 memory 影响文档结构/内容/格式。

---

## req 插件核心机制

### 双轨需求

| | REQ（正式需求） | QUICK（快速修复） |
|---|---|---|
| 生命周期 | 📝 草稿 → 👀 待评审 → ✅ 评审通过 → 🔨 开发中 → 🧪 测试中 → 🎉 已完成 | 草稿 → 方案确认 → 开发中 → 已完成（跳过评审+测试） |
| 入口 | `/req:new` | `/req:new-quick` |
| 模板 | `requirement-template.md`（一~十一章） | `quick-template.md`（问题/方案/验证/记录） |
| 开发门槛 | `/req:dev` 拒绝未评审的 REQ | 草稿即可开发 |
| 编号 | `REQ-XXX` | `QUICK-XXX`（扫描本地需求目录取最大值+1） |

状态流转由命令驱动：`/req:review pass/reject` · `/req:dev`（自动） · `/req:test`（自动）· `/req:done`（必须 y/n 确认）。`/req:upgrade <QUICK-XXX>` 将未完成的 QUICK 升级为 REQ（4 阶段扩 6 阶段）。无文档的轻量任务走 `/req:fix`（修 bug，含根因分析）和 `/req:do`（优化/重构/升级，AI 选流程）。

### 存储（无全局缓存）

需求文档**唯一事实源**是 primary 仓库的 `requirementsDir`（默认 `docs/requirements/`，纳入 git）。**无全局缓存**：readonly 仓库经 `.devflow/settings.local.json` 的 `requirementSource.path` **直读**主仓需求目录，不复制、不同步。

`docs/requirements/` 子目录：`active/`（进行中）· `completed/`（归档）· `modules/`（模块文档）· `specs/`（规范文档，跨仓库共享）· `templates/`（4 个模板）· `PRD.md` + `INDEX.md`。

**无同步**：需求只有一份，写入即生效，无 PostToolUse 同步 Hook、无 cp。（v2.x 的 `~/.claude-requirements/` 全局缓存 + `sync-cache.sh` 已于 v3 移除——breaking change，旧项目需跑 `migrate-config.sh` + readonly 重新 `/req:use` 绑定。）

**仓库角色**（`requirementRole`）：`primary` 读写本仓 `requirementsDir`；`readonly` 无本地需求目录、经 `requirementSource.path` 直读主仓、`/req:dev` 跳过所有文档写入。新增写操作命令必须考虑 readonly 跳过逻辑。不受角色限制的命令：`fix`/`do`/`issue`/`branch`。

### Hooks（`plugins/req/hooks/hooks.json`）

| 时机 | 脚本 | timeout | 行为 |
|------|------|---------|------|
| SessionStart | session-context.sh | 10s | 注入需求上下文；未初始化/未配分支策略时输出引导 |
| PreToolUse(Bash) | confirm-before-commit.sh | 120s | 默认放行；仅当 `.claude/.req-confirm-commit` 存在时拦截 git commit / mv·rm 需求文件 |
| PostToolUse(Write/Edit) | validate-requirement.sh | 5s | 校验文档章节 |

**两个 marker（勿混淆）**：
- `.claude/.req-confirm-commit`：**确认开关**（常驻）。存在 = 启用提交拦截；默认不存在 = 全部直通。用户说「开启提交确认」→ Claude `touch`，「关闭」→ `rm`。
- `.claude/.req-auto`：**自动化豁免**（临时，mtime 10 分钟 TTL）。`/req:fix --auto` 流程开始 `touch`、结束 `rm`；存在且有效时让 Hook 放行 commit 弹框。`--auto` 还跳过命令层文本交互（方案确认、类型选择、issue 关闭询问）并自动串联 commit→push→PR。两者均在 `.gitignore`。

### 分支与 issue

`/req:branch init` 配置策略：`github-flow`（main↔main）· `git-flow`（develop↔develop，hotfix 建两个 PR）· `trunk-based`。命名 `<prefix>REQ-XXX-<slug>[-iN]`（slug ≤5 词 kebab-case，`-iN` 为关联 issue 后缀）。

**CLI 选择**（`repoType`）：GitHub → `gh`；Gitea → **优先 `tea`**（login URL 匹配 `giteaUrl`），不支持的操作（评论列表、PR diff/review、标签增删、Release 附件）回退 `curl + giteaToken`。绝不自动 `tea login add`。OWNER/REPO 从 `git remote origin` 解析；`giteaUrl` 只从配置读，禁止从 remote 猜测。

`--from-issue=#N` 全链路：创建时拉 issue → 编号写入文档 `issue` 字段（无文档则靠分支名 `-iN` 后缀）→ commit 追加 `closes #N` → done 时询问 API 关闭（`--auto` 跳过询问，靠 `closes #N` 自动关）。

---

## 项目级配置约定

`.devflow/settings.json`（团队共享、入 git，放非密钥）+ `.devflow/settings.local.json`（不入 git，放密钥/本机路径）。读取时 local 覆盖同名。**Claude Code 自身的 hooks/permissions 仍在 `.claude/settings.json`，两者互不迁移**；项目级窄知识 skill 仍在 `.claude/skills/`。

| 字段 | 文件 | 控制 | 消费者 |
|------|------|------|--------|
| `requirementProject` | settings | 项目名（标签/显示用） | req、pm |
| `requirementRole` | settings | `primary`/`readonly` | req、pm |
| `requirementsDir` | settings | 需求目录，默认 `docs/requirements`，可改 | req、pm |
| `branchStrategy`（对象，不含 token） | settings | `repoType`/`giteaUrl`/`mainBranch`/`developBranch`/`*Prefix`/`branchFrom`/`mergeTarget`/`mergeMethod`/`reviewers` 等 | req、uat |
| `giteaToken` | settings.local | Gitea API token | req、uat |
| `requirementSource`（`{path,project?}`） | settings.local | **readonly 专用**：指向 primary 仓库根的本机绝对路径，据此直读主仓 | req、pm |

跨插件共享：pm 复用 `requirementProject`/`requirementRole`/`requirementsDir`；uat 复用 `branchStrategy`/`giteaToken`。

---

## 项目架构适配

插件不内置项目架构细节，从下游项目的 `docs/prompt/` 和 `.claude/skills/` 读取。

| 位置 | 内容 | 加载方式 |
|------|------|---------|
| `CLAUDE.md` | AI 行为指令（通用规则、引用指针） | 每次会话自动加载 |
| `docs/prompt/architecture.md` | 项目架构知识（分层、规范、技术栈） | `/req:dev`、`/req:test` 显式 Read |
| `docs/prompt/release.md` | 项目发版规则 | `/req:release` 步骤 0 Read |
| `docs/prompt/` Prompt 库（`code-generation`/`refactoring`/`test-generation`/`testing`/`error-diagnosis`/`pr-review`/`requirement-structuring`） | 各方面项目特有规范，统一 5 节骨架 | 对应命令按需 Read（`/req:dev`/`do`/`test*`/`fix`/`review-pr`/`new`·`edit`），缺失降级，非阻塞 |
| `docs/requirements/specs/` | 公共知识层（枚举、规则、契约摘要） | 命令按仓库角色注入 |
| `settings.local.json` | 结构化配置 | 命令读取字段 |
| `.claude/skills/<concern>.md` | 窄知识具体约定（如路径变量） | 命令扫描全量注入 |

- `/req:init` 扫描项目结构生成 `docs/prompt/architecture.md`；CLAUDE.md 只留引用指针，不内嵌架构内容。Prompt 库其余 7 文件从 `templates/prompt-snippets/` 复制空骨架（仅当不存在），供下游按项目填充；骨架格式见 `prompt-craft.md`。
- 项目级 skill 文件名反映关注点（`migration.md` ✅，`config.md` ❌）；`docs/prompt/` 文件按需 Read，缺失时打印创建提示（非阻塞）。
- 现有示例：`.claude/skills/migration.md` 声明 `MIGRATIONS_DIR`，供 `/req:dev` 写入、`/req:release` 扫描合并。Changelog 目录固定 `docs/changelogs/`，不参与配置。
- **Prompt 结构验证**：`plugins/req/schemas/prompt-schema.md` 定义各命令期望的 prompt 文件结构；`/req:update` 拉新版本后对照检查，缺必需章节报错、缺推荐章节警告。

---

## 其他插件要点

**pm** — req 数据的**只读消费者**（不触发缓存同步），从 PRD/需求文档/Git 记录生成内容。无 req 数据时仍可用（仅 Git 指标）。命令：`/pm` · `weekly` · `monthly` · `milestone` · `stats` · `progress` · `plan` · `risk` · `standup` · `ask` · `brief` · `export`。输出到 `docs/reports/`。

**api** — 前端 API 对接。配置 `.api-config.json`（项目根，入 git）；Swagger **不缓存**，每次实时解析（`scripts/swagger-parser.py`，无第三方依赖）。产物：TS 类型→`{typeDir}`、请求函数→`{outputDir}`；gen 做字段 diff + 引用文件影响分析后才写入。命令：`/api:import` · `search` · `map` · `gen` · `config` · `help`。

**diag** — 生产诊断，**全程只读**，与 [claude-safe-ops](https://github.com/zhouhao4221/claude-safe-ops) 互补。边界：SSH 只读命令 ✅ · DB SELECT ✅ · 远端 `/tmp/claude-diag-*` append ⚠️ · 写操作/Edit/Write ❌。**6 个风控 Hook 全 deny**：敏感输入拦截 · Hook 完整性自检（防风控链被禁用）· SSH 主机白名单 · 命令动词白名单 · 写操作+本地提权阻断 · JSONL 审计（30 天）。**改动 hooks/ 须同步 hooks.json 注册，否则被 validate-hooks 拦截。** 命令：`/diag:init` · `diagnose` · `audit`。存储 `~/.claude-diag/`。依赖：`python3` · `jq` · `yq`/`pyyaml` · `ssh`。

**uat** — UI 验收测试。存储：`docs/uat/flows/`（流程文档，入 git）· `docs/uat/reports/` + `screenshots/`（`.gitignore`）。`/uat:run` 激活 `uat-executor`，意图驱动、不依赖预写选择器（testid 为可选加速）。结果四态 PASS/⚠️PASS/FAIL/SKIP。命令：`/uat:init`（首次必跑，装 skill 到项目）· `new` · `run` · `report` · `bug`（FAIL→issue）。

---

## 维护规则与易错点

1. 只改 `commands/<name>.md`（及其 `_*.md` 子文件），**绝不手改 `skills/*/SKILL.md`**；改完运行 `python3 scripts/gen-skills.py` 重新派生，发布前用 `--check` 校验一致性。helper skill（无同名 command）是手写的，生成器不碰。
2. 共享规则改 `_*.md`，勿在每个命令重复。
3. 缓存同步由 Hook 强制单向（本地→缓存覆盖），命令内不写显式 cp。
4. `requirementRole=readonly` 是贯穿多命令的分支点，新增写命令必须处理跳过。
5. 两个 marker：`.req-confirm-commit`=开关常驻，`.req-auto`=临时豁免有 TTL。
6. Gitea 一律「tea 优先、curl 回退」，禁止自动 `tea login add`。
7. 模型分级只有 haiku / 省略两档，按推理强度选；技能形态无 model 字段。
8. diag 的 6 个风控 Hook 是设计核心，改 hooks 必须同步注册。
9. `/req:release` 用 `version-bumper` 按 semver 推导各插件版本；发布事实源是 plugin.json，README 版本号需手动同步（当前已滞后）。
