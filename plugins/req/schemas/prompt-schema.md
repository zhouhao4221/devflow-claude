# Prompt 文件期望结构
<!-- schema-version: 1.1 -->

> 插件命令运行时从项目 `docs/prompt/` 读取架构知识。
> 本文件定义各命令依赖的章节，供 `/req:update` 在插件更新后检查项目是否同步覆盖。
> 章节名不要求精确匹配标题文字，只需语义覆盖（标题或正文含关键词即可）。

---

## docs/prompt/architecture.md

**必需**（缺失时 `/req:dev` 降级为通用实现，质量明显下降）：

| 关键词 | 用途 | 依赖命令 |
|--------|------|---------|
| 技术栈 / 框架 / language | 生成代码时选择正确语言和库 | `/req:dev` |
| 分层 / 层级 / layer | 确定实现的层级顺序（controller→service→repo 等） | `/req:dev` |
| 目录 / 结构 / directory | 文件放置位置 | `/req:dev` |
| 命名 / 规范 / convention | 函数名、文件名、变量名风格 | `/req:dev` |

**推荐**（缺失时命令仍可运行，但生成结果可能与项目现有代码风格不一致）：

| 关键词 | 用途 | 依赖命令 |
|--------|------|---------|
| 测试 / test | 测试文件位置和规范 | `/req:dev`、`/req:test` |
| 接口 / API / endpoint | 接口层规范和请求格式 | `/req:dev` |
| 错误处理 / error | 统一错误返回结构 | `/req:dev` |

---

## docs/prompt/release.md

**可选文件**（缺失时 `/req:release` 使用插件默认行为，跳过项目特有检查和步骤）：

| 章节 | 用途 | 缺失时行为 |
|------|------|-----------|
| 版本号文件 | 版本号确定后需同步更新的文件及字段（package.json、plugin.json 等） | 跳过版本号文件更新 |
| 发版前检查 | 生成产物前必须通过的命令（测试、构建、lint） | 跳过，直接进入步骤 1 |
| 发版后步骤 | Release 创建成功后的提示事项（通知、部署） | 最终报告无发版后提示 |
| 额外附件 | 除 SQL 外需上传到 Release 的文件（glob） | 仅上传 SQL 资产 |

---

## docs/prompt/testing.md

**可选文件**（缺失时 `/req:test` 使用内置默认值，可能不匹配项目实际测试配置）：

| 关键词 | 用途 |
|--------|------|
| 运行命令 / run / exec | 执行测试的命令 |
| 文件位置 / 目录 / path | 测试文件存放路径 |
| 框架 / framework / library | 使用的测试框架 |

---

## Prompt 库（统一 5 节骨架）

以下文件由 `/req:init` 从 `templates/prompt-snippets/` 生成，遵循固定 5 节结构（什么时候用 / 必备输入 / 触发方式 / 优质输出标准 / 常见失败模式）。**均为可选文件**：存在则对应命令注入，缺失时命令降级为通用行为（不报错，仅 `/req:update` 校验时提示推荐补齐）。

> 校验规则：文件存在时检查 5 节是否齐全（语义匹配标题即可）；缺节为**警告**，不阻塞。文件整体缺失为**推荐**项，不报错。

| 文件 | 内容 | 消费命令 |
|------|------|---------|
| `code-generation.md` | 代码生成规范 | `/req:dev` |
| `refactoring.md` | 重构规范（行为不变） | `/req:do` |
| `test-generation.md` | 测试用例生成规范 | `/req:test_new` |
| `error-diagnosis.md` | 错误根因分析规范 | `/req:fix` |
| `pr-review.md` | PR 评审关注点 | `/req:review-pr` |
| `requirement-structuring.md` | 模糊需求结构化规范 | `/req:new`、`/req:edit` |
| `prompt-craft.md` | Prompt 文件自身的格式规范（不被命令读取，供团队维护参考） | — |

**5 节关键词**（每节语义命中标题或正文即视为存在）：

| 节 | 关键词 |
|----|--------|
| 什么时候用 | 什么时候 / 适用 / 场景 / when |
| 必备输入 | 必备 / 输入 / 准备 / input |
| 触发方式 | 触发 / 使用 / trigger |
| 优质输出标准 | 输出 / 标准 / output |
| 常见失败模式 | 失败 / 问题 / 误区 / failure |
