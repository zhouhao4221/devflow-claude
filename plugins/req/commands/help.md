---
description: 已更名为 rd - 查看迁移步骤
model: claude-haiku-4-5-20251001
---

# req 已更名为 rd

原样输出以下内容，不读取任何文件、不执行任何命令：

```
req 插件已更名为 rd（R&D 研发）：命令前缀 /req:xxx → /rd:xxx，命令名与功能不变。
本插件只是过渡提示，原 /req:* 命令已全部移到 rd。

迁移三步：
  1. claude plugins uninstall req@devflow
  2. claude plugins install rd@devflow
  3. 在已有项目里执行 /rd:migrate —— 把 CLAUDE.md、docs/prompt/ 等处残留的 /req: 引用逐项替换为 /rd:

无需改动：.devflow/ 配置、需求文档（REQ-XXX）、.claude/.req-* 本地开关。
入口命令 /req 现在是 /rd:req。
```
