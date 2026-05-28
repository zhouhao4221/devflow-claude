# 跨平台重构方案

> DevFlow 插件跨平台适配（Claude Code / OpenCode / Codex）架构方案，记录最终决策和技术路线。

---

## 1. 背景

DevFlow 现有架构深度绑定 Claude Code 生态（marketplace + hooks + skills），导致 OpenCode 和 Codex 用户无法直接使用。目标是让 80 个 SKILL.md 和 82 个命令可以在三平台上运行，同时保持 skill 内容仅维护一份。

---

## 2. 最终架构方案

### 2.1 整体架构图

```
                          ┌─────────────────────┐
                          │   devflow-skills     │  ← 独立仓库，平台无关
                          │  (80 个 SKILL.md)     │
                          │  GitHub: zhouhao4221/ │
                          │  devflow-skills       │
                          └──────────┬──────────┘
                                     │ 构建时复制 (cp -r)
                                     ▼
┌────────────────────────────────────────────────────────────┐
│                      devflow-claude                         │  ← 平台专属仓库
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │                     plugins/                          │  │
│  │  ┌────────────┬────────────┬──────────┬──────────┐   │  │
│  │  │    req/    │    pm/     │   api/   │  diag/   │   │  │
│  │  ├────────────┼────────────┼──────────┼──────────┤   │  │
│  │  │ commands/  │ commands/  │commands/ │commands/ │   │  │
│  │  │ hooks/     │ hooks/     │ hooks/   │ hooks/   │   │  │
│  │  │ scripts/   │ scripts/   │ scripts/ │ scripts/ │   │  │
│  │  │ templates/ │            │          │templates/│   │  │
│  │  │ skills/  ←─┼────────────┼──────────┼──────────┤   │  │
│  │  │ (构建产物)  │ (构建产物)  │ (构建产物) │ (构建产物) │   │  │
│  │  └────────────┴────────────┴──────────┴──────────┘   │  │
│  │                                                         │
│  │  ┌──────────────────────────────────────────────────┐  │  │
│  │  │                  specs/                           │  │  │
│  │  │  ┌──────────────┬──────────────┬──────────────┐  │  │  │
│  │  │  │ commands/    │   hooks/     │  plugins/    │  │  │  │
│  │  │  │ (82 个 yaml) │ (yaml)       │ (yaml)       │  │  │  │
│  │  │  └──────────────┴──────────────┴──────────────┘  │  │  │
│  │  │  ❌ 无 skills/ spec（skill 天然平台无关）          │  │  │
│  │  └──────────────────────────────────────────────────┘  │  │
│  │                                                         │
│  │  ┌──────────────────────────────────────────────────┐  │  │
│  │  │                 adaptors/                         │  │  │
│  │  │  ┌──────────┬───────────┬──────────┐            │  │  │
│  │  │  │ claude/  │ opencode/ │  codex/  │            │  │  │
│  │  │  │ build.py │ build.py  │ build.py │            │  │  │
│  │  │  └──────────┴───────────┴──────────┘            │  │  │
│  │  │  功能: 生成 plugin.json + hooks.json +            │  │  │
│  │  │  复制 skills（cp -r devflow-skills/ → plugins/）  │  │  │
│  │  └──────────────────────────────────────────────────┘  │  │
│  └──────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────┘
```

**数据流**：`devflow-skills/`（唯一源码）→ adaptor 构建步骤 `cp -r` → 各 plugin `skills/`（构建产物，gitignore）。

### 2.2 仓库划分

| 仓库 | 定位 | 内容 | URL |
|------|------|------|-----|
| `devflow-skills` | 平台无关技能库 | 80 个 SKILL.md（零修改） + `_common.md` | https://github.com/zhouhao4221/devflow-skills |
| `devflow-claude` | 平台专属仓库 | commands / hooks / scripts / templates / specs / adaptors | https://github.com/zhouhao4221/devflow-claude |

### 2.3 Skills 目录结构

```
devflow-skills/
├── README.md
└── skills/
    ├── req/          # 需求管理（46 个技能）
    │   ├── req/SKILL.md
    │   ├── new/SKILL.md
    │   ├── dev/SKILL.md
    │   └── ...
    ├── pm/           # 项目管理（14 个技能）
    │   ├── pm/SKILL.md
    │   ├── weekly/SKILL.md
    │   └── ...
    ├── api/          # API 对接（8 个技能）
    │   ├── api/SKILL.md
    │   ├── gen/SKILL.md
    │   └── ...
    ├── diag/         # 生产诊断（5 个技能）
    │   ├── diag/SKILL.md
    │   └── ...
    └── uat/          # UI 验收测试（7 个技能）
        ├── uat/SKILL.md
        └── ...
```

### 2.4 构建时复制策略

Claude Code 的 plugin 系统禁止引用外部目录（`plugin.json` 的 `skills` 字段不能使用 `../` 路径），因此采用构建时复制方案：

```
adaptor build 步骤:
  1. 读取 specs/ → 生成 plugin.json + hooks.json
  2. cp -r devflow-skills/skills/* → plugins/{plugin}/skills/
  3. plugins/{plugin}/skills/ 加入 .gitignore，不提交到 repo
```

**为什么不选 symlink**：marketplace 安装时会 dereference 外部 symlink（复制内容），效果等同于构建复制但不可预测。显式 build 步骤更可控。

### 2.5 Skill 格式

每个技能是一个目录，包含 `SKILL.md`，使用简单的 YAML frontmatter：

```yaml
---
name: skill-name
description: 技能描述
---
```

规格约束：
- 仅 `name` + `description` 两个字段，三平台格式完全兼容
- 命令与技能的绑定关系通过自然语言描述（CLAUDE.md / 命令正文 / SKILL.md description），无需声明式映射
- 如需增强可靠性，可选在 devflow-skills 包中加入 `skill-bindings.json` 做声明式映射供 CI 校验——非必须

---

## 3. 核心决策

### 3.1 已确认的决策

| # | 决策点 | 结论 | 理由 |
|---|--------|------|------|
| 1 | skill 独立包 | ✅ `devflow-skills` 独立仓库 | 80 个 SKILL.md 天然平台无关，零修改可用 |
| 2 | Claude plugin 引用方式 | ✅ 构建时复制（非 symlink） | Claude Code plugin 不支持引用外部目录；构建复制是唯一可靠方案 |
| 3 | `specs/skills/*.yaml` | ❌ 砍掉，不编写 | skill 不需要 spec 抽象层，省掉 72 个 yaml + 30% adaptor 代码 |
| 4 | adaptor 技能生成逻辑 | ❌ 砍掉，改为 `cp -r` 一行命令 | 文件复制即可完成，不需要复杂转换逻辑 |
| 5 | 是否"两边写代码" | 否 | 源头只有 `devflow-skills/` 一份，plugin 下的 `skills/` 是构建产物（gitignore） |
| 6 | 交付分期 | 一期命令+技能（覆盖 90%），二期 Hook 替代方案 | Hook 平台差异大，先交付核心功能 |
| 7 | 兼容性红线 | Claude Code 构建产物 diff 一致，Phase 1 不通不进入 Phase 2 | 确保 Claude 用户的现有体验不退化 |
| 8 | 插件优先级 | req → pm → api → uat → diag | 按使用频次和覆盖面排序 |

### 3.2 风险与缓解

| 风险 | 严重度 | 缓解方案 |
|------|--------|----------|
| skill 包与 plugin 包版本不一致 | 🟡 中 | plugin 用 git submodule 锁定 skill 包 commit；CI 加 `name` 一致性校验 |
| 自然语言耦合无硬约束 | 🟡 中 | 可选 `skill-bindings.json` 声明式映射 + CI 校验 |
| 多仓库维护 | 🟡 中 | skill 包变更频率极低；发版联动场景少 |

---

## 4. 工期与排期

| 阶段 | 内容 | 工期 | 说明 |
|------|------|------|------|
| **Phase 0** | 创建 devflow-skills 独立包 | 1 天 | ✅ 已完成。迁移 80 个 SKILL.md，创建独立仓库，可先行发布 |
| **Phase 1** | Spec 基础架构 + Claude Adapter | 3-4 天 | 省掉 72 个 skill spec 编写（原 5-6 天 → 3-4 天）。commands + hooks + plugins spec 编写 + Claude adaptor 实现（含构建时复制逻辑） |
| **Phase 2** | OpenCode + Codex Adapter | 5 天 | OpenCode 适配（3 天） + Codex 适配（2 天）。adaptor 简化为命令+hooks 两块 |
| **Phase 3** | 插件跨平台适配（req → pm → api → uat → diag） | 7 天 | 按优先级逐批适配 |
| **Phase 4** | CI/CD 构建脚本 + 安装文档 | 4 天 | 构建流水线 + 一键安装脚本 + 用户文档 |
| **总计** | | **16-17 天** | 较原方案（19-20 天）节省 3 天 |

### 4.1 验收标准

| 平台 | 验收指标 |
|------|----------|
| Claude Code | 构建产物与当前 plugin diff 一致（排除 skills 目录变更）；所有命令可用 |
| OpenCode | 所有命令可用；skills 注入正常；hooks 行为一致 |
| Codex | 所有命令可用；skills 注入正常 |

---

## 5. 变更记录

| 日期 | 版本 | 变更内容 |
|------|------|----------|
| 2026-05-28 | v1.0 | 初始版本：skill 独立方案、构建时复制策略、最终架构图、工期调整 |

---

## 6. 相关文档

- [devflow-skills](https://github.com/zhouhao4221/devflow-skills) - 独立技能库
- [devflow-claude](https://github.com/zhouhao4221/devflow-claude) - Claude Code 专属插件仓库
- [Token 使用与节约指南](./token-optimization.md)
- [需求分析方法论](./requirement-analysis-methodology.md)
