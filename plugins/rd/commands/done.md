---
description: 完成需求 - 标记完成并归档
argument-hint: "[REQ-XXX|QUICK-XXX]"
allowed-tools: Read, Write, Edit, Glob, Bash(git:*, mv:*, gh:*, tea:*, curl:*)
model: claude-haiku-4-5-20251001
---

# 完成需求

标记需求为已完成，归档文档。

> 存储路径规则见 [_storage.md](../shared/_storage.md)
>
> **CLI 优先级**：GitHub 走 `gh`；Gitea 按 [`_gitea_cli.md`](../shared/_gitea_cli.md) 检测 `tea`，可用即走 `tea pulls create` / `tea issues close`，否则回退本文 curl 示例。

## 命令格式

```
/rd:done [REQ-XXX|QUICK-XXX]
```

- 省略编号时自动选择「测试中」的需求
- 多个候选时交互式选择

---

## 执行流程

### 1. 选择需求

- 指定编号 → 使用该需求
- 未指定 → 扫描 `active/` 中状态为「测试中」的需求，唯一则直接使用，多个则列出让用户选

### 2. 前置检查

- 读取需求文档元信息，按类型取验证章节：REQ「六、测试要点」/ QUICK「验证方式」（见 `_storage.md`「双轨状态机」）
- 文档已在 `completed/` → 提示「已归档」退出
- 状态必须为「测试中」（REQ 与 QUICK 相同；QUICK 未经 `/rd:test` 时提示先执行），否则报错退出
- 未勾选项：带「（待观察：…）」「（未实测：…）」标注的放行，在步骤 6 输出中列出；裸 `- [ ]` 展示警告并要求用户确认继续

### 3. 更新需求文档

修改元信息：
- 状态：已完成
- 完成日期：YYYY-MM-DD（今日；元信息表无此行时追加）

勾选生命周期「已完成」对应的复选框。

### 4. 更新 PRD 索引

仅 REQ：定位 `docs/requirements/PRD.md` 的「需求追踪」章节（`grep -n "需求追踪"`），更新对应需求所在行的「状态」和「完成日期」两列。PRD 不存在、无该章节或需求为 QUICK 时静默跳过。

### 5. 归档文档

将需求文档从 `active/` 移动到 `completed/`（使用 `git mv` 保留历史）。

### 6. 输出确认

```
REQ-XXX <标题> 已完成
   归档至 docs/requirements/completed/REQ-XXX-<slug>.md
   放行的未勾项（已标注）：
   - <项>（待观察：<原因>）      ← 有则列出

查看列表：/rd:req（索引由该命令实时渲染，无需维护文件）
```

QUICK 同样格式，编号与路径换成 `QUICK-XXX`。

### 7. 分支合并提醒

读取 `.devflow/settings.json` 的 `branchStrategy` 和需求文档的 `branch` 字段。无 `branchStrategy` 或 `branch` 为空 → 跳过本步。

按 `repoType` 创建 PR，逻辑同 [pr.md](./pr.md)（push + 创建 PR + 提示 `/rd:review`）。

**特殊情况**：
- `giteaToken` 缺失 → 提示手工 compare 链接
- Git Flow + hotfix 分支 → 需合并到 `main` 和 `develop` 两处，创建两个 PR

### 8. 关联 issue 关闭提醒

按 [_issue.md 的 Issue 读取优先级](../shared/_issue.md#issue-编号的读取优先级) 获取 issue 编号：先查需求文档元信息 `issue` 字段，若为 `-` 或为空则查分支名 `-iN` 后缀。均未找到 → 跳过本步。

否则询问用户：

```
检测到关联 issue: #123
   是否关闭该 issue？(y/n)
```

**用户确认（y）** → 按 `repoType` 关闭 issue，逻辑同 [issue.md §5](./issue.md)。

**用户拒绝（n）**：跳过。

---

## 与 `/rd:release` 的区别

`/rd:done` 只做归档，不发版。发版用 `/rd:release`（合并 SQL / 生成 changelog / 打 tag / 创建 Release）。

## 用户输入

$ARGUMENTS
