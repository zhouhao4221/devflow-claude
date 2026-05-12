---
description: 上报测试失败项 - 将失败场景创建为 Gitea issue
argument-hint: "[module]"
allowed-tools: Read, Glob, Bash(git remote:*, command:*, tea:*, curl:*, gh:*)
model: claude-haiku-4-5-20251001
---

# 上报测试 Bug

将最近一次测试的失败场景上报为 Gitea issue。

## 命令格式

```
/qa:bug [module]
```

---

## 执行流程

### 1. 读取配置

从 `settings.local.json` 读取：
- `branchStrategy.repoType`：仓库类型（github / gitea）
- `branchStrategy.giteaUrl`：Gitea 地址（gitea 时必填）
- `branchStrategy.giteaToken`：Gitea token（gitea 时必填）

### 2. 找到最新报告

扫描 `docs/qa/reports/` 找最新报告文件，提取所有 `❌ FAIL` 场景。

若无失败项：
```
✅ 最近一次测试全部通过，无需上报
```

若无报告文件：
```
❌ 未找到测试报告，请先执行 /qa:run
```

### 3. 展示失败列表并询问

```
📋 发现 2 个失败场景：

  1. S02 密码错误提示
     失败原因：表单未显示错误信息

  2. S05 退出登录后跳转
     失败原因：未跳转到登录页，停留在当前页

是否上报到 Gitea？(y/n/选择编号如 1,2)
```

用户可选择全部上报、部分上报或取消。

### 4. 上报 issue

**前置检查**（gitea 仓库）：
- `giteaUrl` 和 `giteaToken` 非空，否则提示：
  ```
  ❌ 未配置 giteaUrl / giteaToken
  💡 在 settings.local.json 中配置后重试
  ```

**CLI 优先**（与 req 插件保持一致）：
- GitHub：`gh issue create`
- Gitea：优先 `tea issue create`，不可用时回退 `curl + giteaToken`

**issue 内容**：
```
标题：[QA] <模块名> - S0N <场景名称>

正文：
## 测试场景
- 模块：<module>
- 场景：S0N <场景名称>
- 测试日期：YYYY-MM-DD

## 失败步骤
<失败步骤描述>

## 预期结果
<预期断言>

## 实际结果
<失败原因>

## 截图
<截图路径（如有）>

---
由 /qa:bug 自动生成
```

### 5. 输出结果

```
✅ 已创建 2 个 issue：

  #42 [QA] 用户登录 - S02 密码错误提示
  #43 [QA] 用户登录 - S05 退出登录后跳转

💡 /qa:run   修复后重新验证
```
