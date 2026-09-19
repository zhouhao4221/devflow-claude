---
description: 代码审查 - AI 审查 PR 并提交评论，或按人工审查评论修改代码
argument-hint: "[comments] [PR-ID|REQ-XXX] [--level=low|medium|high] [--auto]"
allowed-tools: Read, Write, Edit, Glob, Grep, Bash(git:*, gh:*, tea:*, curl:*), Agent, Skill
---

# 代码审查

审查 PR 的代码：无子命令时 AI 审查并提交评论；`comments` 子命令拉取人工审查评论、生成修改方案并按确认修改代码。需求评审不在这里：提审 / 通过 / 驳回用 `/rd:req-review`。

> **Audience:** Engineer
> 不受仓库角色限制，readonly 也可执行。
>
> CLI 优先级：GitHub → `gh pr`/`gh api`；Gitea → 按 [`_gitea_cli.md`](../shared/_gitea_cli.md) 检测 `tea`。tea 未覆盖的接口走 curl。

## 命令格式

```
/rd:review [PR-ID|REQ-XXX] [--level=low|medium|high] [--auto]   # AI 审查（默认）
/rd:review comments [PR-ID|REQ-XXX]                             # 按人工评论改代码
```

## 参数守卫

参数含 `pass` / `reject`（如 `/rd:review REQ-001 pass`）→ 这是需求评审的旧写法，**不执行**任何流程，只输出：

```
需求评审已改为 /rd:req-review：/rd:req-review REQ-001 pass
```

---

## 通用前置（定位 PR）

- 依赖已创建的 PR；未找到关联 PR 时提示先执行 `/rd:pr` 创建；本文与 `pr-ops.md` 的「通用前置」保持一致
- 确定目标 PR：参数给 `PR-ID` 直接使用；给 `REQ-XXX` 取需求文档 `branch` 字段；都省略时从当前分支匹配
- **GitHub 的 gh 可用** = 已安装且 `gh auth status` 通过（只装未登录也算不可用）。不可用时：只读查询（取 PR 元数据、拉评论）回退公开 REST API，私有仓库无凭据时提示 `gh auth login` 后退出；写操作（提交审查评论、Approve、合并）不执行，改为输出 PR 链接与手动操作指引，审查报告仅本地展示

---

## AI 代码审查（无子命令）

### 1. 取 diff 并判定规模

PR 元数据按平台取（GitHub `gh pr view`，Gitea `/pulls/{N}`），diff 一律走本地 git：fetch PR 分支与 `mergeTarget` 两端后 `git diff --numstat <mergeTarget>...<branch>` 得到逐文件行数。

**文件分类**（只看路径/后缀，不读内容；同时供路由、4.1 打分使用）：

| 类别 | 判定依据 |
|------|---------|
| 非代码 | 文档（`*.md`、`docs/`）、配置（`*.json`/`*.yaml`/`*.yml`/`*.toml`/`*.ini`/`.env*`）、lock（`*.lock`、`package-lock.json`、`pnpm-lock.yaml`、`go.sum`）、生成文件（`*.pb.go`、`*_gen.*`、`*.generated.*`、`dist/`、`build/`） |
| 展示层 | 样式（`*.css`/`*.scss`/`*.less`/`*.styl`、`styles/`）、静态资源（`assets/`、`static/`、`public/`、图片、字体）、文案（`i18n/`、`locales/`、`*.po`）、纯模板 `*.html` |
| 逻辑代码 | 其余全部。`.vue`/`.tsx`/`.jsx` 含逻辑，归此类不拆；测试文件按路径识别（`test`/`spec`/`__tests__`/`_test.go`），属于逻辑代码的子集 |

**路由**：

| PR 规模 | 判定 | diff 进主会话的方式 |
|---------|------|-------------------|
| 小 PR | ≤ 10 个文件且 ≤ 800 行 | 读全量 diff |
| 小 PR（非逻辑为主） | 非代码 + 展示层改动行 ≥ 80%，且逻辑代码部分 ≤ 10 个文件且 ≤ 800 行 | 只读逻辑代码文件的 diff；非逻辑文件看 numstat 清单，抽读改动行数最多的 3 个 |
| 大 PR | 其余 | 派 `diff-digest` 取摘要（无需落盘），diff 原文不进主会话 |

> 第二行是为批量改名、lock 更新、纯样式/文案 PR 设的：这类改动送去原生 `/code-review` 跑六分钟不值，但把几千行 CSS 全读进主会话同样不值，所以只读有逻辑的那部分。

### 2. 读取审查依据

按优先级：项目 CLAUDE.md 开发规范 → 测试规范 → 需求文档功能清单和业务规则。

另 Read `docs/prompt/pr-review.md`，存在则将其审查维度（必备输入、优质输出标准、常见失败模式）并入第 4 步审查关注点；缺失静默跳过。

### 3. 对比需求文档与实际实现

检查维度：

| 检查项 | 判断依据 |
|--------|---------|
| 状态字段 | 文档状态是否为「开发中/测试中」 |
| 功能清单 (第二章) | diff 是否覆盖清单每一项 |
| 接口需求 (第五章) | diff 中路由/DTO 是否在文档中记录 |
| 数据模型 (11.1) | 表/字段变更是否在文档中描述 |
| 文件改动清单 (11.3) | diff 实际文件 vs 清单列出文件 |
| 实现步骤 (11.4) | 清单步骤是否在 diff 中能找到 |
| 业务规则 (第三章) | 关键规则是否在代码中体现（如校验逻辑） |
| 关联需求 | 文档「关联」字段引用 |

> primary 读 `docs/requirements/active/`，readonly 读 `<requirementSource.path>/<requirementsDir>/active/`。未找到需求文档时跳过此步。
>
> 大 PR 用第 1 步 `diff-digest` 返回的文件清单与结构性改动（路由、DTO、表/字段）做比对，不拉 diff 原文。

### 4. 代码质量审查

| PR 规模 | 方式 |
|---------|------|
| 小 PR | 交给 `planner`（Fable）审查：正确性、安全性、错误处理、需求匹配、测试覆盖（见下） |
| 大 PR | 调用原生 `/code-review`（Skill 工具），主会话不看 diff 原文，只接收已验证的问题清单 |

> 大 PR 不再自研逐文件委派：原生审查多 agent 并行 + 逐条验证去重，实测无误报且跨文件问题自己追完；而自研路径要主会话把 diff 再抄进每个 prompt，「diff 不进主会话」并不成立。一次 medium 约 6 分钟（2026-09 实测）。

**小 PR 审查交给 `planner`**：prompt 内联任务类型 `review 小 PR`、第 1 步读入的 diff、第 2 步审查依据摘要（含 pr-review.md 维度）、问题清单骨架（阻塞 / 建议 / 信息，每条带 file:line）；主会话复核后并入第 5 步报告。**planner 失败**（Agent 返回 API 错误，如 Fable 额度用尽、未开通、云厂商未上架；或超轮仍无结论）→ 不重试，主会话用当前模型按同一骨架自己基于 diff 内联审查，首行注明 `⚠️ Fable 不可用，本审查由当前模型生成`。

**4.1 档位**：`--level=` 显式指定优先；否则按下表打分自动选，并在输出里打印 `档位：<level>（命中：<信号列表>）` 与 `文件分类：逻辑 n / 展示 n / 非代码 n`，便于事后调阈值。信号全部来自第 1 步的 `git diff --numstat`、文件分类与 `diff-digest` 返回的结构性改动清单，不额外读文件内容。

| 分值 | 信号 | 判定依据 |
|------|------|---------|
| +1 | 规模大 | 超过 30 个文件或 2000 行 |
| +1 | 契约变更 | 结构性改动含接口签名、DTO/表字段、错误码、配置项或依赖变化 |
| +1 | 敏感路径 | 路径含 `migration`/`schema`/`.sql`、`auth`/`permission`/`acl`/`rbac`、`pay`/`billing`、`delete`/`purge`/`drop` |
| +1 | 缺测试 | 逻辑代码文件有改动，但测试文件改动行数不足其改动的 10%；展示层与非代码文件不计入分母（否则纯样式 PR 会白拿这 1 分） |
| +1 | 跨模块 | 改动落在 ≥ 3 个顶层模块目录 |
| −1 | 轻量 | QUICK 需求或 hotfix 分支 |
| −1 | 非逻辑为主 | 非代码 + 展示层改动行合计 ≥ 80%（按第 1 步文件分类；两类合并计算，混合 PR 才能命中） |

总分 ≤ −1 → `low`；0 或 1 → `medium`；≥ 2 → `high`。不自动选 `max`；`ultra` 不能由命令触发且单独计费，只在报告末尾提示「可手动 `/code-review ultra <PR#>`」。

**4.2 目标**：GitHub 传 PR 号；Gitea 与 `other` 传 ref 范围 `<mergeTarget>...<branch>`（第 1 步已 fetch 两端，ref 范围只依赖本地 git）。调用形式 `/code-review <level> <target>`。**不加 `--comment`**：GitHub 上会出现两套评论来源，Gitea 不支持；评论统一走第 6 步。

**4.3 结果映射**：Important → 阻塞；Nit → 建议；Pre-existing → 信息，并标注「非本 PR 引入」。原生结果已验证与去重，主会话不逐条复审，只核对与第 3 步「需求文档同步」是否重复。

**4.4 不可用时**：`/code-review` 不在可用技能列表（旧版本或被 `skillOverrides` 锁为仅用户可调用）→ 退回小 PR 的审查方式（`planner`，失败再内联），并在报告首行注明「原生审查不可用，已按小 PR 方式审查」。

### 5. 输出审查报告

问题分三级：**阻塞**（阻止合并）、**建议**（不阻止）、**信息**（知识分享）。

报告分两部分：代码审查 + 需求文档同步（文档与代码偏差，不阻止合并但建议 `/rd:edit` 补齐）。

### 6. 提交审查评论

**零问题直通**：阻塞=0、建议=0、文档同步项=0 时，自动用固定模板提交通过评论，跳过确认。

**有任意问题时**：展示精简版预览 → 询问用户是否提交（`--auto` 跳过确认）。

> 精简规则：保留阻塞（全部）、关键建议、文档同步关键缺失；去除信息级备注、风格命名建议、过程信息。控制在 300 字以内。
>
> Gitea：PR 评论用 `/issues/{N}/comments`（不是 `/pulls/`）。`repoType = "other"` 仅本地展示。

### 7. 无阻塞时的后续操作

阻塞=0 且 PR 为 Open 时：
- **有审核人**（PR reviewers 或 `branchStrategy.reviewers`）→ 提示是否提交 Approved（Gitea `POST /pulls/{N}/reviews` body `{"event":"APPROVED"}`，GitHub `gh pr review --approve`）
- **无审核人** → 仅展示结果，提示可 `/rd:pr merge`

人工审查评论回来后，用 `/rd:review comments` 按评论改代码。

---

## comments — 按人工审查评论修改代码

### 1. 拉取、过滤、展示

按 [`pr-ops.md`](../shared/pr-ops.md) 的「comments」节执行：拉取整体评论与行内评论，过滤本人 / AI 自提交 / 已 resolved，分组展示清单。无可处理评论 → 提示并退出。

### 2. 分析与修改

逐条读取评论引用的源码位置（行内评论按 `path` + `line` 取 ±20 行；整体评论按内容定位相关文件，不确定时派 `code-scout`），判断**可执行**（评论要求明确、改动范围清楚）或**需讨论**（意图不明、与需求文档冲突、涉及方案取舍），生成修改方案：

```
[1/4] src/api/user.ts:42（@reviewer）
  评论：这里应该先校验 token 再取用户
  方案：把 validateToken 调用提到 getUser 之前，补一个过期分支
  判定：可执行

[2/4] 整体评论（@reviewer）
  评论：分页参数是不是该走统一的 PageQuery？
  判定：需讨论 —— 与需求文档「五、接口需求」的分页约定冲突，建议先回复确认
```

用户确认后按方案修改「可执行」项；「需讨论」项只列出，不改代码，可用 `/rd:issue comment` 或 PR 评论回复。修改完成后提示 `/rd:commit`。

> `--auto` 不作用于本子命令：「是否应用修改」的确认保留，避免 AI 误改代码。

---

## 用户输入

$ARGUMENTS
