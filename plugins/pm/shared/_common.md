# pm 公共约定

> pm 各命令共用的数据来源、采集口径与输出格式。命令里出现的 `collect_requirements()` / `collect_prd()` / `collect_modules()` / `collect_git_stats()` / `parse_date_range()` / `offer_save()` 指本文件同名小节，是**口径说明**，不是可调用的函数。

## 数据来源

pm 是 rd 数据的**只读消费者**：不修改任何需求文档；没有 rd 数据时只输出 Git 指标。

配置读 `.devflow/settings.json`，再用 `.devflow/settings.local.json` 覆盖同名字段（不回退 `.claude/settings*.json`，也不读 v2 的 `~/.claude-requirements/` 缓存）：

| 字段 | 用途 |
|------|------|
| `requirementProject` | 标题栏项目名 |
| `requirementRole` | `primary` / `readonly`，缺省按 `primary` |
| `requirementsDir` | 需求根目录，缺省 `docs/requirements` |
| `requirementSource.path`（local） | readonly 专用：primary 仓库根的本机绝对路径 |

需求根目录 `ROOT`（与 rd `_storage.md` 一致）：

- `primary`：本仓 `requirementsDir`
- `readonly`：`requirementSource.path` + **主仓**的 `requirementsDir`（读主仓 `.devflow/settings.json`，缺省同上）。未配置 `requirementSource` → 提示先 `/rd:use <primary-repo-path>` 绑定，本次降级为仅 Git 指标

`ROOT` 下：`active/`、`completed/`、`modules/`、`PRD.md`（无索引文件，需求列表按目录扫描）。

## collect_requirements()

扫描 `active/` 与 `completed/` 下的 REQ-XXX / QUICK-XXX 文档，每条取：编号、标题、类型、状态、模块、优先级、创建/更新日期、功能点进度（done/total）、测试进度（done/total）、关联分支、关联需求，以及是否位于 `completed/`。取自文档元信息表与勾选清单，缺失记空，不推测。

## collect_prd()

`PRD.md` 不存在则视为无 PRD。否则取「产品愿景」「功能规划」「技术选型」「需求追踪」四节内容，并统计已填写章节数 / 总章节数。

## collect_modules()

`modules/*.md` 每个文件取模块名、一句话描述、关联需求数。

## collect_git_stats(from_date, to_date, from_ref, to_ref)

时间范围与 ref 范围按命令参数给出（ref 只给起点时终点为 `HEAD`）。提交类统计一律 `--no-merges`。`--until` 要传 `<to_date> 23:59:59`，只传日期会漏掉截止日当天的提交。

| 指标 | 口径 |
|------|------|
| 提交数 / 按作者 / 按日期 | 非合并提交 |
| 按类型 | 标题前缀 `feat/fix/refactor/perf/docs/test/chore/style/ci/build` 及中文 `新功能/修复/重构/优化/文档/测试/构建`，其余归「其他」 |
| 增删行数、变更文件数 | 有 ref 范围用 `git diff --shortstat`；否则累加范围内各提交的 shortstat |
| 活跃分支 | 按最近提交时间倒序前 20 |
| 最近合并 | 范围内合并提交前 10 |
| Tag | 按创建时间倒序前 10，及最新 tag |

## parse_date_range(from, to, default_range)

- 同时给 `--from` / `--to` → 原样使用；只给 `--from` → 截至今天
- 都不给按 `default_range`：`week` = 本周一至今天；`month` = 本月 1 日至今天；`all` = 不限

## offer_save(content, path)

生成后询问是否保存到 `path`（回车保存 / `n` 跳过）；命令带 `--save` 时直接保存。目录不存在先创建。报告统一放 `docs/reports/`：

`weekly/<to_date>.md` · `monthly/<YYYY-MM>.md` · `milestone/<version>.md` · `stats/<date>.md` · `progress/<date>.md` · `risk/<date>.md` · `plans/<主题>.md` · `brief.md` · `custom/<标题>.md`

## 输出格式

- **禁止 emoji**（便于导出 Word/PDF）：重点用 `**加粗**`，风险级别用 **严重** / **警告** / **提示** 纯文字
- 标题栏：

  ```
  <命令标题>

  项目：<project> (<role>) | 日期：YYYY-MM-DD
  ```

- 结构化数据用 Markdown 表格；进度用百分比，不画进度条字符；数据量小时趋势用文字描述
- 结尾列 `**相关命令：**`，2~3 条 `/pm:xxx - 说明`
