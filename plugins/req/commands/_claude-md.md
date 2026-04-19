# 公共逻辑参考 - CLAUDE.md 架构检查

> 此文档定义命令对项目 CLAUDE.md「项目架构」章节的依赖检查规则。
>
> 同伴文档：[`_storage.md`](./_storage.md)、[`_branch.md`](./_branch.md)、[`_issue.md`](./_issue.md)、[`_template.md`](./_template.md)、[`_granularity.md`](./_granularity.md)。

## CLAUDE.md 架构检查

### 为什么需要

插件不硬编码任何项目架构细节（如分层顺序、目录结构、命名规范）。这些信息由项目自己的 CLAUDE.md 提供。dev-guide、test-guide 等 skill 读取 CLAUDE.md 后适配引导。

### 检查时机

以下命令执行前检查 CLAUDE.md 是否包含架构信息：

| 命令 | 依赖的架构信息 | 缺失时影响 |
|------|--------------|-----------|
| `/req:dev` | 分层架构、目录结构 | 无法生成准确的实现方案和文件清单 |
| `/req:test`、`/req:test_new` | 测试规范、测试目录 | 无法定位测试文件和生成测试代码 |
| `/req:new`（后端/全栈类型） | API 风格 | 无法生成准确的接口需求章节 |

### 检查规则

```python
claude_md_path = "CLAUDE.md"  # 项目根目录
architecture_keywords = [
    "分层架构", "目录结构", "技术栈", "项目架构",
    "Architecture", "Tech Stack", "Project Structure"
]

if os.path.exists(claude_md_path):
    content = read_file(claude_md_path)
    has_architecture = any(kw in content for kw in architecture_keywords)
else:
    has_architecture = False
```

### 缺失时的提醒（非阻断，仅警告）

```
⚠️ CLAUDE.md 中未检测到项目架构描述

   /req:dev 需要架构信息来生成实现方案（分层顺序、目录结构、开发规范）
   /req:test 需要测试规范来定位测试文件和生成测试代码

   💡 添加方式：
   - /req:init <project> --reinit  交互式生成架构片段
   - 手动在 CLAUDE.md 中添加「项目架构」章节

   继续执行，但生成的方案可能不够准确。
```

### 架构片段模板

插件提供预置模板供用户选择（存放在 `templates/claude-md-snippets/`）：

| 模板 | 文件 | 适用场景 |
|------|------|---------|
| Go 后端 | `go-backend.md` | Gin + GORM 分层架构 |
| Java 后端 | `java-backend.md` | Spring Boot 分层架构 |
| 前端 React | `frontend-react.md` | React/Next.js + TypeScript |
| 通用 | `generic.md` | 空白模板，手动填写 |
