---
description: 轻量修复 - 无文档的 bug 修复流程，AI 辅助定位问题
---

# 轻量修复

创建修复分支，AI 辅助分析定位 bug，修复后直接提交和 PR。不创建需求文档。

> 此命令**不受仓库角色限制**，readonly 仓库也可执行。
> 不触发缓存同步（无需求文档）。

## 命令格式

```
/req:fix <问题描述>
```

示例：
- `/req:fix 登录超时后 token 未清除`
- `/req:fix 订单列表分页数据重复`
- `/req:fix 导出 Excel 中文文件名乱码`

---

## 执行流程

### 1. 工作区检查

```bash
git status --porcelain
```

有未提交改动时终止，提示先 commit 或 stash。

### 2. 读取分支策略

```python
strategy = read_settings("branchStrategy")

if strategy:
    MAIN_BRANCH = strategy["mainBranch"]
    BRANCH_FROM = strategy.get("branchFrom", MAIN_BRANCH)
    FIX_PREFIX = strategy.get("fixPrefix", "fix/")
else:
    MAIN_BRANCH = detect_main_branch()
    BRANCH_FROM = MAIN_BRANCH
    FIX_PREFIX = "fix/"
```

### 3. 创建修复分支

AI 根据问题描述生成英文 slug（lowercase kebab-case，最多 5 词）：

```
将创建修复分支：fix/login-token-not-cleared
基于分支：main
```

用户确认后：

```bash
git fetch origin $BRANCH_FROM
git checkout -b ${FIX_PREFIX}<slug> origin/$BRANCH_FROM
```

### 4. AI 辅助分析 bug

> 读取项目 CLAUDE.md 的「项目架构」章节，了解分层结构和目录布局。

根据用户描述的问题，AI 进行定位分析：

#### 4.1 问题分析

```
🔍 Bug 分析：登录超时后 token 未清除

📋 问题理解：
- 现象：用户登录超时后，本地 token 未被清除，导致后续请求携带过期 token
- 影响范围：认证流程、请求拦截器

🔎 可能涉及的代码：
```

#### 4.2 定位相关文件

AI 搜索代码库，定位可能相关的文件：

```
📂 相关文件定位：

| 文件 | 相关度 | 原因 |
|------|-------|------|
| src/utils/auth.ts | 高 | token 存取逻辑 |
| src/interceptors/request.ts | 高 | 请求拦截，超时处理 |
| src/store/user.ts | 中 | 用户状态管理 |
```

#### 4.3 根因分析

AI 阅读相关代码后给出根因判断：

```
🎯 根因分析：

在 src/interceptors/request.ts:45，响应拦截器捕获 401 状态码时
调用了 router.push('/login')，但未调用 removeToken()。

建议修复：在跳转登录页前清除 token。
```

#### 4.4 修复建议

```
💡 修复建议：

1. src/interceptors/request.ts
   - 在 401 处理分支中，跳转前调用 removeToken()

2. 建议同时检查：
   - token 过期的其他入口（如定时刷新失败）
```

### 5. 用户确认后执行修复

AI 展示修复方案后等待用户确认：

```
是否按以上方案修复？（可以补充说明或调整方向）
```

用户确认后，AI 按方案修改代码。

### 6. 修复完成提示

```
✅ 修复完成！

🌿 分支：fix/login-token-not-cleared
📝 修改文件：
- src/interceptors/request.ts（+3 -1）

💡 后续操作：
- /req:commit - 提交修复代码
- /req:pr - 创建 PR
```

---

## 与其他修复方式的区别

| 方式 | 命令 | 文档 | 分支 | 适用场景 |
|------|------|------|------|---------|
| 轻量修复 | `/req:fix` | 无 | fix/slug | 日常小 bug，改动 < 5 个文件 |
| 有记录的修复 | `/req:new-quick` | QUICK 文档 | fix/QUICK-XXX-slug | 需要记录的修复，方便追溯 |
| 紧急修复 | `/req:branch hotfix` | 无 | hotfix/slug | 线上紧急问题，从主分支拉 |

**选择依据：**
- 改完就忘的小 bug → `/req:fix`
- 需要测试和记录的修复 → `/req:new-quick`
- 线上出问题了 → `/req:branch hotfix`

---

## 用户输入

$ARGUMENTS
