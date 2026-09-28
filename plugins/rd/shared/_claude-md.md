# 公共逻辑参考 - CLAUDE.md 架构检查

> 此文档定义命令对项目 CLAUDE.md「项目架构」章节的依赖检查规则。
>
> 同伴文档（同目录，按需 Read；此处不用链接，避免把整组共享文件拖进上下文）：`_storage.md`、`_branch.md`、`_issue.md`、`_template.md`、`_granularity.md`。

## CLAUDE.md 架构检查

### 为什么需要

插件不硬编码任何项目架构细节（如分层顺序、目录结构、命名规范）。这些信息由项目自己的 CLAUDE.md 提供。dev-guide、test-guide 等 skill 读取 CLAUDE.md 后适配引导。

### 项目指令文件：CLAUDE.md 或 AGENTS.md

本插件各处说的「CLAUDE.md」指项目根的**项目指令文件**：有 `CLAUDE.md` 用它；没有而有 `AGENTS.md` 时用 `AGENTS.md`（Claude Code 2.1.277 起此时改读 AGENTS.md 作为项目上下文）。

**只有 AGENTS.md 的项目，禁止新建 CLAUDE.md**——一旦存在 CLAUDE.md，Claude Code 就不再读 AGENTS.md，项目原有指引整体失效。检查与追加（架构片段、指针行）都作用于 AGENTS.md；两者都没有时才新建 CLAUDE.md。

### 检查时机

以下命令执行前检查项目是否提供了架构信息：

| 命令 | 依赖的架构信息 | 缺失时影响 |
|------|--------------|-----------|
| `/rd:dev` | 分层架构、目录结构 | 无法生成准确的实现方案和文件清单 |
| `/rd:test`、`/rd:test_new` | 测试规范、测试目录 | 无法定位测试文件和生成测试代码 |
| `/rd:new`（后端/全栈类型） | API 风格 | 无法生成准确的接口需求章节 |

### 检查规则

```python
# 项目根目录；无 CLAUDE.md 时回落 AGENTS.md
claude_md_path = "CLAUDE.md" if os.path.exists("CLAUDE.md") else "AGENTS.md"
architecture_keywords = [
    "分层架构", "目录结构", "技术栈", "项目架构",
    "Architecture", "Tech Stack", "Project Structure"
]

# /rd:init 把架构写进 docs/prompt/architecture.md，指令文件只留一行指针
if os.path.exists("docs/prompt/architecture.md"):
    has_architecture = True
elif os.path.exists(claude_md_path):  # 兼容旧项目：架构直接写在指令文件里
    content = read_file(claude_md_path)
    has_architecture = any(kw in content for kw in architecture_keywords)
else:
    has_architecture = False
```

### 缺失时的提醒（非阻断，仅警告）

```
⚠️ 未检测到项目架构描述（docs/prompt/architecture.md 与 CLAUDE.md 均无）

   /rd:dev 需要架构信息来生成实现方案（分层顺序、目录结构、开发规范）
   /rd:test 需要测试规范来定位测试文件和生成测试代码

   添加方式：
   - /rd:init <project> --reinit  扫描项目生成 docs/prompt/architecture.md

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
