# 测试运行规范

> 本文件由 `/rd:test`、`/rd:test_regression` 读取，注入项目测试的运行细节。
> `/rd:test` 步骤 7、`/rd:do`、`/rd:fix` 的自主验收从「必备输入」取 E2E 命令 / 前端地址 / 登录配方；缺失时退回手动验证。
> 删除不需要的章节即可——缺失时命令使用内置默认值（可能不匹配实际配置）。

## 什么时候用

> 说明测试运行的适用范围。

<!--
示例：
- 回归测试、提交前验证、CI 前本地自查
-->

## 必备输入

> 运行测试所需的信息。

<!--
示例：
- 运行命令：`npm test` / `go test ./...` / `pytest`
- 测试文件位置与命名
- 依赖的环境变量 / 测试数据库 / 容器
- E2E 运行命令（headless）：`npx playwright test`
- 前端地址（baseURL）：`http://localhost:3000`
- 登录配方：登录页 `/login` → 填账号密码 → 点「登录」；账号取 `E2E_USER` / `E2E_PASSWORD` 环境变量（只写变量名，不写密钥）。变量要让 E2E 命令读得到：启动 Claude Code 前 export，或把 E2E 命令写成 `set -a && . ./.env.test && set +a && npx playwright test`（`.env.test` 加入 .gitignore）
- 产物目录：`test-results/acceptance/`（截图与 aria 快照，需在 .gitignore 中）
- 服务启动与探活：后端 `<启动命令>`、前端 `npm run dev`，就绪 URL `http://localhost:3000`
-->

## 触发方式

<!--
示例：
- `/rd:test_regression`
- `/rd:test REQ-XXX`
-->

## 优质输出标准

<!--
示例：
- 全部用例通过，无 skip 残留
- 失败时输出可定位的报错（文件 / 行 / 断言）
-->

## 常见失败模式

| 问题 | 原因 | 解决方案 |
|------|------|----------|
<!-- 示例：本地通过 CI 失败 | 环境变量缺失 | 必备输入列全环境依赖 -->
