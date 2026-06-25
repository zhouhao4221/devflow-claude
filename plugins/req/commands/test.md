---
description: 需求测试 - 综合测试验证（回归 + 新建 + 交互验证）
argument-hint: "[REQ-XXX]"
allowed-tools: Read, Write, Edit, Glob, Grep, Bash
---

> **重要**：测试文件位置、运行命令、环境启动均从项目 `docs/prompt/testing.md` 读取，不内置任何项目细节。文件不存在时打印创建提示（非阻塞），回退到 `docs/prompt/architecture.md` 的「测试规范」章节。

# 需求测试

针对指定需求执行综合测试：运行已有测试 → 引导创建新测试 → 交互验证测试要点。

> 存储和缓存同步见 [`_storage.md`](./_storage.md)

## 命令格式

```
/req:test [REQ-XXX] [选项]
```

省略编号时自动选择「开发中/测试中」的需求，多个候选让用户选择。

| 选项 | 说明 |
|-----|------|
| `--failed` | 仅运行上次失败的测试 |
| `--skip-ut` / `--skip-api` / `--skip-e2e` | 跳过对应阶段 |
| `--force` | 某阶段失败时继续后续 |

---

## 总体流程

1. 选择需求 & 前置检查（状态必须为「开发中/测试中」，功能未完成时警告）
2. 提取测试要点（业务维度，分 API/业务规则/数据权限/其他）
3. 识别变更范围（优先需求文档「文件改动清单」，否则 `git diff`，按 testing.md 定位测试文件）
4. **阶段一：UT** — 回归运行变更相关已有 UT → 缺失时引导 `/req:test_new --type=ut`
5. **阶段二：API 测试** — 按 testing.md 启动环境 → 回归已有 → 缺失时引导 `/req:test_new --type=api`
6. **阶段三：E2E 测试** — 额外检查前端服务 → 回归已有 → 缺失时引导 `/req:test_new --type=e2e`
7. **交互验证** — 自动化未覆盖的测试要点逐项引导手动验证
8. 更新状态为「测试中」、记录结果、同步全局缓存
9. 汇总报告（各阶段通过/失败、测试要点覆盖率）

全部通过 → 提示 `/req:done`。存在失败 → 列出失败用例和原因，提示 `/req:dev` 修复或 `--failed` 重跑。

---

## 测试模式

| 模式 | 命令 |
|------|------|
| 综合测试（默认） | `/req:test REQ-XXX` |
| 增量测试 | `/req:test REQ-XXX --failed` |
| 跳过阶段 | `--skip-ut` / `--skip-api` / `--skip-e2e` |
| 强制继续 | `--force` |

---

## 用户输入

$ARGUMENTS
