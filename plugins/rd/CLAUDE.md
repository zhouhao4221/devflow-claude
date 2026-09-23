# rd 插件 — 目录级说明

> 本文件只在处理 `plugins/rd/` 下文件时加载；全局规则见仓库根 `CLAUDE.md`。

## 项目架构适配（init / dev / test / release / update 如何读下游项目）

插件不内置项目架构细节，从下游项目的 `docs/prompt/` 和 `.claude/skills/` 读取。

| 位置 | 内容 | 加载方式 |
|------|------|---------|
| `CLAUDE.md` | AI 行为指令（通用规则、引用指针） | 每次会话自动加载 |
| `docs/prompt/architecture.md` | 项目架构知识（分层、规范、技术栈） | `/rd:dev`、`/rd:test` 显式 Read |
| `docs/prompt/release.md` | 项目发版规则 | `/rd:release` 步骤 0 Read |
| `docs/prompt/` Prompt 库（`code-generation`/`refactoring`/`test-generation`/`testing`/`error-diagnosis`/`pr-review`/`requirement-structuring`） | 各方面项目特有规范，统一 5 节骨架 | 对应命令按需 Read（`/rd:dev`/`do`/`test*`/`fix`/`pr review`/`new`·`edit`），缺失降级，非阻塞 |
| `docs/requirements/specs/` | 公共知识层（枚举、规则、契约摘要） | 命令按仓库角色注入 |
| `.devflow/settings.json(.local)` | 结构化配置 | 命令读取字段（local 覆盖同名） |
| `.claude/skills/<concern>.md` | 窄知识具体约定（如路径变量） | 命令扫描全量注入 |

- `/rd:init` 扫描项目结构生成 `docs/prompt/architecture.md`；CLAUDE.md 只留引用指针，不内嵌架构内容。Prompt 库其余 7 文件从 `templates/prompt-snippets/` 复制空骨架（仅当不存在），供下游按项目填充；骨架格式见 `prompt-craft.md`。
- 项目级 skill 文件名反映关注点（`migration.md` ✅，`config.md` ❌）；`docs/prompt/` 文件按需 Read，缺失时打印创建提示（非阻塞）。
- 现有示例：`.claude/skills/migration.md` 声明 `MIGRATIONS_DIR`，供 `/rd:dev` 写入、`/rd:release` 扫描合并。Changelog 目录固定 `docs/changelogs/`，不参与配置。
- **Prompt 结构验证**：`plugins/rd/schemas/prompt-schema.md` 定义各命令期望的 prompt 文件结构；`/rd:update` 拉新版本后对照检查，缺必需章节报错、缺推荐章节警告。

## 核心机制（双轨需求 / 存储 / Hooks / 分支与 issue）

### 双轨需求

| | REQ（正式需求） | QUICK（快速修复） |
|---|---|---|
| 生命周期 | 📝 草稿 → 👀 待评审 → ✅ 评审通过 → 🔨 开发中 → 🧪 测试中 → 🎉 已完成 | 草稿 → 开发中 → 测试中 → 已完成（只跳过评审） |
| 入口 | `/rd:new` | `/rd:new-quick` |
| 模板 | `requirement-template.md`（一~十一章） | `quick-template.md`（问题/方案/验证/记录） |
| 开发门槛 | `/rd:dev` 拒绝未评审的 REQ | 草稿即可开发（方案在 `new-quick` 内确认，不是状态） |
| 编号 | `REQ-XXX` | `QUICK-XXX`（扫描本地需求目录取最大值+1） |

状态流转由命令驱动，REQ 与 QUICK 共用同一组命令：`/rd:req-review`（提审含 AI 预审）→ `pass/reject`（仅 REQ） · `/rd:dev`（自动） · `/rd:test`（自动，QUICK 按「验证方式」验证）· `/rd:done`（必须 y/n 确认，门槛统一「测试中」）。状态机唯一定义在 `shared/_storage.md`「双轨状态机」；需求索引不落盘，`/rd:req` 实时渲染。`/rd:upgrade <QUICK-XXX>` 将未完成的 QUICK 升级为 REQ（4 阶段扩 6 阶段）。无文档的轻量任务走 `/rd:fix`（修 bug，含根因分析）和 `/rd:do`（优化/重构/升级，AI 选流程）。

### 存储（无全局缓存）

需求文档**唯一事实源**是 primary 仓库的 `requirementsDir`（默认 `docs/requirements/`，纳入 git）。**无全局缓存**：readonly 仓库经 `.devflow/settings.local.json` 的 `requirementSource.path` **直读**主仓需求目录，不复制、不同步。

**无同步**：需求只有一份，写入即生效，无 PostToolUse 同步 Hook、无 cp。（v2.x 的 `~/.claude-requirements/` 全局缓存 + `sync-cache.sh` 已于 v3 移除——breaking change，旧项目需跑 `/rd:migrate` + readonly 重新 `/rd:use` 绑定。）

**仓库角色**（`requirementRole`）：`primary` 读写本仓 `requirementsDir`；`readonly` 无本地需求目录、经 `requirementSource.path` 直读主仓、`/rd:dev` 跳过所有文档写入。新增写操作命令必须考虑 readonly 跳过逻辑。不受角色限制的命令：`fix`/`do`/`issue`/`branch`。

### Hooks（`plugins/rd/hooks/hooks.json`）

| 时机 | 脚本 | timeout | 行为 |
|------|------|---------|------|
| SessionStart | session-context.sh | 10s | 注入需求上下文；未初始化/未配分支策略时输出引导 |
| PreToolUse(Bash) | confirm-before-commit.sh | 120s | 默认放行；仅当 `.claude/.req-confirm-commit` 存在时拦截 git commit / mv·rm 需求文件 |
| PostToolUse(Write/Edit) | validate-requirement.sh | 5s | 校验文档章节 |

**两个 marker（勿混淆）**：
- `.claude/.req-confirm-commit`：**确认开关**（常驻）。存在 = 启用提交拦截；默认不存在 = 全部直通。用户说「开启提交确认」→ Claude `touch`，「关闭」→ `rm`。
- `.claude/.req-auto`：**自动化豁免**（临时，mtime 10 分钟 TTL）。`/rd:fix --auto` 流程开始 `touch`、结束 `rm`；存在且有效时让 Hook 放行 commit 弹框。`--auto` 还跳过命令层文本交互（方案确认、类型选择、issue 关闭询问）并自动串联 commit→push→PR。两者均在 `.gitignore`。

### 分支与 issue

`/rd:branch init` 配置策略：`github-flow`（main↔main）· `git-flow`（develop↔develop，hotfix 建两个 PR）· `trunk-based`。命名 `<prefix>REQ-XXX-<slug>[-iN]`（slug ≤5 词 kebab-case，`-iN` 为关联 issue 后缀）。

**CLI 选择**（`repoType`）：GitHub → `gh`；Gitea → **优先 `tea`**（login URL 匹配 `giteaUrl`），不支持的操作（评论列表、PR diff/review、标签增删、Release 附件）回退 `curl + giteaToken`。绝不自动 `tea login add`。OWNER/REPO 从 `git remote origin` 解析；`giteaUrl` 只从配置读，禁止从 remote 猜测。

`--from-issue=#N` 全链路：创建时拉 issue → 编号写入文档 `issue` 字段（无文档则靠分支名 `-iN` 后缀）→ commit 追加 `closes #N` → done 时询问 API 关闭（`--auto` 跳过询问，靠 `closes #N` 自动关）。
