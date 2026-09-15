---
description: 查看需求项目 - 当前仓库对应的需求项目、需求目录与统计
allowed-tools: Read, Glob, Bash(ls:*)
model: claude-haiku-4-5-20251001
---

# 查看需求项目

v3 起没有全局缓存和中心索引：每个 primary 仓库的 `requirementsDir` 就是一个需求项目，readonly 仓库经 `requirementSource.path` 绑定其中一个。本命令展示当前仓库对应的那个项目。

## 命令格式

```
/req:projects [--detail]
```

---

## 执行流程

### 1. 读取配置

读取 `.devflow/settings.json` 的 `requirementProject` / `requirementRole` / `requirementsDir`，再用 `.devflow/settings.local.json` 覆盖同名字段（含 `requirementSource`）。

无 `requirementProject` 时输出后结束：

```
当前仓库未初始化需求项目

  主仓库：/req:init <project-name>
  只读仓库：/req:use <primary-repo-path>
```

### 2. 确定需求根目录

- `primary` / 未配置角色：本仓 `requirementsDir`（缺省 `docs/requirements`）
- `readonly`：`<requirementSource.path>/<主仓 requirementsDir>`；目录不存在 → 提示主仓路径失效，重新 `/req:use <primary-repo-path>` 绑定，结束

### 3. 统计

- `active/`、`completed/` 下的需求文档数
- `modules/*.md` 模块数
- `--detail`：活跃需求按元信息「状态」分组计数（草稿 / 待评审 / 评审通过 / 开发中 / 测试中）

### 4. 输出

```
需求项目

项目：my-saas-product（primary）
需求目录：docs/requirements/
需求：活跃 3 · 已完成 12 · 模块 4

可用命令：
  /req            列出需求
  /req:modules    模块概览
```

readonly 仓库在「需求目录」下追加一行 `主仓：<requirementSource.path>`。`--detail` 在「需求」下追加状态分布：

```
状态分布：草稿 1 · 待评审 1 · 开发中 1
```

---

## 用户输入

$ARGUMENTS
