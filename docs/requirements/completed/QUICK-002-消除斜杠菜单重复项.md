# QUICK-002 消除斜杠菜单重复项

## 元信息

| 字段 | 值 |
|-----|-----|
| 编号 | QUICK-002 |
| 改动类型 | bug修复 |
| 端类型 | 全栈 |
| 状态 | 已完成 |
| 模块 | 插件架构 |
| 优先级 | P1 |
| 创建时间 | 2026-08-24 |
| 负责人 | haiqing |
| 关联需求 | REQ-003（本需求废止其派生机制） |
| branch | fix/QUICK-002-slash-menu-duplicates |
| issue | - |
| completedAt | 2026-08-24 |

## 生命周期

- [x] 草稿
- [x] 方案确认
- [x] 开发中
- [x] 已完成

---

## 问题描述

### 现象

用户在 Claude Code 输入 `/req` 唤起补全菜单，同一条命令出现多遍：

```
/req:do    (req) 智能开发 - AI 分析意图，自动选择流程，生成方案并执行
/req:do    (req) 智能开发 - AI 分析意图，自动选择流程，生成方案并执行
/req:pr    (req) 创建 PR - 根据仓库类型自动创建 Pull Request
/req:pr    (req) 创建 PR - 根据仓库类型自动创建 Pull Request
```

`claude plugin details req`（Claude Code 2.1.241）的组件清单坐实了重复：

```
Skills (77)  _branch, _claude-md, _common, ..., branch, branch, changelog, changelog,
             dev, dev, do, do, done, done, ..., pr, pr, ...
```

77 = `commands/` 44 个文件 + `skills/` 33 个目录。成对出现的名字在 per-component 表里也是两行（`do` ~8.6k 是内联附录的 skill，`do` ~2.9k 是 command）。

### 期望

一条命令在斜杠菜单里只出现一次。

---

## 实现方案

### 问题分析

两个独立成因，都在本仓库：

1. **命令镜像 skill（主因，51 处）**。REQ-003 建立了「command 单源派生 skill 镜像」机制，前提是「skill 服务于不支持 slash 的客户端」。该前提在 Claude Code 2.x 已不成立——它把插件 skill 也暴露成 `/<plugin>:<skill>`，与同名 command 落在同一个菜单里，`description` 还由生成器逐字复制，两项完全无法区分。受影响：req 23 · pm 12 · api 6 · uat 6 · diag 4。

2. **共享参考文档被注册成伪命令（次因，12 处）**。`commands/` 下的**每个** `.md` 都会被注册，包括没有 frontmatter 的 `_storage.md`、`_common.md`、`release-rationale.md` 等，变出 `/req:_storage` 这类条目，各自还占 ~20–30 always-on token。

排除的两个非成因：`~/.claude/plugins/cache/devflow/req/` 下虽有 3 个版本目录（4.0.0 / 4.1.0 / 4.1.1），但 `claude plugin list` 只加载 4.1.1，旧的已打 `.orphaned_at`；本地仓库也不存在重名命令文件。

### 解决方案

**command 是能力的唯一入口**，`skills/` 只留与命令不同名的手写 helper skill。

1. 删除 51 个镜像 skill 目录 + `plugins/api/skills/_common.md`（只被镜像引用的陈旧副本）。14 个 helper skill 原样保留。
2. 12 个共享参考文档移到 `plugins/<p>/shared/`，48 处链接 `](./_x.md)` 改写为 `](../shared/_x.md)`。api/pm 有 5 个文件原先只写纯文本 `` `_common.md` ``、不给路径，首处提及升级为真链接。
3. `scripts/gen-skills.py` 派生器退役，换成 `scripts/check-layout.py` 守卫，一次守住三条：`skills/` 无命令镜像、`commands/` 无非命令文件（必须有 frontmatter + `description`）、所有相对链接可达。接入 `/req:release` 发布前置。
4. 顺带修掉链接检查暴露的既存幽灵引用：`scripts/migrate-config.sh` 在仓库中根本不存在，却被 3 处引用；迁移逻辑本就写在 `/req:migrate` 自身，三处改为指向该命令。

### 涉及文件

| 文件 | 改动类型 | 说明 |
|-----|---------|------|
| plugins/{req,pm,api,diag,uat}/skills/<命令名>/ | 删除 | 51 个命令镜像 skill |
| plugins/api/skills/_common.md | 删除 | 只被镜像引用的陈旧副本 |
| plugins/{req,pm,api}/shared/*.md | 移动 | 12 个共享参考文档移出 commands/ |
| plugins/*/commands/*.md | 修改 | 48 处链接改写 + 5 处纯文本提及升级为链接 |
| scripts/gen-skills.py | 删除 | 派生器退役 |
| scripts/check-layout.py | 新增 | 布局守卫（镜像 / 伪命令 / 悬空链接） |
| plugins/req/commands/release.md | 修改 | 发布前置换成 check-layout.py |
| plugins/req/commands/migrate.md、shared/_storage.md | 修改 | 移除 migrate-config.sh 幽灵引用 |
| CLAUDE.md | 修改 | 「命令与技能结构」重写、心智模型 3、维护规则 1/2/7 |
| docs/design/token-optimization.md | 修改 | 「共享文件禁止互引」理由从生成器内联改为链接展开 |
| docs/requirements/modules/插件架构.md | 修改 | 双形态分发 → 单一入口，F1 废止、F2 完成 |

### 改动量
- 预估：中
- 涉及文件：99 个（53 删 / 12 移 / 33 改 / 1 增）
- 菜单项：142 → 78

---

## 验证方式

- [x] `python3 scripts/check-layout.py --check` 通过：64 个命令 + 14 个 helper skill = 78 个菜单项，无重复，83 个相对链接全部可达
- [x] 注入三类回归（假镜像 skill / commands/ 下放无 frontmatter 文件 / 制造悬空链接），守卫全部命中并退出码 1
- [x] 无参运行自动清理镜像与散落文件，其余报出要求手工修复
- [x] `bash plugins/diag/tests/smoke.sh` 35/35 通过
- [x] 全仓无残留 `gen-skills` / `check-skills` / `commands/_*` 路径引用（changelog 与已归档需求中的历史记述保留不动）

---

## 开发记录

### 2026-08-24
- 用户报告 `/req` 菜单命令重复；`claude plugin details req` 定位到 command 与镜像 skill 双重注册
- 删除 51 个镜像 skill，`gen-skills.py` 退役
- 12 个共享参考文档移出 `commands/`，新增 `check-layout.py` 守卫三类布局问题
- 修掉守卫暴露的 `migrate-config.sh` 幽灵引用（既存缺陷，与本次重复问题无关）
