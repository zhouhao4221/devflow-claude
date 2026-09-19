# Token 使用与节约指南

> 面向 DevFlow 插件维护者。每次 `/rd:*`、`/api:*`、`/pm:*` 调用的延迟、成本、cache 命中率都受 token 数量影响——本指南给出一套可量化、可执行的节约规则。

---

## 1. 为什么关心 token

| 维度 | 关系 |
|------|------|
| **延迟** | prompt 越大，模型 prefill 越慢；用户从敲完命令到看到第一个字的时间被 prompt 大小直接拉长 |
| **成本** | 按 token 计费（input + output），prompt 占比通常是 80%+ |
| **Cache 命中率** | Anthropic prompt cache TTL 5 分钟。prompt 越大，跨会话 cache miss 时重建越贵 |
| **上下文窗口** | 1M context 看似很大，但塞满后会触发自动压缩，损失对话历史精度 |

**经验阈值（单命令文件）**：
- < 15 KB → 健康
- 15~30 KB → 可接受，留意继续增长
- 30~50 KB → 应该考虑拆分
- \> 50 KB → 必须拆分（参考 `release.md` 案例，§5）

---

## 2. Token 怎么算

### 2.1 速算法（无需调 tokenizer）

| 内容类型 | 估算公式 | 示例 |
|---------|---------|------|
| 纯英文 | `字符数 / 4` | 1 KB ≈ 250 tokens |
| 纯中文 | `字符数 × 1.5` | 1 KB（含 ~330 个汉字）≈ 500 tokens |
| 中英混合 markdown | `字节数 / 3` | 1 KB ≈ 330 tokens |
| 代码（含 markdown 围栏） | `字节数 / 3.5` | 1 KB ≈ 280 tokens |

**快速命令**：

```bash
# 看插件所有命令的字节数 → 粗估 token
wc -c plugins/rd/commands/*.md | sort -n

# 单文件估算 token（中英混合 markdown 经验值）
python3 -c "import os; b=os.path.getsize('plugins/rd/commands/release.md'); print(f'{b} bytes ≈ {b//3} tokens')"
```

### 2.2 精确测量

需要精确数字时用 Anthropic 官方 tokenizer：

```bash
# Python：pip install anthropic
python3 -c "
from anthropic import Anthropic
c = Anthropic()
n = c.count_tokens(open('plugins/rd/commands/release.md').read())
print(f'{n} tokens')
"
```

或用 `claude` CLI 的 `/cost` 命令查看本会话已消耗 token。

### 2.3 估算的局限

速算公式有 ±20% 误差。对中英混合文档：
- 大量代码块、表格 → 偏低估
- 大量自然语言段落 → 偏高估
- emoji、特殊符号 → 每个常吃 1~3 tokens

---

## 3. 哪些东西会算成 token

### 3.1 自动加载（每次调用都付费）

| 来源 | 触发时机 | 节约手段 |
|------|---------|---------|
| **slash 命令文件本身** | 用户键入 `/rd:xxx` | §4.1 拆主+rationale |
| **frontmatter 里的 `description`、`argument-hint`** | 命令注册时 | 保持简短 |
| **CLAUDE.md（项目 + 用户）** | 每次会话/调用 | 不在本插件可控范围；项目 CLAUDE.md 已 ~10KB，注意不要无限膨胀 |
| **MEMORY.md 索引** | 每次会话 | 索引行 ≤ 150 字符；详细内容放独立 memory 文件按需读 |
| **SessionStart hook 输出** | 会话启动 | `session-context.sh` 输出尽量短，目前 ~30 行 OK |

### 3.2 按需加载（只在用到时付费）

| 来源 | 触发时机 | 节约手段 |
|------|---------|---------|
| **Read 工具拉的文件** | 模型决定 Read | §4.2 把大共享文件拆主题；用 `offset/limit` 只拉需要段落 |
| **Glob/Grep 结果** | 模型搜索 | 收紧 `path` 和 `glob` 参数，避免 1000 行结果 |
| **Bash 命令输出** | 命令执行 | 长输出加 `head`/管道过滤 |
| **Hook PostToolUse 输出** | 工具调用后 | hook 脚本只输出关键状态，不打印整个文件 |
| **子 Agent 返回结果** | Agent 调用结束 | 在 prompt 里写"报告 ≤ 200 words"约束 |

### 3.3 不算（但常被误以为算）

- `_*.md` 共享文件**不会**因为被 markdown 链接引用就被自动加载——只有模型显式 Read 才付费
- `commands/` 目录下的其他命令文件不会被一起加载
- `templates/` 文件不在 prompt 里，需要 Read 才进入上下文

---

## 4. 节约策略（按收益排序）

### 4.1 拆主+rationale（最大收益）

**何时用**：单命令文件 > 30 KB，且其中有大段"为什么这样设计"的散文。

**做法**：
1. 主文件 `<command>.md` 只留：frontmatter、参数说明、step 骨架、决策代码、强制交互闸门、输出模板
2. 配套文件 `<command>-rationale.md` 收：设计原理、行为矩阵详解、完整边界情况大表
3. 主文件用 `详见 rationale §X` 引用，不重复内容

**案例**：`plugins/rd/commands/release.md` 从 63 KB 拆到 15 KB 主文件 + 14 KB `release-rationale.md`（按需读）。常见路径每次省 ~12K tokens。

### 4.2 共享文件按主题拆

**何时用**：`_common.md` 类共享文档 > 15 KB，被多个命令引用。

**做法**：按读取主题切成多个小文件：

```
_storage.md        # settings + 存储路径 + 写入规则（无缓存）
_branch.md         # 分支策略配置
_issue.md          # Issue 拉取 + 分支/commit 关联
_template.md       # 模板约束 + 状态确认
_granularity.md    # 需求粒度 + REQ vs QUICK
_claude-md.md      # CLAUDE.md 架构检查
```

更新各命令的引用从 `[_common.md]` 改成具体的 `[_issue.md]` 等。模型 Read 时只拉相关主题（~3-6KB），不再每次拉 22KB。

**共享文件之间禁止用 Markdown 链接互引**：任何一个 `_*.md` 链到其它几个，模型顺着链接展开就会把整组 ~33KB 全部读进上下文，按主题拆分的收益直接归零（2026-08 前由此派生的 skill 镜像也都因此超 30KB）。互相提及时写纯文本文件名（`` `_branch.md` ``），只有真实依赖（如 `_issue.md` → `_gitea_cli.md` 的 tea 检测）才用链接。

### 4.3 显式降级到 Haiku

**何时用**：纯读取、列表展示、机械操作、帮助信息类命令。

**做法**：在 frontmatter 加 `model: claude-haiku-4-5-20251001`。Haiku 4.5 比 Sonnet 5 便宜 2 倍（$1/$5 vs $2/$10 每百万 token，2026-09 核实），主要收益是快，价差已不大。

**已应用**：以 `grep -l "^model:" plugins/*/commands/*.md` 为准，不在此维护清单。

**禁忌**：需要复杂推理、代码生成、深度分析的命令（如 `/rd:dev`、`/rd:do`）不要降级。

**中间档 Sonnet**：数据聚合 + 成文类命令（`/pm:weekly`、`monthly`、`milestone`、`stats`、`progress`、`brief`、`risk`）用 `model: claude-sonnet-5`——比会话模型便宜 2.5～5 倍（Opus 5 $5/$25、Fable 5.1 $10/$50），写报告绰绰有余。Sonnet 5 原生 1M 上下文且超 200K 不加价、订阅制不计 extra usage（2026-08 核实），旧的「sonnet[1m] 付费墙」顾虑已不存在。`/pm:plan`、`/pm:ask` 需要真实推理，保持省略。

**省略档要收窄**（2026-09）：会话模型升到 Fable 5.1 后，省略档相对 sonnet 的价差从 2.5 倍拉到 5 倍。Anthropic 的建议是先试 Fable 低 effort 再换便宜模型，当时误以为命令 frontmatter 没有 `effort` 字段（2026-09-19 查文档：命令与 skill 同源，也支持 `effort`，本仓库尚未启用）；且这类命令输入密集（读文档、读代码），输入按单价计费，effort 也降不下来。因此**有界的单文档编辑/分析**（`/rd:edit`、`prd-edit`、`split`、`new-quick`）与**模板化的测试/代码生成**（`/rd:test`、`test_new`、`/api:gen`、`map`）显式 `claude-sonnet-5`，CLI 包装类（`/rd:issue`，与 `branch`/`commit` 同类）显式 haiku。省略档只留真正需要会话模型做判断的：`/rd:dev`、`do`、`fix`、`new`、`pr`、`init`（一次性、要归纳架构）、`/pm:plan`、`ask`、`/diag:diagnose`。

**会话模型不再假定是 Fable，「想」交给 Fable 子代理**（2026-09-19，v5.1.0）：命令默认跑当前会话模型；`/rd:dev`、`do`（实现方案）、`/rd:fix`（根因 + 修复）、`/rd:review`（小 PR 审查）派 `planner`，`/diag:diagnose`（根因）派 `root-cause`，两者 `model: fable`。子代理失败（Fable 额度用尽 / 不可用）时错误回到主会话，主会话用当前模型接手。中间走过两步弯路（v5.0.1–v5.0.2 给命令钉 `model: best`），教训如下（官方文档 2026-09-19 核实）：

1. **命令级覆盖只到当轮**：命令的 `model`「applies for the rest of the current turn … The session model resumes when you send your next prompt」。靠它区分「想」和「写」时，闸门必须落在轮与轮之间：Plan Mode 的 ExitPlanMode、AskUserQuestion 都在同轮内返回，确认后写代码仍跑钉的模型；出方案之前先停下等回复，方案又落到会话模型（v5.0.1 的 dev 两头都中，v5.0.2 硬改闸门位置，代价是多处「请用户重跑」）。子代理方案与闸门位置无关，v5.1.0 已撤回这些限制。
2. **命令级覆盖不会降级**：`best` 只在 Fable「不可用」（allowlist 排除、云厂商未上架）时退 Opus；额度用尽不算不可用，钉了 `best` 的 `/rd:fix` 直接报「You're out of usage credits. Run /usage-credits to keep using Fable 5.1 or /model to switch models」，命令锁死。`fallbackModel` 链也明确不处理计费 / 限流错误（「Authentication, billing, rate-limit … never trigger a switch」）。
3. **子代理失败可接手**：同样额度用尽时，`model: fable` 的子代理返回 `Agent terminated early due to an API error: You're out of usage credits…`（HTTP 429），主会话照常继续，可按同一骨架自己做。部分套餐 / 席位下 Fable 按 usage credits 计费、不占套餐额度，交互会话首次弹同意提示（`-p` / Agent SDK 不弹，直接计费）。

**代价**：子代理只拿到主会话内联的素材，不继承会话历史，所以不存在「整段历史按 Fable 单价重算」的问题；代价是素材要内联充分（规则见 `_delegate.md`「思考委派」），方案回来还要主会话复核一遍。

### 4.4 收紧 `allowed-tools` 预授权

**何时用**：所有命令。

**做法**：frontmatter 只声明真正需要的工具，只读命令不声明 Write/Edit。注意 `allowed-tools` 只是**免确认预授权**，不限制可用工具——未声明的工具照样能调用，只是会弹确认，不能当安全边界用；命令 frontmatter 也没有禁用工具的字段，硬约束只能靠 Hook。

**收益**：越界调用（只读命令去写文件、跑无关 Bash）不会被静默放行，用户在确认框里能拦下；Bash 限定子集（`Bash(git:*, gh:*)`）让常规命令免确认、其余命令弹确认。

### 4.5 把确定性逻辑下沉到 shell 脚本

**何时用**：命令里有大段"伪代码描述算法"（如版本号推导、SQL 解析、JSON 构造），且逻辑确定。

**做法**：写到 `scripts/<topic>.sh`（或 `.py`），命令文件改成"调用 + 展示结果"。

**收益**：脚本不进 prompt，模型只看几行调用代码；执行也比"模型按伪代码 Bash 跑"快得多。

**示例方向**（暂未实施）：`/rd:release` 的 `compute_bump`、SQL 合并/回滚生成、Gitea Release API 调用都符合这个模式。

### 4.6 Read 用 `offset/limit` 精读

**何时用**：知道目标文件具体行号或只需开头/末尾。

**做法**：

```python
Read(file_path="docs/requirements/active/REQ-001.md", offset=120, limit=50)
```

**收益**：1000 行的需求文档只读 50 行，省下 ~95% Read 体积。

### 4.7 Hook 输出严格控制

**做法**：
- `validate-requirement.sh` 只输出 `✅` / `❌ <一句话>`，不要 dump 整个文件
- `confirm-before-commit.sh` 默认静默放行，仅拦截时输出决策
- `session-context.sh` 控制在 30 行以内

---

### 4.8 高吞吐步骤委派给 subagent

**何时用**：命令中某一步会往主会话灌入大量原始输出（跑测试、大 PR diff、批量 grep），或可按独立单元拆分并行（逐单元实施）。

**做法**：命令文档指示把该步骤派给插件自带的 agent（`plugins/rd/agents/`），主会话只接收结构化结论；frontmatter `allowed-tools` 加 `Agent`。规则与可用 agent 见 `plugins/rd/shared/_delegate.md`。

**收益**：两层。① 机械步骤跑在 haiku 上（`test-runner`）；② **上下文隔离**——原始输出留在 subagent，主会话之后每一轮都不再为它付费，这一层通常比单价差更大。

**禁忌**：小任务不委派（任务说明 + 回传本身有开销，经验阈值 > 1 万 token 才划算）；不要把需要主会话上下文的推理（方案设计、跨文件改动）拆出去——planner/executor 割裂后返工更贵。整条命令的 `model` 仍按 §4.3 分 haiku / sonnet / 省略三档，委派不是降档的理由。

**已应用**：`/rd:test` 阶段一~三回归运行（`test-runner`，haiku）· `/rd:dev` §4 / `/rd:fix` §1.2 / `/rd:do` §2 代码定位（`code-scout`，haiku，主会话只精读返回的 file:line）· `/rd:review` 大 PR 需求比对用 `diff-digest` 摘要；代码质量审查改调原生 `/code-review`（自研 `file-reviewer` 已删，实测自研需主会话把 diff 抄进每个 prompt，隔离不成立）。

---

## 5. 案例：`release.md` 拆分前后

| 维度 | 拆分前 | 拆分后 |
|------|--------|--------|
| `release.md` | 63 KB / 1327 行 / ~21K tokens | 43.8 KB / 1130 行 / ~14K tokens |
| `release-rationale.md` | — | 13.7 KB（按需 Read） |
| 常见路径每次加载 | 21K tokens | 14K tokens（**省 33%**） |
| 出错追问"为什么"时再加载 | 已在 prompt 中 | +4.5K tokens（按需） |

**结论**：拆分让常见路径变快，罕见追问稍微变慢——但罕见追问本来就允许稍长。

---

## 6. 维护 checklist

新增或修改命令时，按下面顺序自检：

- [ ] 命令文件大小 < 30 KB？超过先想是否能拆 rationale
- [ ] frontmatter `description` ≤ 50 字符？
- [ ] frontmatter `allowed-tools` 是否最小集？
- [ ] 是否纯读取/列表？是 → 加 `model: claude-haiku-4-5-20251001`；是数据聚合成文？→ `model: claude-sonnet-5`；需要深度推理的一步（方案设计/根因分析/小 PR 审查）？→ 不抬命令档，派 `planner`（Fable，失败降级当前模型）
- [ ] 有没有会灌入大量原始输出的步骤（跑测试、大 diff）？有 → 委派 subagent（§4.8），`allowed-tools` 加 `Agent`
- [ ] 引用 `_common.md` 的具体章节？引用越具体越省（模型可能只 Read 一次而非反复）
- [ ] 长伪代码（> 50 行）能否下沉到脚本？
- [ ] 输出模板是否过度展开？只列结构和关键字段，不写所有可能的分支
- [ ] 边界情况是否塞进主文件？> 10 行的就剥到 rationale

定期检查（建议每月）：

```bash
# 命令文件按大小排序，前 3 名是优化候选
wc -c plugins/*/commands/*.md | sort -nr | head -10

# 共享文件按大小排序
wc -c plugins/*/shared/*.md | sort -nr
```

---

## 7. 不要做的优化

- ❌ **不要为省 token 删掉强制交互闸门描述** —— 这些是命令正确性的合约，不能为了变快而模糊
- ❌ **不要把 frontmatter 的 `model` 设成不存在的模型** —— 用户账号可能没开 Opus，用 `claude-haiku-4-5-20251001` 这种确定的 ID
- ❌ **不要把 rationale 删光** —— 设计依据迁出主文件后**必须**有归宿（rationale 文档），否则下次维护无人能改
- ❌ **不要在 hook 里调用 LLM** —— hook 输出每次都进 prompt，即使是简单分类也会让会话启动变慢
- ❌ **不要让命令"为了精简"省略输出模板** —— 模型看不到模板就不知道该输出什么样的格式，反而要更多 token 自己想

---

## 8. 参考

- Anthropic prompt caching: https://docs.anthropic.com/en/docs/build-with-claude/prompt-caching
- Claude tokenizer 行为差异：中文每字 1.5~2 tokens 是因为 BPE 把 UTF-8 多字节字符切多个 token
- 项目 CLAUDE.md「命令与技能结构」章节定义模型分级四档；已应用清单以 `grep -l "^model:" plugins/*/commands/*.md` 为准
