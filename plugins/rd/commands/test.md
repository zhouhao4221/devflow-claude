---
description: 需求测试 - 综合测试验证（回归 + 新建 + 自主验收）
argument-hint: "[REQ-XXX|QUICK-XXX]"
allowed-tools: Read, Write, Edit, Glob, Grep, Bash, Agent
---

> **重要**：测试文件位置、运行命令、环境启动均从项目 `docs/prompt/testing.md` 读取，不内置任何项目细节。文件不存在时打印创建提示（非阻塞），回退到 `docs/prompt/architecture.md` 的「测试规范」章节。

# 需求测试

针对指定需求执行综合测试：运行已有测试 → 引导创建新测试 → 自主验收测试要点。

> 存储路径规则见 [`_storage.md`](../shared/_storage.md)

## 命令格式

```
/rd:test [REQ-XXX|QUICK-XXX] [选项]
```

省略编号时自动选择「开发中/测试中」的需求，多个候选让用户选择。

| 选项 | 说明 |
|-----|------|
| `--failed` | 仅运行上次失败的测试 |
| `--skip-ut` / `--skip-api` / `--skip-e2e` | 跳过对应阶段 |
| `--force` | 某阶段失败时继续后续 |

---

## 总体流程

1. 选择需求 & 前置检查（REQ / QUICK 通用：状态必须为「开发中/测试中」；REQ 功能清单未完成时警告）
2. 提取验证清单——按类型取章节：REQ「六、测试要点」，QUICK「验证方式」（见 `_storage.md`「双轨状态机」）；REQ 按 API/业务规则/数据权限/其他分维度
3. 识别变更范围（优先需求文档「文件改动清单」，否则 `git diff`，按 testing.md 定位测试文件）
4. **阶段一：UT** — 回归运行变更相关已有 UT（委派 `test-runner`）→ 缺失时引导 `/rd:test_new --type=ut`
5. **阶段二：API 测试** — 按 testing.md 启动环境 → 回归已有（委派 `test-runner`）→ 缺失时引导 `/rd:test_new --type=api`
6. **阶段三：E2E 测试** — 额外检查前端服务 → 回归已有（委派 `test-runner`）→ 缺失时引导 `/rd:test_new --type=e2e`
7. **自主验收** — 阶段一~三未覆盖的验证项按 [`_verify.md`](../shared/_verify.md)「自主验收」分类：`script` / `visual` 并行派 `ui-verifier`（headless 探针，截图不进主会话），`manual` 逐项引导用户手动验证。前端未起时先按 testing.md 启动（同阶段三，`--skip-e2e` 不影响本步）；前置不满足时全部退回逐项手动引导，报告写「自主验收：未配置（原因）」。回写按 `_verify.md`：PASS 勾选并附探针路径；FAIL、BLOCKED 保持未勾；manual 通过则勾选，用户明确暂缓才加「（待观察：原因）」或「（未实测：原因）」；readonly 仓库不写回，只在报告中列出
8. 更新状态为「测试中」并勾选生命周期；旧模板的存量 QUICK 若没有「测试中」复选框，在「开发中」之后插入该行再勾选（守卫要求状态与最后已勾格一致）；记录结果
9. 汇总报告（各阶段通过/失败、自主验收 n/m（FAIL n，BLOCKED n）、测试要点覆盖率）

全部通过 → 提示 `/rd:done`。存在失败（含自主验收 FAIL）→ 列出失败用例和原因，提示 `/rd:dev` 修复或 `--failed` 重跑。

---

## 回归阶段的执行方式

阶段一~三的「回归运行已有测试」一律委派给 `test-runner` subagent 执行，主会话只接收摘要，测试日志不进入主会话；规则见 [`_delegate.md`](../shared/_delegate.md)。

- 环境检查/启动（阶段二、三）仍由主会话完成，subagent 只跑测试命令
- prompt 自包含：工作目录、testing.md 中的运行命令（已拼好 `--failed`/模块过滤）、本阶段要跑的测试文件清单、`--failed` 模式下的上次失败清单
- 同一阶段内测试命令可按文件/模块拆分且数量 > 1 时，一次并行派多个
- subagent 回传 ERROR（依赖缺失、命令不存在、编译失败）时按原因处理或询问用户，不要改命令绕过
- 汇总报告的失败用例直接取自各 subagent 返回，不再重跑
- `<E2E 目录>/acceptance/` 下的自主验收探针属于阶段三回归范围，下次运行一并跑

---

## 测试模式

| 模式 | 命令 |
|------|------|
| 综合测试（默认） | `/rd:test REQ-XXX` |
| 增量测试 | `/rd:test REQ-XXX --failed` |
| 跳过阶段 | `--skip-ut` / `--skip-api` / `--skip-e2e` |
| 强制继续 | `--force` |

---

## 用户输入

$ARGUMENTS
