# QUICK-005 迁移补项目级插件开关检查 + GitHub PR 成功提示

## 元信息

| 字段 | 值 |
|-----|-----|
| 编号 | QUICK-005 |
| 改动类型 | bug修复 |
| 端类型 | 全栈 |
| 状态 | 已完成 |
| 模块 | 快速修复 |
| 优先级 | P2 |
| 创建时间 | 2026-09-15 |
| 负责人 | |
| 关联需求 | REQ-004、REQ-005 |
| branch | fix/QUICK-005-migrate-enabled-plugins |
| issue | - |

## 生命周期

- [x] 草稿
- [x] 方案确认
- [x] 开发中
- [x] 已完成

---

## 问题描述

### 现象
1. **项目级插件开关无人迁移**：团队项目常在提交进 git 的 `.claude/settings.json` 里写 `"enabledPlugins": {"req@devflow": true}`。req 更名为 rd 后该键失效，但 `/rd:migrate` 的扫描范围（CLAUDE.md、`docs/prompt/`、需求模板、`.claude/skills/`）不含它，教程 1.6 也没提。成员拉代码后项目启用的仍是只剩 `/req:help` 的过渡插件。
2. **GitHub 仓库建 PR 后无下一步提示**：`pr.md` 步骤 6 的「成功输出」（含「建议 `/rd:pr review`」「合并后 `/rd:pr merge`」）只写在 gitea 小节，github 小节只说「`gh pr create`，不可用给链接」。REQ-005 验收项 3 要求创建成功后提示 `/rd:pr review`，在 GitHub 仓库上没有文档依据，全靠执行者自行推断。

两处均在 REQ-004 / REQ-005 发布后的迁移讨论与补测中发现（v4.0.0 已发布，QUICK-004 #77 合并时未来得及并入）。

### 期望
1. `/rd:migrate` 检测项目级 `enabledPlugins` 中的 `req@devflow`，确认后替换为 `rd@devflow`；教程 1.6 写明这一步。
2. gitea / github 两种仓库创建（或复用）PR 后都输出统一的成功提示，下一步为 `/rd:pr review`。

---

## 实现方案

### 问题分析
1. REQ-004 设计「只换前缀」时把迁移对象限定为 DevFlow 自有文件，遗漏了 Claude Code 自身配置里以插件名为键的 `enabledPlugins`——插件改名恰恰让这个键失效。
2. `pr.md` 步骤 6 的成功输出块排版在 `#### gitea` 之下，语义上被归属到 gitea，github 分支缺少对应输出定义。

### 解决方案
1. **`plugins/rd/commands/migrate.md`** 新增「2D. 项目级插件开关（req 插件更名为 rd 后）」：
   - 读 `.claude/settings.json` 与 `.claude/settings.local.json` 的 `enabledPlugins`；存在 `req@devflow` 时展示并确认，确认后键名改为 `rd@devflow`、值保持不变；两键同时存在时只删除 `req@devflow`
   - 注明这是本命令唯一会改 `.claude/` 的地方（Claude Code 自身配置，非 DevFlow 字段）；无该键时静默跳过
   - 同步开头「支持几类迁移」列表、命令格式说明（无参数时一并检测 2C / 2D）、「3. 输出结果」汇总
2. **`docs/tutorial.md` / `.en.md` / `.ko.md`** 1.6「req → rd」小节：「无需改动」行后加一条项目级 `enabledPlugins` 提醒
3. **`plugins/rd/commands/pr.md`** 步骤 6：成功输出块从 `#### gitea` 小节移出，放到三个平台小节之后作为公共输出——gitea / github 创建成功或复用已有 PR 时统一输出；github 不可用给 compare 链接时同样附下一步提示；other 保持原输出

### 涉及文件

| 文件 | 改动类型 | 说明 |
|-----|---------|------|
| plugins/rd/commands/migrate.md | 修改 | 新增 2D 项目级插件开关迁移，同步分类列表 / 命令格式 / 输出汇总 |
| docs/tutorial.md、docs/tutorial.en.md、docs/tutorial.ko.md | 修改 | 1.6 补 enabledPlugins 提醒（三语同一处） |
| plugins/rd/commands/pr.md | 修改 | 成功输出从 gitea 小节提到步骤 6 公共部分 |

### 改动量
- 预估：小
- 涉及文件：5 个（其中 3 个为教程三语同一处）
- 代码行数：约 30 行

---

## 验证方式

- [ ] 在含 `"enabledPlugins": {"req@devflow": true}` 的样例项目执行 `/rd:migrate` → 2D 列出该键，确认后变为 `rd@devflow` 且值不变；无该键的项目静默跳过（未实测；`migrate.md` 2D 文本已核对）
- [x] `pr.md` 步骤 6 中 gitea / github 均能找到成功输出定义，下一步为 `/rd:pr review`（#80 实测：github 回退 compare 链接时输出该提示）
- [x] 教程三语 1.6 含 enabledPlugins 提醒
- [x] `python3 scripts/check-layout.py --check` 通过；确认无副作用

---

## 开发记录

### 2026-09-15
- 创建快速需求（讨论「旧 req 项目如何升级」时发现 enabledPlugins 缺口；REQ-005 补测时发现 GitHub 成功输出缺口）
- 过渡插件 `/req:help` 按维护者决定不改（仅保留一个大版本，v5 删除）
- 实现随 #78 合并，v4.0.1 发布；过渡插件 req 后于 #79 提前移除
- 补测（rd 5.0.1）：#80 创建时 gh 未登录，按 github 回退输出 compare 链接 + `/rd:pr review` 下一步提示
- 用户确认归档（`/rd:done QUICK-005`），状态→已完成，移至 completed/
