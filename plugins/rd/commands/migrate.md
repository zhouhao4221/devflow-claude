---
description: 迁移 - 旧布局迁到 .devflow、调整需求目录、req→rd 命令前缀与插件开关替换
allowed-tools: Read, Write, Edit, Glob, Grep, Bash(mkdir:*, mv:*, ls:*, rm:*)
model: claude-haiku-4-5-20251001
---

# 迁移需求

支持四类迁移：
1. **配置迁移**：从 v2.x 旧布局（`.claude/` 配置 + `~/.claude-requirements/` 全局缓存）迁到 v3（`.devflow/` + 无缓存）
2. **目录迁移**：调整需求文档存放目录（`requirementsDir`）
3. **命令前缀迁移**：req 插件更名为 rd 后，把本项目文件里残留的旧前缀 `/req:` 替换为 `/rd:`（逐项确认）
4. **插件开关迁移**：项目级 `.claude/settings.json(.local)` 的 `enabledPlugins` 中旧插件名 `req@devflow` 改为 `rd@devflow`（确认后替换）

## 命令格式

```
/rd:migrate [--to=<new-requirementsDir>]
```

- 无参数：执行配置迁移（旧布局 -> `.devflow/`），并检测旧前缀 `/req` 引用（2C）与项目级插件开关（2D）
- `--to=<dir>`：把需求目录迁移到新位置并更新 `requirementsDir`

---

## 执行流程

### 1. 识别当前布局

读 `.devflow/settings.json`（新）或 `.claude/settings.json(.local)`（旧）。检测是否存在旧全局缓存 `~/.claude-requirements/projects/<project>/`。

### 2A. 配置迁移（检测到 `.claude/` 旧 DevFlow 配置）

- 把 `.claude/settings.json(.local)` 中的 DevFlow 字段搬到 `.devflow/`：
  - `requirementProject` / `requirementRole` / `requirementsDir` / `branchStrategy` -> `.devflow/settings.json`
  - `giteaToken` -> `.devflow/settings.local.json`
- **不搬** Claude Code 自身的 hooks/permissions（留在 `.claude/settings.json`）
- readonly 仓库：提示改用 `/rd:use <primary-repo-path>` 重新绑定（旧缓存寻址已废弃）

> **旧全局缓存的数据**：primary 仓库的需求文档本就在本地 `docs/requirements/`，缓存只是副本。迁移确认本地完整后，可手动删除 `~/.claude-requirements/projects/<project>/`。若出现本地缺失、仅缓存有的异常，先从缓存 `mv` 回本地需求目录再删缓存。

### 2B. 目录迁移（提供 `--to`）

- 将当前 `requirementsDir` 下全部内容 `mv` 到 `--to` 指定的新目录
- 更新 `.devflow/settings.json` 的 `requirementsDir` 为新值

### 2C. 命令前缀迁移（req 插件更名为 rd 后）

无参数执行时与 2A 一并检测。

**扫描范围**（只扫这些，其余不动）：`CLAUDE.md`、`docs/prompt/**/*.md`、`<requirementsDir>/templates/*.md`、`.claude/skills/**/*.md`。需求文档（`active/`、`completed/`）与 `docs/changelogs/` 是历史记录，不扫。

**识别规则**（旧前缀 → 新前缀，按顺序匹配）：
- 审查类命令先单独映射（顺序敏感，先长后短）：`/req:review-pr review` → `/rd:review`、`/req:review-pr merge` → `/rd:pr merge`、`/req:review-pr fetch-comments` → `/rd:pr comments`、单独的 `/req:review-pr` → `/rd:pr status`；`/rd:pr review` → `/rd:review`；`/req:review` 与 `/rd:review`（旧语义只有需求评审，后面跟 `REQ-XXX` / `pass` / `reject` 或无参数）→ `/rd:req-review`。`/rd:pr comments` 不动（命令仍在，改为只读查看）
- `/req:<命令>` → `/rd:<命令>`
- 单独出现的 `/req`（入口命令：后面不是字母、`/`、`:`、`-`、`_`）→ `/rd:req`
- 不是命令的一律不碰：`docs/requirements`、`.claude/.req-auto`、`REQ-XXX`

**逐处确认**：下游文件可能被用户改写过，禁止静默批量替换。每处展示前后对比：

```
[1/7] CLAUDE.md:42（旧前缀）
  - 开发前先执行 /req:dev 生成方案
  + 开发前先执行 /rd:dev 生成方案
替换？(y 替换 / n 跳过 / a 本文件剩余全部替换 / q 结束)
```

未检测到时输出「未发现 /req 旧前缀引用，无需清理」。

### 2D. 项目级插件开关（req 插件更名为 rd 后）

无参数执行时与 2A、2C 一并检测。团队常把 `enabledPlugins` 写在提交进 git 的 `.claude/settings.json`，插件改名后旧键失效——成员拉代码后项目启用的仍是已不存在的旧插件名，rd 不会被加载。

- 读取 `.claude/settings.json` 与 `.claude/settings.local.json` 的 `enabledPlugins`
- 存在旧键 `req@devflow` → 展示所在文件与当前值，确认后键名改为 `rd@devflow`、值保持不变；`rd@devflow` 已存在时只删除旧键
- 只改这一个键，不动其它插件与 Claude Code 自身配置（hooks / permissions）；这是本命令唯一会修改 `.claude/` 的地方
- 未检测到旧键时静默跳过

### 3. 输出结果

显示迁移类型、搬运的字段/文件、新配置位置与后续提示（如 readonly 重绑定、删除旧缓存）。执行了 2C 时附替换汇总：已替换与跳过的 `文件:行号` 清单；执行了 2D 时列出改动的 settings 文件，并提示提交以便团队成员同步。

---

## 用户输入

$ARGUMENTS
