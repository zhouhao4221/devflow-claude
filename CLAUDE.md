# CLAUDE.md

## 项目本质

DevFlow 是一个 **Claude Code 插件市场（marketplace）**，对外发布 4 个插件，覆盖软件研发全生命周期。

> 在本仓库工作 = **开发/维护这些插件本身**，而非使用它们。下游用户安装插件后在他们自己的项目里跑 `/rd:*`、`/pm:*` 等命令。本仓库里出现的 `docs/requirements/`、`docs/reports/` 等是插件自身的 dogfooding 产物（DevFlow 用自己的 rd 插件管理自己的需求）。

面向**下游用户**的文档是 `README.md`（+ 英/韩双语）和 `docs/tutorial.md`；本文件（CLAUDE.md）面向**在本仓库工作的 AI 与维护者**。

## 核心心智模型（最重要）

1. **命令/技能文件是「给 Claude 的指令文档」，不是可执行代码。** `commands/<name>.md` 与 `skills/<name>/SKILL.md` 是自然语言指令，运行时由 Claude 解读执行。**改流程 = 改 `.md`**，通常无需动脚本。
2. **脚本（`scripts/`）只做确定性的副作用**：文档校验、状态字段写入、Hook 拦截、布局守卫、外部数据解析（如 Swagger）。不承载业务判断。
3. **共享逻辑抽到 `plugins/<p>/shared/`**，命令用 `../shared/x.md` 链接引用，避免重复、控制 token；**不能放 `commands/` 下**（原因见「命令与技能结构」）。新命令链接到具体专题文件（`_storage`/`_branch`/`_issue`/`_gitea_cli`/`_granularity`/`_template`/`_delegate`/`_verify`/`_claude-md`），不要链 `_common.md`（它只是索引）。
4. **只写 Claude 推不出来的内容**：平台差异约束、非显而易见的业务规则、输出格式。不写 curl/gh/tea 完整命令、Python 实现、URL 模板。判断标准：能从 API 文档或常识推断 → 不写；不能（如「Gitea labels 必须走独立端点」）→ 写。

## 插件全景

| 插件 | 职责 |
|------|------|
| **rd** | 研发（R&D）全流程：需求分析→评审→开发→测试→归档 + 分支/PR/issue/版本（原 req） |
| **pm** | 项目管理助手：周报/月报/统计/风险/方案（只读消费 rd 数据） |
| **api** | 前端 API 对接：Swagger 解析、字段映射、TS 代码生成 |
| **diag** | 生产诊断（**全程只读**）：SSH 拉日志→解析堆栈→关联代码→修复建议 |

> uat（UI 验收测试，REQ-002 交付）已于 2026-09 移除：CLI 里驱动浏览器逐场景验收不合适。
>
> req 插件已于 v4（REQ-004）更名为 **rd**（R&D 研发）：只换命令前缀 `/req:` → `/rd:`（入口 `/rd:req`），`requirement*` 配置字段、`.claude/.req-*` marker、`REQ-XXX` 编号不变；过渡插件 req（`/req:help`）已移除，老用户按 README / 教程 1.6 迁移。

**版本事实源是各 `plugin.json` + `marketplace.json`**——README / tutorial 不写插件版本号。README 三语介绍全部 4 个插件（diag 另有 `plugins/diag/README.md`）；教程是 rd 全流程示例，不覆盖 pm / api / diag。

## 命令与技能结构

**command 是能力的唯一入口；`skills/` 下只放 helper skill**（REQ-003 的「命令→技能镜像」派生机制已于 2026-08 废止）：

- **`commands/<name>.md`**：唯一权威源，且 `commands/` 下**只能**放这类文件（必须有 frontmatter + `description`）。可引用 `../shared/` 里的共享子文件（`_storage.md`、`_gitea_cli.md`、`release-rationale.md` 等）。
- **`skills/<name>/SKILL.md`**：仅限**与任何命令都不同名**的 helper skill（见下节），全部手写。

**两类东西都会污染斜杠菜单，一律禁止**——Claude Code 把 `skills/` 下每个子目录、`commands/` 下每个 `.md` 都注册成菜单项：

- **命令同名 skill 镜像**：与 command 落在同一菜单、`description` 一模一样，每条命令重复两遍（`claude plugin details req` 里出现 `do, do`、`pr, pr`），多出的那份 description 还白占 always-on token。原 `scripts/gen-skills.py` 按 `SKIP_MIRROR` 名单派生的 51 个镜像（req 23 · pm 12 · api 6 · uat 6 · diag 4）已整体删除。
- **共享参考文档放 `commands/`**：`_storage.md` 之类会变出 `/rd:_storage` 等 12 个伪命令。统一放 `plugins/<p>/shared/`（rd 10 · pm 1 · api 1）。

`scripts/check-layout.py` 一次性守住四条：`skills/` 无命令镜像、`commands/` 无非命令文件、所有相对链接可达、插件内无过时引用（`.claude/settings*` 读写 DevFlow 字段、`sync-cache` / 全局缓存、缓存同步类表述、未定义的 `<plugin-path>`；迁移说明与 Claude Code 自身配置项豁免，确需保留加 `stale-ok`）。`--check` 报错退 1（发布前置，`.github/workflows/check.yml` 在每个 PR 上连同 diag 冒烟测试自动跑），不带参数则自动清理可清理的部分。`scripts/check-requirements.py --check` 守需求目录：`completed/` 内状态为已完成、`active/` 内不为已完成、状态与生命周期已勾格一致、编号唯一，同样进 CI 与发布前置。

命令 frontmatter：

```yaml
---
description: 命令简介
argument-hint: "[参数] [--选项=值]"
allowed-tools: Read, Glob, Grep
model: claude-haiku-4-5-20251001   # 省略则继承会话模型
---
```

**模型分级**（四档，README 三语版的四档表与本节保持一致）：

| 策略 | 适用 | 做法 |
|------|------|------|
| 显式 haiku | 纯查询/展示/格式化输出/配置/规则明确的状态流转/CLI 包装（branch·commit·issue·pr） | `model: claude-haiku-4-5-20251001` |
| 显式 sonnet | 数据聚合 + 成文类（pm 周报/月报/里程碑/统计/进度/简介/风险扫描）、有界的单元审查、有界的单文档编辑/分析（rd edit·prd-edit·split·new-quick）、模板化的测试与代码生成（rd test·test_new、api gen·map） | `model: claude-sonnet-5` |
| 不指定 | 会话模型够用的判断：多轮需求讨论（rd new）/需求评审预审（rd req-review）/架构归纳（rd init）/自由问答与方案（pm ask·plan） | 省略 `model` |
| 显式 best（Fable） | 需要高度思考、做错会写进代码或带偏修复方向：实现方案设计（rd dev·do）、根因分析（rd fix、diag diagnose）、代码审查（rd review） | `model: best` |

> **会话模型按非 Fable 设计**（2026-09-19 起）：假定会话默认是 Opus 5 / Sonnet 5，Fable 5.1（$10/$50，Opus 5 的 2 倍、sonnet 的 5 倍）只由 fable 档命令显式调用。省略档是「会话模型够用」档而非「最强档」：新命令按「会话模型做错的代价」定档，代价高才钉 fable，不因流程重要就抬档。会话模型本身是 Fable 时省略档也跑 Fable，只是贵，不影响正确性。
> fable 覆盖**只到当轮**（用户下一句起回到会话模型，官方文档 2026-09-19 核实）：dev/do/fix 的方案在命令轮用 Fable 定，确认后的实施跑会话模型；多轮讨论型命令钉 fable 只管得到第一轮，所以 `/rd:new` 留省略档。
> fable 档写别名 `model: best`，不写完整 ID（与 sonnet 相反）：`best` 在 Fable 可用时解析为 Fable 5.1，不可用（allowlist 排除、云厂商未上架）时退到 Opus 而不是可能更弱的会话模型，且按 provider 解析 ID；这一档要的是「当前最强」，不钉版本。
> sonnet 一律写 `claude-sonnet-5`（原生 1M 上下文、超 200K 不加价、Pro/Max 不计 extra usage，2026-08 核实）。`pm:plan`/`pm:ask` 需要真实推理，保持省略。
> `model` 是命令层的主成本杠杆。**输入密集型的有界任务**（读文档/读代码为主、产出受模板约束）一律显式 haiku/sonnet（2026-09 按此把 9 条命令降档）；fable 档只收推理密集的，读得多不是抬档理由。命令 frontmatter 与 skill 同源（除 `name`/`paths`），也能写 `effort`（2026-09-19 查文档，此前误记为仅 agent 支持），本仓库尚未启用。
> 模型分级**仅对 `commands/*.md` 命令调用生效**；helper skill 无 `model` 字段，运行在触发它的会话/命令模型下。
> 边界例外：`done`/`upgrade`/`release` 虽含写操作，但流程被模板和显式参数高度约束，仍用 haiku。反向例外：`req-review` 的 pass/reject 本是状态流转，但与提审的 AI 预审共用一条命令，随命令走省略档（REQ-007）。
> 按档位切命令：一条命令只能钉一档，子命令推理强度差异大时拆成两条命令，而不是整条抬档——`/rd:pr`（create/status/comments/merge，haiku）与 `/rd:review`（AI 审查 / 按评论改代码，fable）就是这样分的；`/rd:pr comments` 只读展示、`/rd:review comments` 才改代码。

**子任务委派**（命令内粒度，与整条命令的模型分级正交）：**主会话专注判断，执行外包给 subagent**——主会话做方案设计、跨文件一致性、闸门交互、验收复核，其余派给 `plugins/rd/agents/` 的 5 个 agent，原始输出不进主上下文。

| 只读型 | 用途 | | 可写型 | 用途 |
|--------|------|---|--------|------|
| `code-scout` haiku | 定位代码 | | `impl-worker` sonnet | 按实施单改一个独立单元 |
| `test-runner` haiku | 跑测试 | | `doc-writer` haiku | 按素材+骨架成文/回填章节 |
| `diff-digest` haiku | 压缩大 diff，可逐文件落盘 | | | |

规则见 `shared/_delegate.md`。派生 subagent 的命令 `allowed-tools` 必须列 `Agent`（`allowed-tools` 只做免确认预授权，**不限制**可用工具；没列时仍能派生，但每次都弹确认打断流程）。

**委派写操作有准入门槛**（`impl-worker`，见 `_delegate.md` 的「委派实施」）：方案已确认到文件级 + 单元互不依赖 + 契约已定死 + 有验收命令，四条全满足才派；新建抽象、跨层契约变更、方案仍在演化的首版实现一律主会话自己写。验收复核的是 `git diff` 实际内容，不是 subagent 的自述。**降档不是委派的理由**——委派是为了上下文隔离（避免开发中途触发压缩、让已确认方案被摘要化），不是为了把推理换成便宜模型。

**大 PR 代码质量审查不自研**：`/rd:review` 直接调原生 `/code-review`（多 agent 并行 + 逐条验证），档位按 PR 复杂度自动选。原 `file-reviewer` agent 已删：实测自研路径要主会话把 diff 抄进每个 prompt，「diff 不进主会话」不成立，还有误报。

**两条已知失败模式**（dogfooding 实测踩过）：① prompt 只给素材的磁盘路径而不内联正文 → subagent 把轮次耗在自己找文件上；② 一个 subagent 塞多个文件 → 撞 `maxTurns` 交出半成品。切分要细、素材要内联。

**allowed-tools**：只读命令不声明 Write/Edit/Bash。不声明 ≠ 禁用——调用时只是弹确认；命令 frontmatter 没有禁用工具的字段（`disallowed-tools` 仅 skill 支持），硬约束只能靠 Hook。**Token 节约**：单文件 < 30 KB；> 50 KB 拆主文件 + rationale；详见 [`docs/design/token-optimization.md`](./docs/design/token-optimization.md)。

## 自动触发技能（helper skill）

`skills/` 下**只有** helper skill——不与任何命令同名，由命令运行时按 `description` 自动激活，提供细化引导：

> `natural-language-dispatcher` 是 rd 的关键入口：用户用中文自然语言（非斜杠命令）表达意图时自动激活，识别意图→映射命令。`requirement-analyzer`/`prd-analyzer` 受 Memory 隔离约束：禁止 memory 影响文档结构/内容/格式。

---

## rd 插件核心机制

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

---

## 项目级配置约定

`.devflow/settings.json`（团队共享、入 git，放非密钥）+ `.devflow/settings.local.json`（不入 git，放密钥/本机路径）。读取时 local 覆盖同名。**Claude Code 自身的 hooks/permissions 仍在 `.claude/settings.json`，两者互不迁移**；项目级窄知识 skill 仍在 `.claude/skills/`。

| 字段 | 文件 | 控制 | 消费者 |
|------|------|------|--------|
| `requirementProject` | settings | 项目名（标签/显示用） | rd、pm |
| `requirementRole` | settings | `primary`/`readonly` | rd、pm |
| `requirementsDir` | settings | 需求目录，默认 `docs/requirements`，可改 | rd、pm |
| `branchStrategy`（对象，不含 token） | settings | `repoType`/`giteaUrl`/`mainBranch`/`developBranch`/`*Prefix`/`branchFrom`/`mergeTarget`/`mergeMethod`/`reviewers` 等 | rd |
| `giteaToken` | settings.local | Gitea API token | rd |
| `requirementSource`（`{path,project?}`） | settings.local | **readonly 专用**：指向 primary 仓库根的本机绝对路径，据此直读主仓 | rd、pm |

跨插件共享：pm 复用 `requirementProject`/`requirementRole`/`requirementsDir`。

---

## 项目架构适配

插件不内置项目架构细节，从下游项目的 `docs/prompt/`、`.claude/skills/`、`docs/requirements/specs/` 与 `.devflow/settings.json(.local)` 读取；各文件的加载时机、`/rd:init` 生成规则与 prompt 结构校验见 `plugins/rd/CLAUDE.md`。

---

## 其他插件要点

各插件专属约束在 `plugins/<p>/CLAUDE.md`（pm · api · diag），进入该目录工作时自动加载。

---

## 维护规则与易错点

1. 能力只改 `commands/<name>.md`（及其 `shared/_*.md` 子文件）；发布前跑 `python3 scripts/check-layout.py --check` 守住菜单、链接与过时引用，`python3 scripts/check-requirements.py --check` 守住需求目录一致性（CI 都会跑）。helper skill 手写，脚本不碰。
2. 共享规则改 `_*.md`，勿在每个命令重复。**共享文件之间不要用 Markdown 链接互引**（命令会顺着链接把整组 ~33KB 全读进来），互相提及写纯文本文件名，仅真实依赖用链接。
3. `requirementRole=readonly` 是贯穿多命令的分支点，新增写命令必须处理跳过。
4. **`scripts/` 下的 hook 脚本同样受配置约定管辖**：读 `.devflow/settings.json(.local)`、按 `requirementsDir` 解析路径、readonly 走 `requirementSource.path`，不得写死 `docs/requirements` 或回退 `.claude/`。改配置约定时必须连带检查 `hooks.json` 注册的每个脚本——v2.39.1 修的就是它们漏跟 v3 迁移、静默失效整整四个版本。**命令正文、`shared/`、helper skill 同理**：v2.42 之后又查出 req 十余条命令仍读写 `.claude/settings*`、按 v2 缓存同步执行（`branch init` 把配置写到 `.claude/`，其它命令读不到）。这类残留现由 `check-layout.py` 的过时引用检查兜底；约定再变时先改守卫规则，再让它列出遗留。
5. 两个 marker：`.req-confirm-commit`=开关常驻，`.req-auto`=临时豁免有 TTL。
6. Gitea 一律「tea 优先、curl 回退」，禁止自动 `tea login add`。
7. 模型分级四档（haiku / `claude-sonnet-5` / 省略 / `best` 即 Fable）按推理强度选，会话模型按非 Fable 设计，helper skill 无 `model` 字段；命令内高吞吐步骤走 subagent 委派而非降整条命令的档位。委派规则集中在 `shared/_delegate.md`：切分要细（一个 subagent 一个源文件/一个单元）、素材正文内联进 prompt（给路径必超轮）、写操作满足准入四条才派、超轮用 SendMessage 续问而非重派。详见「命令与技能结构」。
8. diag 的 6 个风控 Hook 是设计核心，改 hooks 必须同步注册。
9. `/rd:release` 用 `version-bumper` 按 semver 推导各插件版本；发布事实源是 plugin.json + marketplace.json，README / tutorial 不写插件版本号，无需同步。
10. **改 `agents/` 或任何插件文件后，本仓库工作区的改动对运行时无效**——Claude Code 运行时加载的是 `~/.claude/plugins/cache/devflow/<plugin>/<version>/`，`/plugin` 更新则从 `~/.claude/plugins/marketplaces/devflow`（GitHub 克隆）拉。cache 按版本号分目录，**不 bump 版本号 `/plugin` 会报「already at the latest version」而不更新**。要让改动生效并可实测，必须走完：提交 → push → `/plugin` 更新 → `/reload-plugins`。在此之前跑 subagent 测的都是旧定义。
