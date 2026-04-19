# 公共逻辑参考 - 模板格式与状态确认

> 此文档定义状态更新确认机制、确认操作规范、状态流转、Memory 隔离规则、模板格式约束等共用规则。
>
> 同伴文档：[`_storage.md`](./_storage.md)（存储与配置）、[`_branch.md`](./_branch.md)、[`_issue.md`](./_issue.md)、[`_granularity.md`](./_granularity.md)、[`_claude-md.md`](./_claude-md.md)。

## 状态更新确认机制

不同命令对状态更新的确认要求：

| 命令 | 状态变更 | 确认机制 |
|-----|---------|---------|
| `/req:review pass/reject` | 待评审 → 评审通过/驳回 | 显式参数即为确认 |
| `/req:dev` | 评审通过 → 开发中 | 首次进入时自动更新 |
| `/req:test` | 开发中 → 测试中 | 测试完成后自动更新 |
| `/req:done` | 测试中 → 已完成 | **必须明确确认（y/n）** |

## 确认操作规范

默认**不弹任何原生确认对话框**——命令已通过多轮讨论 / 显式参数 / y/n 完成意图确认，Claude Code 本身也足够稳定，无需再叠加一层打断。用户可按需通过自然语言开启 Bash 侧拦截，**无需手动编辑任何配置文件**。

### 开启/关闭拦截（记忆 + marker 文件）

开关由项目内 `.claude/.req-confirm-commit` 标记文件承载。Claude 根据用户自然语言意图维护该文件并在 memory 中落 feedback：

| 用户说 | Claude 动作 |
|-------|-------------|
| "以后 git commit 前帮我确认" / "开启提交确认" / "commit 前弹一下" | `mkdir -p .claude && touch .claude/.req-confirm-commit`，保存/更新 feedback memory 记录偏好 |
| "不用确认了" / "关闭提交确认" / "别再弹框了" | `rm -f .claude/.req-confirm-commit`，更新 memory |

标记文件已加入 `.gitignore`（每台机器独立）。Claude 在新会话首次感知到偏好与 marker 状态不一致时，可按 memory 中的 feedback 自动补 `touch`，用户无需重复交代。

### Hook 原生确认（仅在 marker 存在时生效）

| 操作 | Hook 脚本 | 触发条件 |
|------|----------|---------|
| git commit | confirm-before-commit.sh | Bash 命令包含 git commit |
| 移动需求文件 | confirm-before-commit.sh | Bash 命令包含 mv ... REQ-/QUICK- |
| 删除需求文件 | confirm-before-commit.sh | Bash 命令包含 rm ... REQ-/QUICK- |

> `--auto` 模式标记（`.claude/.req-auto`）仍由 `/req:fix --auto` 等流程负责建立/清理；在 marker 启用拦截时它负责让 Hook 放行自动化流水线。

### 执行规则

1. **展示预览后直接执行** — 不输出"回车继续"等文本确认提示
2. **默认直通** — 任何 Write/Edit/Bash 都不走 Hook 原生对话框
3. **需要用户输入的场景仍需等待** — 选择章节编号、选择目标需求、描述修改意图等由命令层负责
4. **`/req:done` 等显式 y/n 场景** — 由命令层提示，不依赖 Hook

## 状态流转

```
📝 草稿 → 👀 待评审 → ✅ 评审通过 → 🔨 开发中 → 🧪 测试中 → 🎉 已完成
```

## Memory 隔离规则（强制）

涉及模板的命令和 skill **禁止受 auto-memory 影响**。模板化输出必须完全由模板结构和用户当前输入决定，不得因 memory 中的偏好、历史记录或反馈而改变文档结构、章节内容或格式。

**适用范围**：
- 命令：`/req:new`、`/req:new-quick`、`/req:edit`、`/req:upgrade`、`/req:prd-edit`
- skill：`requirement-analyzer`、`prd-analyzer`

**具体禁止行为**：
1. 不得根据 memory 中的偏好跳过或合并模板章节
2. 不得根据 memory 中的历史需求自动填充当前需求内容
3. 不得根据 memory 中的反馈调整模板格式（如章节顺序、表格列数）
4. 不得读取 `~/.claude/projects/*/memory/` 目录下的文件来辅助文档生成

**允许的行为**：memory 可影响**交互风格**（如提问的详略程度），但不得影响**文档产出物**。

---

## 模板格式约束（强制）

创建和编辑需求文档时，**必须严格遵循模板格式**：

### 模板读取优先级

| 需求类型 | 优先读取 | 回退读取 |
|---------|---------|---------|
| REQ-XXX | `docs/requirements/templates/requirement-template.md` | `<plugin-path>/templates/requirement-template.md` |
| QUICK-XXX | `docs/requirements/templates/quick-template.md` | `<plugin-path>/templates/quick-template.md` |
| PRD | `docs/requirements/templates/prd-template.md` | `<plugin-path>/templates/prd-template.md` |

**模板不存在时终止**：两个路径都不存在时，**必须终止操作**，提示用户执行 `/req:update-template` 恢复模板。不得在无模板的情况下创建或编辑文档。

### 格式规则

1. **章节结构不可变**：不得新增、删除、合并或重命名模板中的章节
2. **层级标题不可变**：章节标题、编号（一、二、三...）必须与模板完全一致
3. **表格格式不可变**：表格的列名、列数必须与模板一致
4. **保留空章节**：未涉及的章节保留模板占位文本，不得删除
5. **仅填充内容**：在模板对应章节的占位文本处填充实际内容

### 适用命令

- `/req:new` - 创建时严格按模板生成
- `/req:new-quick` - 创建时严格按快速模板生成
- `/req:edit` - 编辑时保持模板结构不变
- `/req:upgrade` - 转换时按目标模板结构生成

### 验证机制

`scripts/validate-requirement.sh` 在 Write/Edit 后自动验证：
- REQ-XXX：检查所有章节（元信息、生命周期、一~十）
- QUICK-XXX：检查简化模板的所有章节（元信息、生命周期、问题描述、实现方案、验证方式、开发记录）
