---
description: 执行 QA 测试 - 按流程文档逐场景验收
argument-hint: "[module]"
allowed-tools: Read, Write, Edit, Glob, Bash(mkdir:*)
---

# 执行 QA 测试

读取测试流程文档，调用 qa-executor skill 逐场景执行，输出报告。

> **运行环境要求**：操作方式为 `browser` 时，必须在 **Codex Chrome** 或 **Claude 桌面客户端** 中运行，否则无法调用浏览器工具。

## 命令格式

```
/qa:run [module]
```

- 省略模块名：列出所有 flow 文档，提示用户选择
- 指定模块名：直接执行对应 flow 文档

---

## 执行流程

### 1. 确定执行范围

- 有参数 → 查找 `docs/qa/flows/<module>.md`
- 无参数 → 列出所有 flow 文档，用户选择（支持"全部"）

若 flow 文件不存在：
```
❌ 未找到测试流程文档：docs/qa/flows/<module>.md
💡 使用 /qa:new <module> 创建
```

### 2. 激活 qa-executor skill

读取 flow 文档后，按 `plugins/qa/skills/qa-executor/SKILL.md` 的指导执行：

- 检查运行环境（browser 模式下确认浏览器工具可用）
- 逐场景执行并记录结果

### 3. 写入报告

执行完毕后：
1. 创建 `docs/qa/screenshots/` 目录（如不存在）
2. 将报告写入 `docs/qa/reports/YYYY-MM-DD-<module>.md`
3. 更新 flow 文档元信息的 `最后执行` 字段

### 4. 输出汇总

在终端展示执行汇总（格式见 qa-executor skill），并提示：

```
📄 报告已保存：docs/qa/reports/YYYY-MM-DD-<module>.md

💡 /qa:report          查看完整报告
💡 /qa:bug             将失败项上报为 issue
```
