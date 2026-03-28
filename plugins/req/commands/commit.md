---
description: 规范提交 - 生成 Conventional Commits 格式的 Git 提交
---

# 规范提交

生成符合 Conventional Commits 规范的 Git 提交，自动关联当前需求编号，便于后续 `/req:changelog` 生成版本说明。

> 此命令**不受仓库角色限制**，readonly 仓库也可执行。
> 不触发缓存同步。

## 命令格式

```
/req:commit [消息]
```

**示例：**
- `/req:commit` — 交互式选择类型并生成提交
- `/req:commit 实现部门渠道关联` — 自动分析变更并生成提交

---

## 执行流程

### 1. 检查工作区状态

```bash
git status --short
git diff --cached --stat
```

**无变更时：**
```
❌ 没有可提交的变更

💡 请先暂存文件：
- git add <file>       暂存指定文件
- git add -A           暂存所有变更
```

**有未暂存变更时：**
自动将所有变更暂存（`git add -A`），展示暂存结果：

```
📁 已暂存所有变更：
  M  internal/sys/biz/dept_channel.go
  A  internal/sys/model/sys_dept_channel_model.go
  M  internal/sys/controller/v1/sys_dept.go
  M  internal/sys/router.go
```

### 2. 分支合规检查（自动切换/创建分支）

> 读取 `.claude/settings.local.json` 的 `branchStrategy`，未配置时跳过此步骤。

```python
strategy = read_settings("branchStrategy")
current_branch = git("branch --show-current")

if strategy:
    main_branch = strategy["mainBranch"]
    develop_branch = strategy.get("developBranch")
    branch_from = strategy.get("branchFrom", main_branch)

    # 检测活跃需求（开发中/测试中）
    active_reqs = find_active_requirements()

    # 判断是否在保护分支上（mainBranch 或 developBranch）
    on_protected = current_branch in [main_branch, develop_branch]

    if on_protected and active_reqs:
        # 只有一个活跃需求 → 自动处理
        # 多个活跃需求 → 让用户选择
        if len(active_reqs) == 1:
            req = active_reqs[0]
        else:
            print("检测到多个活跃需求：")
            for i, r in enumerate(active_reqs):
                print(f"  {i+1}. {r.id} {r.title}")
            print(f"  {len(active_reqs)+1}. 跳过，继续在 {current_branch} 提交")
            # 等待用户选择
            req = user_choice

        if req:
            if req.branch and req.branch != "-":
                # 情况 A：需求已有分支 → 暂存变更，切换到需求分支
                print(f"🔀 当前在 {current_branch}，自动切换到需求分支：{req.branch}")
                git("stash")
                git(f"checkout {req.branch}")
                git("stash pop")
            else:
                # 情况 B：需求无分支 → 创建新分支，更新需求文档的 branch 字段
                prefix = strategy.get("featurePrefix", "feat/") if req.id.startswith("REQ") else strategy.get("fixPrefix", "fix/")
                slug = to_kebab_case(translate_to_english(req.title))  # 最多 5 词
                new_branch = f"{prefix}{req.id}-{slug}"

                print(f"🔀 当前在 {current_branch}，自动创建需求分支：{new_branch}")
                git(f"checkout -b {new_branch} {branch_from}")
                # 更新需求文档的 branch 字段
                update_requirement_meta(req, branch=new_branch)

    elif on_protected and not active_reqs:
        # 无活跃需求，正常提交（文档、配置等非需求变更）
        pass

    # 情况 C：在 hotfix 分支上
    elif current_branch.startswith(strategy.get("hotfixPrefix", "hotfix/")):
        print(f"🚨 当前在紧急修复分支：{current_branch}")
        # 正常提交，类型建议选「修复」

    # 情况 D：在需求分支上
    else:
        # 正常提交，尝试从分支名匹配需求编号
        pass
```

**各场景行为总结：**

| 当前分支 | 有活跃需求 | 行为 |
|---------|-----------|------|
| mainBranch | 1个，已有需求分支 | 🔀 stash → 切换到需求分支 → stash pop → 提交 |
| mainBranch | 1个，无需求分支 | 🔀 自动创建需求分支 → 切换 → 提交 |
| mainBranch | 多个 | 让用户选择需求或跳过 |
| mainBranch | 无 | 正常提交（文档、配置等非需求变更） |
| developBranch | 有 | 同 mainBranch 逻辑 |
| hotfix/* 分支 | — | 正常提交，自动建议「修复」类型 |
| feat/REQ-XXX-* | — | 正常提交，自动关联对应 REQ |
| fix/QUICK-XXX-* | — | 正常提交，自动关联对应 QUICK |

### 3. Code Review 提醒

提交前展示代码审查提醒（信息展示，不等待回复）：

```
⚠️ 提交前请确认已完成 Code Review
   检查要点：逻辑正确性、安全隐患、错误处理、代码规范、调试代码清理
```

### 4.5 检测当前需求

**优先从分支名匹配**（步骤 2 已获取当前分支信息）：

```python
current_branch = git("branch --show-current")

# 优先：从分支名提取需求编号
import re
branch_match = re.search(r'(REQ-\d+|QUICK-\d+)', current_branch)
if branch_match:
    CURRENT_REQ = branch_match.group(1)
else:
    # 回退：扫描活跃需求
    PROJECT = read_settings("requirementProject")
    ROLE = read_settings("requirementRole")

    if ROLE == "readonly":
        active_dir = f"~/.claude-requirements/projects/{PROJECT}/active/"
    else:
        active_dir = "docs/requirements/active/"

    active_reqs = find_requirements(active_dir, status=["开发中", "测试中"])

    if len(active_reqs) == 1:
        CURRENT_REQ = active_reqs[0]
    elif len(active_reqs) > 1:
        print("检测到多个活跃需求：")
        for i, req in enumerate(active_reqs):
            print(f"  {i+1}. {req}")
        print(f"  {len(active_reqs)+1}. 不关联需求")
    else:
        CURRENT_REQ = None
```

### 5. 分析变更内容

读取 `git diff --cached` 的内容，分析暂存的代码变更：

- 变更性质（新增功能、修复问题、重构等）
- 变更描述（从代码差异中提炼）

### 6. 生成提交信息

#### 6.1 选择提交类型

如果用户未提供消息，交互式选择：

```
📝 选择提交类型：

  1. 新功能     新增功能
  2. 修复       问题修复
  3. 重构       代码重构
  4. 优化       性能优化
  5. 文档       文档更新
  6. 测试       测试相关
  7. 构建       构建/工具/依赖
  8. 样式       代码格式（不影响逻辑）
```

如果用户已提供消息，根据变更内容和消息自动推断类型。

#### 6.2 组装提交消息

**格式：**
```
前缀: 描述 (REQ-XXX)
```

**规则：**
- `前缀`：必填，中文类型前缀
- 描述：简洁的中文描述
- `(REQ-XXX)`：自动追加当前需求编号（如有）

**前缀映射：**

| 前缀 | 含义 | Changelog 分类 |
|------|------|---------------|
| `新功能` | 新增功能 | 新功能 (Features) |
| `修复` | 问题修复 | 问题修复 (Bug Fixes) |
| `重构` | 代码重构 | 重构优化 (Refactoring) |
| `优化` | 性能优化 | 性能优化 (Performance) |
| `文档` | 文档更新 | 文档更新 (Documentation) |
| `测试` | 测试相关 | 测试 (Tests) |
| `构建` | 构建/工具/依赖 | 其他变更 (Others) |
| `样式` | 代码格式 | 其他变更 (Others) |

**示例：**
```
新功能: 实现部门渠道关联 (REQ-001)
修复: 订单渠道过滤逻辑错误 (REQ-001)
重构: 部门服务层代码 (QUICK-003)
文档: 更新 API 文档
构建: 升级依赖版本
```

### 7. 确认并提交

展示完整提交预览：

```
📋 提交预览：

  类型：新功能
  描述：实现部门渠道关联
  关联：REQ-001

  完整消息：
  新功能: 实现部门渠道关联 (REQ-001)

  变更文件（4）：
  A  internal/sys/model/sys_dept_channel_model.go
  A  internal/sys/store/sys_dept_channel_store.go
  A  internal/sys/biz/dept_channel.go
  M  internal/sys/router.go

```

展示预览后直接执行提交（Hook 会弹出原生确认对话框）：

```bash
git commit -m "新功能: 实现部门渠道关联 (REQ-001)"
```

### 8. 提交结果

```
✅ 提交成功！

  commit abc1234
  新功能: 实现部门渠道关联 (REQ-001)

  4 files changed, 156 insertions(+), 3 deletions(-)

💡 后续操作：
- 继续开发：/req:dev
- 再次提交：/req:commit
- 推送远程：git push
- 生成版本说明：/req:changelog <version>
```

---

## Breaking Change 支持

如果变更包含破坏性改动，在前缀后添加 `!` 标记：

```
新功能!: 重构部门 API 返回结构 (REQ-005)
```

交互式流程中增加确认：

```
如果变更涉及 API 返回结构变更、数据库 schema 变更等，自动标记为 Breaking Change。
```

---

## 多行提交消息

对于需要详细说明的提交，支持添加 body：

```
新功能: 实现部门渠道关联 (REQ-001)

- 新增 sys_dept_channel 表及 Model/Store 层
- 实现渠道范围校验逻辑
- 添加获取可选渠道接口
```

当变更涉及多个文件或逻辑复杂时，自动添加 body 说明。

---

## 与 Changelog 的对应关系

本命令生成的提交消息使用中文前缀，`/req:changelog` 可直接解析：

| 提交格式 | Changelog 分类 |
|---------|---------------|
| `新功能: 描述 (REQ-XXX)` | 新功能 (Features) |
| `修复: 描述 (REQ-XXX)` | 问题修复 (Bug Fixes) |
| `重构: 描述` | 重构优化 (Refactoring) |
| `优化: 描述` | 性能优化 (Performance) |
| `文档: 描述` | 文档更新 (Documentation) |
| `测试: 描述` | 测试 (Tests) |
| `构建/样式: 描述` | 其他变更 (Others) |

**需求编号关联**：commit message 中的 `(REQ-XXX)` / `(QUICK-XXX)` 会被 changelog 自动提取并归入「关联需求」章节。

## 用户输入

$ARGUMENTS
