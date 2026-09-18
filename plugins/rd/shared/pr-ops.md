# PR 子命令流程（status / comments / merge）

> 由 `/rd:pr <子命令>` 按需读取，不是独立命令；创建 PR 的流程在 `commands/pr.md`，AI 代码审查在 `commands/review.md`。先执行「通用前置」，再执行对应小节。

> 不受仓库角色限制，readonly 可执行。
>
> CLI 优先级：GitHub → `gh pr`/`gh api`；Gitea → 按 [`_gitea_cli.md`](../shared/_gitea_cli.md) 检测 `tea`。tea 未覆盖的接口走 curl。

## 通用前置

- 依赖已创建的 PR；未找到关联 PR 时提示先执行 `/rd:pr` 创建
- 确定目标 PR：参数给 `PR-ID` 直接使用；给 `REQ-XXX` 取需求文档 `branch` 字段；都省略时从当前分支匹配
- **GitHub 的 gh 可用** = 已安装且 `gh auth status` 通过（只装未登录也算不可用）。不可用时：只读查询（status、comments 拉评论）回退公开 REST API，私有仓库无凭据时提示 `gh auth login` 后退出；写操作（合并）不执行，改为输出 PR 链接与手动操作指引

---

## status — 查看 PR 状态

根据 `repoType` 查询 PR（从需求文档 `branch` 字段取分支名，Gitea 需指定 `head=OWNER:branch`）。展示：PR 编号、标题、状态、合并方向、是否可合并、审查状态、可用操作。

---

## comments — 拉取并展示评论（只读）

### 1. 拉取评论

同时拉取 Issue Comments（整体讨论）和 Review Comments（行内评论，含 `path` 和 `line` 字段）。
Gitea：整体评论 `/issues/{N}/comments`，行内评论先 `GET /pulls/{N}/reviews` 再逐条 `/reviews/{ID}/comments`。

### 2. 过滤评论

排除：当前 git 用户自己的评论、已 resolved/outdated 的行评论、AI 自提交的审查报告（body 以 `AI 代码审查报告` 开头）。

### 3. 分组展示

按「整体评论 / 行内评论（按文件）」分组列出：作者、时间、正文，行内评论附 `path:line`。**不读源码、不生成方案、不改文件**。末尾提示：

```
要按评论改代码：/rd:review comments
```

`/rd:review comments` 复用本节的 1–2 步再做分析与修改。

---

## merge — 合并 PR

### 前置检查

PR 存在 → PR 为 Open → 无合并冲突。逐项失败时提示处理方式。

### 执行合并

读取 `branchStrategy.mergeMethod`（默认 `merge`），按平台执行（GitHub `gh pr merge --<mergeMethod>`，Gitea merge method 通过 `Do` 字段传递）。`repoType = "other"` 展示手动合并命令。

GitHub 的 gh 不可用时不尝试合并：输出 PR 链接，按 `mergeMethod` 提示网页上对应的按钮（`merge` → Create a merge commit、`squash` → Squash and merge、`rebase` → Rebase and merge），等用户回复已合；再查 API 确认 `merged=true` 才进入「合并后」，仍未合并则如实告知，不给归档提示。

### 合并后

输出合并信息，提示 `/rd:done` 归档。读取 `branchStrategy.deleteBranchAfterMerge`（默认 `true`），询问是否删除已合并分支。

---

## Git Flow 双 PR 场景

hotfix 分支可能存在两个 PR（→ main + → develop），分别展示，按先 main 后 develop 顺序操作。

---

## 与 `/rd:release` 的关系

`/rd:pr merge` 是单需求里程碑，不是发版：
- migration SQL 在 merge 时不会被归档，等 `/rd:release` 统一处理
- 合并到 developBranch ≠ 发布
- 不要手工 tag 或建 Release，应由 `/rd:release` 原子化完成

