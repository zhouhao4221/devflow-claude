# Release 配置

> 本文件由 `/req:release` 在步骤 0 读取，注入项目特有的发版规则。
> 删除不需要的章节即可——所有章节均为可选，缺失时使用插件默认行为。

## 版本号文件

版本号确定后更新以下文件并暂存：

- `.claude-plugin/marketplace.json` → `metadata.version`（X.Y.Z 格式，去掉 v 前缀）
- 各 `plugins/*/plugin.json` → `version`（按该插件目录范围内的 commit 变更等级独立 bump：`feat` → minor，`fix/perf/refactor` → patch，其他类型 → 不变；详细规则见 `plugins/req/skills/version-bumper/SKILL.md`）

## 发版前检查

> 在生成任何产物（changelog、commit）之前必须通过的检查。
> 检查失败时硬停止，不继续执行后续步骤。

- 确认 `.claude-plugin/marketplace.json` 和各 `plugins/*/plugin.json` 无未提交的手动版本号修改（版本号由 `/req:release` 步骤 2.5 自动 bump，手动修改会与自动 bump 冲突）

## 发版后步骤

> Release 创建成功后执行（草稿模式下不执行，publish 后由人工触发）。
> 仅输出提示，不自动执行副作用操作（通知、部署等由人工确认）。

- 通知：发版后在 #releases 频道公告新版本

## 额外附件

无。
