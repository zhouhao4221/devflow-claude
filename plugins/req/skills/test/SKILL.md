---
name: test
description: 需求测试 - 综合测试验证（回归 + 新建 + 交互验证）
---

> **重要**：测试文件位置、运行命令、环境启动均从项目 `docs/prompt/testing.md` 读取，不内置任何项目细节。文件不存在时打印创建提示（非阻塞），回退到 `docs/prompt/architecture.md` 的「测试规范」章节。

# 需求测试

针对指定需求执行综合测试：运行已有测试 → 引导创建新测试 → 交互验证测试要点。

> 存储和缓存同步见 `_storage.md`（见附录：_storage.md）

## 命令格式

```
/req:test [REQ-XXX] [选项]
```

省略编号时自动选择「开发中/测试中」的需求，多个候选让用户选择。

| 选项 | 说明 |
|-----|------|
| `--failed` | 仅运行上次失败的测试 |
| `--skip-ut` / `--skip-api` / `--skip-e2e` | 跳过对应阶段 |
| `--force` | 某阶段失败时继续后续 |

---

## 总体流程

1. 选择需求 & 前置检查（状态必须为「开发中/测试中」，功能未完成时警告）
2. 提取测试要点（业务维度，分 API/业务规则/数据权限/其他）
3. 识别变更范围（优先需求文档「文件改动清单」，否则 `git diff`，按 testing.md 定位测试文件）
4. **阶段一：UT** — 回归运行变更相关已有 UT（委派 `test-runner`）→ 缺失时引导 `/req:test_new --type=ut`
5. **阶段二：API 测试** — 按 testing.md 启动环境 → 回归已有（委派 `test-runner`）→ 缺失时引导 `/req:test_new --type=api`
6. **阶段三：E2E 测试** — 额外检查前端服务 → 回归已有（委派 `test-runner`）→ 缺失时引导 `/req:test_new --type=e2e`
7. **交互验证** — 自动化未覆盖的测试要点逐项引导手动验证
8. 更新状态为「测试中」、记录结果、同步主仓需求目录
9. 汇总报告（各阶段通过/失败、测试要点覆盖率）

全部通过 → 提示 `/req:done`。存在失败 → 列出失败用例和原因，提示 `/req:dev` 修复或 `--failed` 重跑。

---

## 回归阶段的执行方式

阶段一~三的「回归运行已有测试」一律委派给 `test-runner` subagent 执行，主会话只接收摘要，测试日志不进入主会话；规则见 `_delegate.md`（见附录：_delegate.md）。

- 环境检查/启动（阶段二、三）仍由主会话完成，subagent 只跑测试命令
- prompt 自包含：工作目录、testing.md 中的运行命令（已拼好 `--failed`/模块过滤）、本阶段要跑的测试文件清单、`--failed` 模式下的上次失败清单
- 同一阶段内测试命令可按文件/模块拆分且数量 > 1 时，一次并行派多个
- subagent 回传 ERROR（依赖缺失、命令不存在、编译失败）时按原因处理或询问用户，不要改命令绕过
- 汇总报告的失败用例直接取自各 subagent 返回，不再重跑

---

## 测试模式

| 模式 | 命令 |
|------|------|
| 综合测试（默认） | `/req:test REQ-XXX` |
| 增量测试 | `/req:test REQ-XXX --failed` |
| 跳过阶段 | `--skip-ut` / `--skip-api` / `--skip-e2e` |
| 强制继续 | `--force` |

---

## 用户输入

$ARGUMENTS

---

# 附录（自动内联的共享约定）

> 以下内容由 command 引用的共享子文件自动内联，供不支持 slash 的 Claude 客户端离线阅读。请勿手动编辑本文件——改动应在对应 command 进行。

## 附录：_storage.md

# 公共逻辑参考 - 存储与配置

> 此文档定义 settings 文件写入、存储路径、缓存同步、需求编号、元信息等共用规则。
>
> 同伴文档（同目录，按需 Read；此处不用链接，避免生成器传递内联）：`_branch.md`（分支策略）、`_issue.md`（Issue 关联）、`_template.md`（模板与状态确认）、`_granularity.md`（需求粒度）、`_claude-md.md`（架构检查）。

## settings 文件写入规范

DevFlow 配置存储在项目根的 `.devflow/` 目录，按是否含密钥分两个文件：

| 字段 | 文件 | 纳入 git | 说明 |
|------|------|----------|------|
| `requirementProject` | `.devflow/settings.json` | ✅ | 团队共享配置 |
| `requirementRole` | `.devflow/settings.json` | ✅ | 团队共享配置 |
| `requirementsDir` | `.devflow/settings.json` | ✅ | 需求文档根目录，省略时默认 `docs/requirements` |
| `branchStrategy`（不含 token） | `.devflow/settings.json` | ✅ | 团队共享配置 |
| `giteaToken` | `.devflow/settings.local.json` | ❌ | 个人密钥，禁止提交 |

> **`.devflow/` 与 `.claude/` 的分工**：`.devflow/` 只放 DevFlow 业务配置（上表字段）；Claude Code 自身的 hooks、permissions 仍在 `.claude/settings.json`，两者互不迁移。项目级窄知识 skill 仍在 `.claude/skills/`。

**写入规则（强制）**：

1. **禁止独立配置文件**：DevFlow 字段一律合并进 `.devflow/settings.json` 或 `.devflow/settings.local.json`，禁止另建 `devflow.json`、`branchStrategy.json` 等
2. **合并写入**：先读取已有文件内容，合并需要更新的字段后写回，**不得覆盖已有字段**
3. **目录检查**：`.devflow/` 目录不存在时先创建
4. **读取合并顺序**：命令读配置时先读 `.devflow/settings.json`，再用 `.devflow/settings.local.json` 覆盖同名字段（`giteaToken` 以 local 为准）
5. **无写入权限的回退**：当 Write/Edit 工具被拒绝时，**不得**改写到其他文件，而应直接输出可复制执行的 shell 命令：

   ```bash
   # 写入 .devflow/settings.json（团队配置）
   python3 -c "import json,os; p='.devflow/settings.json'; os.makedirs('.devflow',exist_ok=True); d=json.load(open(p)) if os.path.exists(p) else {}; d['requirementProject']='my-project'; d['requirementRole']='primary'; json.dump(d,open(p,'w'),indent=2,ensure_ascii=False)"
   # 写入 .devflow/settings.local.json（本地密钥）
   python3 -c "import json,os; p='.devflow/settings.local.json'; os.makedirs('.devflow',exist_ok=True); d=json.load(open(p)) if os.path.exists(p) else {}; d['giteaToken']='YOUR_TOKEN'; json.dump(d,open(p,'w'),indent=2,ensure_ascii=False)"
   ```

```python
# 写入团队配置（.devflow/settings.json）
import json, os

path = ".devflow/settings.json"
os.makedirs(".devflow", exist_ok=True)
existing = json.load(open(path)) if os.path.exists(path) else {}
existing["requirementProject"] = "..."  # 只更新需要的字段
with open(path, "w") as f:
    json.dump(existing, f, indent=2, ensure_ascii=False)

# 写入本地密钥（.devflow/settings.local.json）
path = ".devflow/settings.local.json"
existing = json.load(open(path)) if os.path.exists(path) else {}
existing["giteaToken"] = "YOUR_TOKEN"
with open(path, "w") as f:
    json.dump(existing, f, indent=2, ensure_ascii=False)
```

### 读取惯例

命令读取 `requirementProject` / `requirementRole` / `requirementsDir` / `branchStrategy` 时，统一按以下顺序合并：

```
config = merge(.devflow/settings.json, .devflow/settings.local.json)
# .devflow/settings.local.json 中的同名字段覆盖 settings.json
```

**Legacy Claude 迁移（breaking change）**：v2.x 旧项目的 DevFlow 字段在 `.claude/settings.json(.local)`。**读取只认 `.devflow/`，不再回退 `.claude/`**——升级后未迁移的项目读不到配置。迁移方式（任选其一）：
- 运行 `scripts/migrate-config.sh`（搬运 DevFlow 字段到 `.devflow/`，密钥进 `settings.local.json`）
- 重新运行 `/req:init --reinit` 或 `/req:branch init`

> SessionStart hook 检测到 `.claude/` 存在 DevFlow 字段但 `.devflow/` 缺失时，会打印迁移提示。

---

## 存储路径解析

```
需求存储（唯一源，在 primary 仓库）: <requirementsDir>/   默认 docs/requirements/
modules/      # 模块文档
specs/        # 规范文档（数据类型、接口契约等，跨仓库共享）
active/       # 进行中需求
completed/    # 已完成需求
INDEX.md      # 索引
```

**无全局缓存**：需求文档只存在于 primary 仓库的 `requirementsDir`，是唯一事实源。readonly 仓库不复制、不缓存，直接读 primary 仓库目录。

**解析规则**：
1. 读 `.devflow/settings.json` 的 `requirementRole` / `requirementsDir` / `requirementSource`，再用 `.devflow/settings.local.json` 覆盖同名字段
2. `primary`：需求根目录 = 本仓 `requirementsDir`（省略时默认 `docs/requirements/`；下文 `docs/requirements/` 均指此解析结果）
3. `readonly`：需求根目录 = `requirementSource.path` 指向的主仓根 + 该主仓的 `requirementsDir`；未配置 `requirementSource` 时报错，提示先 `/req:use <primary-repo-path>` 绑定

**仓库角色**（`requirementRole` 字段）：

| 角色 | 值 | 说明 |
|------|------|------|
| 主仓库 | `primary` | 拥有本地 `requirementsDir`，可读写，写入即生效 |
| 只读仓库 | `readonly` | 无本地需求目录，经 `requirementSource.path` 直接读主仓，不可创建/编辑/变更状态 |

**读取策略**：
- `primary`：读写本仓 `requirementsDir`
- `readonly`：直接读 `requirementSource.path` 下的需求目录（实时，无副本）

## 写入规则（无缓存，主仓唯一源）

**核心原则**：需求文档**只有一份**，位于 primary 仓库的 `requirementsDir`。不存在缓存层，因此没有同步动作。

- **primary**：所有修改需求的命令（new、new-quick、edit、review、dev、test、done、upgrade、modules/specs/prd 编辑）直接写本仓 `requirementsDir`，写完即生效，**无任何后续同步或 cp**。
- **readonly**：禁止一切写操作（创建、编辑、状态更新）。仅读取 `requirementSource.path`。

> **历史说明（v2.x → v3 breaking change）**：v2.x 曾用 `~/.claude-requirements/` 全局缓存 + PostToolUse `sync-cache.sh` 单向同步，readonly 从缓存读。v3 起**移除缓存**：readonly 改为经 `requirementSource.path` 直读主仓，`sync-cache.sh` 不再注册。命令内**不应再有任何缓存读写、cp 到缓存、或全局索引（`~/.claude-requirements/index.json`）操作**。

## 需求编号生成

扫描 active/ 和 completed/ 目录，找最大编号 +1，格式 `REQ-XXX`

## 元信息字段

| 字段 | 说明 |
|------|------|
| 编号 | REQ-XXX |
| 类型 | 后端/前端/全栈 |
| 状态 | 当前状态 |
| 模块 | 所属模块 |
| 关联需求 | 前后端对应需求 |
| branch | 开发分支名（/req:dev 首次进入时生成） |
| issue | 关联的 Git 平台 issue 编号（如 `#123`），无关联为 `-`。`/req:new --from-issue` 自动填充，`/req:done` 读取后可选关闭 |

## 附录：_delegate.md

# 子任务委派（subagent）规范

> 目的：把「吞吐大、推理浅」的步骤交给独立 subagent 执行，主会话只接收结论。收益有两层：便宜模型单价低；更重要的是**上下文隔离**——测试日志、文件全文、大段 diff 留在 subagent 内，不进入主会话，后续每一轮都不再为它们付费。

## 何时委派

满足任一即委派；否则直接在主会话做（委派本身有开销：写任务说明 + 结果回传）：

| 条件 | 典型步骤 |
|------|---------|
| 步骤会往主会话灌入大量原始输出（估计 > 1 万 token） | 跑测试、拉大 diff、批量 grep |
| 步骤可按单元切分且各单元相互独立 | 逐文件审查、多模块搜索 |
| 步骤不依赖主会话已积累的上下文 | 一条命令 + 判定规则即可完成 |

**不委派**：需要主会话已有上下文才能判断的推理（方案设计、跨文件改动、与用户交互的闸门）。

## 可用 agent（随插件分发，位于 `plugins/req/agents/`）

| agent | 模型 | 用途 | 返回 |
|-------|------|------|------|
| `test-runner` | haiku | 执行给定测试命令 | 计数 + 失败用例（file:line、断言、精简堆栈） |
| `file-reviewer` | sonnet | 审查单个文件的 diff | 阻塞/建议/信息分级清单 + 跨文件疑点 |
| `code-scout` | haiku | 按关键词定位相关代码（实现处/调用链/同类参照） | 文件清单（路径、相关度、关键行、原因），不含文件内容 |

命令的 frontmatter `allowed-tools` **必须包含 `Agent`**（`allowed-tools` 是白名单限制，缺失则无法派生）。

## 委派时必须做到

1. **任务说明自包含**：subagent 没有主会话历史。工作目录、命令、判定规则、项目规范中相关的几条（不是整份文件）都要写进 prompt。
2. **只要结论，不要原文**：agent 定义已规定返回格式；prompt 中再明确「不要回传完整日志/文件内容」。
3. **独立单元并行**：同一批 subagent 在一次调用里一起发出，结果由主会话汇总、去重、合并跨单元问题。
4. **subagent 只读**：agent 定义不含 Write/Edit；需要改代码的结论由主会话执行。
5. **失败要透传**：subagent 报 ERROR/超时时把原因带回，主会话决定重试或降级为内联执行，不静默吞掉。

## 与仓库角色 / 调用形态的关系

- 与 `requirementRole` 无关：委派不涉及需求文档写入。
- skill 形态同样适用：Agent 工具随会话可用；agent 定义随 req 插件安装。
