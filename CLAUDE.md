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

`scripts/check-layout.py` 一次性守住五条：`skills/` 无命令镜像、`commands/` 无非命令文件、命令不写 `model`（`inherit` 除外；frontmatter 按 YAML 解析，与运行时一致，需 PyYAML）、所有相对链接可达、插件内无过时引用（`.claude/settings*` 读写 DevFlow 字段、`sync-cache` / 全局缓存、缓存同步类表述、未定义的 `<plugin-path>`；迁移说明与 Claude Code 自身配置项豁免，确需保留加 `stale-ok`）。`--check` 报错退 1（发布前置，`.github/workflows/check.yml` 在每个 PR 上连同 diag 冒烟测试自动跑），不带参数则自动清理可清理的部分。`scripts/check-requirements.py --check` 守需求目录：`completed/` 内状态为已完成、`active/` 内不为已完成、状态与生命周期已勾格一致、编号唯一，同样进 CI 与发布前置。

**模型策略：命令与执行型 agent 都跑会话模型，只有思考型 agent 换 Fable**（2026-09-23，README 三语版「模型策略」一节与本节保持一致）：

| 层 | 模型 | effort | 说明 |
|----|------|--------|------|
| 命令（`commands/*.md`） | 会话模型 | 会话 | frontmatter 不写 `model`/`effort`（`model: inherit` 除外），`check-layout.py` 拦 `model` |
| 执行型 agent：test-runner · diff-digest · doc-writer | `inherit` | `medium` | 无需推理，但结果被主会话直接采信，漏报 / 错报代价高 |
| 执行型 agent：code-scout · impl-worker · ui-verifier | `inherit` | `high` | 需自主探索（找全调用链 / 找选择器）或写代码过验收；ui-verifier 的结论直接勾选需求文档，误判 PASS 代价最高 |
| 思考型 agent：rd `planner` · diag `root-cause` | `fable` | `xhigh` | 升档拿推理，不随用户调低会话 effort 变浅；失败回主会话降级 |

> **为什么废掉命令级三档（原 haiku 33 条 · sonnet 15 条）**：本机 2.1.239–2.1.280 约 200 次调用实测 0 次生效——`command_permissions` 记下了 `model`，实际调用全是会话模型。① 官方文档：auto 模式下「auto mode 不支持的模型」不被使用、会话保持当前模型，auto 只支持 Opus 4.6+/Sonnet 4.6+/Fable，**Haiku 按设计被忽略**，而 Pro/Max/Team 默认就是 auto；② sonnet 在 auto 下同样不生效，对应 anthropics/claude-code#81318（v2.1.220 起命令/skill 的 `model`/`effort` 覆盖失效的回归，未修）；③ 即便生效，覆盖是在同一对话里换模型，prompt cache 按模型隔离，长会话里要按新模型重写整段历史缓存，小命令多半比留在会话模型读缓存（Opus 5.5 $0.20/MTok）更贵。用户嫌贵用 `/model` 切整个会话。
> **思考交给 Fable，失败降级当前模型**（2026-09-19）：dev/do/fix/review 把方案设计、根因 + 修复、小 PR 审查派给 rd 的 `planner`，diag diagnose 把根因判断派给 diag 的 `root-cause`，两者 `model: fable`、只读。Fable 不可用时 agent 失败、错误回到主会话，主会话用当前模型按同一骨架接手并标注 `⚠️ Fable 不可用`（实测额度用尽时返回 `Agent terminated early due to an API error: You're out of usage credits…`，主会话不受影响）。会话模型本身是 Fable 时照常工作，只是贵。钉在命令上的 Fable 反而会在额度用尽时直接报错、命令锁死（v5.0.1–v5.0.2 实测，`fallbackModel` 不处理计费 / 限流错误）——这是命令不写 `model` 的另一条理由。
> **执行型 agent 跟会话模型、按特性钉 effort**（2026-09-23）：写 `model: inherit`，模型由用户 `/model` 决定。effort 按「错了的代价 × 需要探索多少」定，不按「活简单」定：**下限 `medium`、不用 `low`**（主会话直接采信 agent 结论，省下的 thinking 抵不过一次漏报）；需要自主探索或写代码的 `high`（低 effort 工具调用更少更合并，易漏文件）；深度推理 `xhigh`（Fable 在 Claude Code 默认即 xhigh，钉住只为不随会话调低）。只用 medium/high/xhigh，inherit 下各代会话模型都支持。agent 的 `effort` 实测生效（2026-09-23，两个只差 effort 的临时 agent 同题同模型：low 共 720 输出 token / 30 秒，max 共 18956 / 3 分钟、单次 thinking 1.75 万；#81318 只影响命令 / skill）。jsonl 不记录 effort，再验证只能这样比输出 token。原 haiku（4 个）/ sonnet（impl-worker）弃用：Haiku 4.5 不支持 `effort`（原 `effort: low` 形同虚设）、只有 200K 上下文；Sonnet 5 缓存读价与 Opus 5.5 同为 $0.20/MTok，按本机用量只省约 30%。代价：会话是 Fable 时执行型 agent 也按 Fable 计费——想省钱就把会话切到 Opus 5.5 / Sonnet。命令 frontmatter 的 `effort` 同受 #81318 影响，不用。
> 按推理强度拆命令的旧规则（REQ-007：`/rd:pr` 只读/CLI 包装、`/rd:review` 审查改代码）保留为职责划分，不再对应模型档位。

**子任务委派**（命令内粒度；只有思考型 agent 换模型）：**Fable 想、主会话判断、subagent 执行**——方案设计交 `planner`（Fable），主会话做复核、跨文件一致性、闸门交互、验收，吞吐型步骤派给执行型 agent，原始输出不进主上下文。`plugins/rd/agents/` 共 7 个，diag 另有 `plugins/diag/agents/root-cause.md`。

规则见 `shared/_delegate.md`。派生 subagent 的命令 `allowed-tools` 必须列 `Agent`（`allowed-tools` 只做免确认预授权，**不限制**可用工具；没列时仍能派生，但每次都弹确认打断流程）。

**委派写操作有准入门槛**（`impl-worker`，见 `_delegate.md` 的「委派实施」）：方案已确认到文件级 + 单元互不依赖 + 契约已定死 + 有验收命令，四条全满足才派；新建抽象、跨层契约变更、方案仍在演化的首版实现一律主会话自己写。验收复核的是 `git diff` 实际内容，不是 subagent 的自述。**降档不是委派的理由**——委派是为了上下文隔离（避免开发中途触发压缩、让已确认方案被摘要化），执行型 agent 与会话同模型，不为省钱把推理拆出去。`planner` 反过来是升档：为拿到 Fable 的推理，并借子代理失败实现降级；只委派「想」，素材由主会话内联，结论回主会话复核。

**大 PR 代码质量审查不自研**：`/rd:review` 直接调原生 `/code-review`（多 agent 并行 + 逐条验证），档位按 PR 复杂度自动选。原 `file-reviewer` agent 已删：实测自研路径要主会话把 diff 抄进每个 prompt，「diff 不进主会话」不成立，还有误报。

**两条已知失败模式**（dogfooding 实测踩过）：① prompt 只给素材的磁盘路径而不内联正文 → subagent 把轮次耗在自己找文件上；② 一个 subagent 塞多个文件 → 撞 `maxTurns` 交出半成品。切分要细、素材要内联。

**allowed-tools**：只读命令不声明 Write/Edit/Bash。不声明 ≠ 禁用——调用时只是弹确认；命令 frontmatter 没有禁用工具的字段（`disallowed-tools` 仅 skill 支持），硬约束只能靠 Hook。**Token 节约**：单文件 < 30 KB；> 50 KB 拆主文件 + rationale；详见 [`docs/design/token-optimization.md`](./docs/design/token-optimization.md)。

## 自动触发技能（helper skill）

`skills/` 下**只有** helper skill——不与任何命令同名，由命令运行时按 `description` 自动激活，提供细化引导：

> `natural-language-dispatcher` 是 rd 的关键入口：用户用中文自然语言（非斜杠命令）表达意图时自动激活，识别意图→映射命令。`requirement-analyzer`/`prd-analyzer` 受 Memory 隔离约束：禁止 memory 影响文档结构/内容/格式。

---

## rd 插件核心机制

双轨需求（REQ/QUICK）、存储（无全局缓存、仓库角色）、Hooks 与两个 marker、分支与 issue 的细则见 `plugins/rd/CLAUDE.md`（处理 `plugins/rd/` 下文件时自动加载）。

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
7. 命令不写 `model`（auto 模式忽略 Haiku、#81318 让 sonnet 覆盖失效、换模型要重写缓存），一律跑会话模型；执行型 agent 同样 `model: inherit`、按特性钉 effort（下限 medium）；只有需要 Fable 的「想」派 `planner` / `root-cause`（失败降级当前模型）；helper skill 同样不写 `model`。委派规则集中在 `shared/_delegate.md`：切分要细（一个 subagent 一个源文件/一个单元）、素材正文内联进 prompt（给路径必超轮）、写操作满足准入四条才派、超轮用 SendMessage 续问而非重派。详见「命令与技能结构」。
8. diag 的 6 个风控 Hook 是设计核心，改 hooks 必须同步注册。
9. `/rd:release` 用 `version-bumper` 按 semver 推导各插件版本；发布事实源是 plugin.json + marketplace.json，README / tutorial 不写插件版本号，无需同步。
10. **改 `agents/` 或任何插件文件后，本仓库工作区的改动对运行时无效**——Claude Code 运行时加载的是 `~/.claude/plugins/cache/devflow/<plugin>/<version>/`，`/plugin` 更新则从 `~/.claude/plugins/marketplaces/devflow`（GitHub 克隆）拉。cache 按版本号分目录，**不 bump 版本号 `/plugin` 会报「already at the latest version」而不更新**。要让改动生效并可实测，必须走完：提交 → push → `/plugin` 更新 → `/reload-plugins`。在此之前跑 subagent 测的都是旧定义。
