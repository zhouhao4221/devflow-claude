# QUICK-006 /rd:pr merge 补 gh 不可用时的处理 + mergeMethod 改 squash

## 元信息

| 字段 | 值 |
|-----|-----|
| 编号 | QUICK-006 |
| 改动类型 | bug修复 |
| 端类型 | 全栈 |
| 状态 | 开发中 |
| 模块 | 快速修复 |
| 优先级 | P2 |
| 创建时间 | 2026-09-15 |
| 负责人 | |
| 关联需求 | REQ-005、QUICK-005 |
| branch | fix/QUICK-006-pr-merge-without-gh |
| issue | - |

## 生命周期

- [x] 草稿
- [x] 方案确认
- [x] 开发中
- [ ] 已完成

---

## 问题描述

### 现象
1. **`/rd:pr merge` 在 gh 不可用时无路可走**：REQ-005 补测验收项 2 时，#80 合并前置检查全部通过，但本机 `gh` 已安装、未登录。`pr-ops.md` 的 merge 小节只写「GitHub `gh pr merge --<mergeMethod>`」，没有 gh 不可用时的处理，执行者只能自行推断；最终由维护者手动合并。同一小节的 status / review / comments 也都假设 gh 可用（`gh pr view`、提交审查评论、Approve）。
2. **gh 可用判定只看是否安装**：`pr.md` 创建流程 github 小节用 `command -v gh` 判定，「已安装未登录」会被当成可用，`gh pr create` 失败后才发现。
3. **本仓库 `mergeMethod` 与实际做法不符**：`.devflow/settings.json` 为 `"merge"`，本仓库一律 squash merge（每个 PR 单提交）；gh 可用时 `/rd:pr merge` 会产生 merge commit。

### 期望
1. GitHub 的 gh 不可用（未安装或未登录）时：只读查询回退公开 REST API；提交评论、Approve、合并等写操作不执行，改为输出 PR 链接与手动操作指引；合并时按 `mergeMethod` 提示网页上对应的按钮，用户回复已合后经 API 核实 `merged` 才进入「合并后」。
2. 创建与子命令对 gh 可用的判定一致：已安装且 `gh auth status` 通过。
3. 本仓库 `mergeMethod` 改为 `squash`。

---

## 实现方案

### 问题分析
1. `pr-ops.md` 由 `review-pr.md` 迁移而来（REQ-005），原命令即只描述 gh / Gitea API 的正常路径；QUICK-005 只给创建流程补了「gh 不可用给 compare 链接」的输出，子命令一侧没有对应规则。
2. `pr.md` 的 `command -v gh` 只能识别未安装，识别不了未登录——本机即此状态，#80 创建时靠执行者额外跑 `gh auth status` 才走对回退。
3. `mergeMethod` 为 `/rd:branch init` 时的缺省值，未随仓库合并约定调整。

### 解决方案
1. **`plugins/rd/shared/pr-ops.md`「通用前置」** 新增一条：GitHub 的 gh 可用 = 已安装且 `gh auth status` 通过；不可用时，只读查询（status、review 取 PR 元数据、comments 拉评论）回退公开 REST API（私有仓库无凭据时提示 `gh auth login` 后退出），写操作（提交审查评论、Approve、合并）不执行，输出 PR 链接与手动操作指引，审查报告仅本地展示。
2. **`pr-ops.md`「merge」** 执行合并处补 gh 不可用分支：输出 PR 链接，并按 `mergeMethod` 提示网页按钮（`merge` → Create a merge commit、`squash` → Squash and merge、`rebase` → Rebase and merge）；用户回复已合后查 API 确认 `merged=true` 再执行「合并后」，未合并则如实提示，不进入归档提示。
3. **`plugins/rd/commands/pr.md` 步骤 6 github**：`检查 command -v gh` 改为「gh 已安装且 `gh auth status` 通过」，其余不变。
4. **`.devflow/settings.json`**：`branchStrategy.mergeMethod` 由 `"merge"` 改为 `"squash"`（本仓库配置，非插件行为）。

### 涉及文件

| 文件 | 改动类型 | 说明 |
|-----|---------|------|
| plugins/rd/shared/pr-ops.md | 修改 | 通用前置补 gh 可用判定与降级规则；merge 补 gh 不可用时的手动合并 + API 核实 |
| plugins/rd/commands/pr.md | 修改 | 步骤 6 github 的 gh 可用判定加上已登录 |
| .devflow/settings.json | 修改 | 本仓库 mergeMethod 改为 squash |

### 改动量
- 预估：小
- 涉及文件：3 个
- 代码行数：约 15 行

---

## 验证方式

- [x] `pr-ops.md` 通用前置写明 gh 可用判定（已安装且已登录）、只读回退公开 API、写操作降级为链接与手动指引
- [x] `pr-ops.md` merge 小节 gh 不可用时输出 PR 链接 + 按 `mergeMethod` 的网页按钮提示，用户回复已合后经 API 核实 `merged` 才进入「合并后」
- [x] `pr.md` 步骤 6 github 判定含已登录；`.devflow/settings.json` 的 `mergeMethod` 为 `squash`
- [ ] 升级到含本修复的 rd 版本后，在 gh 未登录环境对一个 open PR 执行 `/rd:pr merge` → 输出链接与 Squash and merge 提示，手动合并后核实通过并提示 `/rd:done`
- [x] `python3 scripts/check-layout.py --check` 通过；确认无副作用

---

## 开发记录

### 2026-09-15
- 创建快速需求（REQ-005 补测验收项 2：#80 `/rd:pr merge` 在 gh 未登录时无处理规则，维护者手动 squash 合并；同时发现本仓库 mergeMethod 与 squash 约定不符）
- 方案经用户确认，进入开发；完成 3 个文件改动，文档核对项与守卫通过；运行时验证（gh 未登录环境执行 `/rd:pr merge`）待发版升级后补测
