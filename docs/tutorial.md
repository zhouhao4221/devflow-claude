# 使用教程

🌐 [English](tutorial.en.md) | [中文](tutorial.md) | [한국어](tutorial.ko.md)

本教程以一个完整示例，演示从安装插件到完成需求的全流程。

> 示例场景：为一个后端项目开发「用户积分规则管理」功能。

---

## 一、安装与初始化

> **两步启动**：插件安装后，每次打开 Claude Code 会话时，若检测到当前仓库未初始化或未配置分支策略，会自动在会话开头输出引导提示。完成下面两步后提示自动消失：
>
> 1. `/rd:init <project-name>` — 初始化需求项目
> 2. `/rd:branch init` — 配置分支策略
>
> 之后即可用 `/rd:new` 创建第一个需求。

### 1.1 安装插件

```bash
# 1. 添加插件仓库为 marketplace
claude plugins marketplace add https://github.com/zhouhao4221/devflow-claude

# 2. 从 marketplace 安装插件
claude plugins install rd@devflow

# 验证安装
claude plugins list
```

### 1.2 初始化需求项目

在项目根目录启动 Claude Code，执行：

```
/rd:init my-saas
```

这会：
- 创建需求目录 `docs/requirements/`（active/、completed/、modules/、templates/；目录位置可用 `requirementsDir` 调整）
- 生成 PRD 文档模板 `docs/requirements/PRD.md`
- 在 `.devflow/settings.json` 中记录项目名、角色（`primary`）和需求目录（团队共享，纳入 git）

需求文档只在本仓库保存一份，写入即生效，没有缓存和同步。

### 1.3 CLAUDE.md 架构描述

初始化时会检查项目 CLAUDE.md 是否包含架构信息。如果缺失，引导你选择预置模板：

```
📋 选择项目类型，生成 CLAUDE.md 建议片段：

  1. Go 后端（Gin + GORM 分层架构）
  2. Java 后端（Spring Boot 分层架构）
  3. 前端项目（React/Vue + TypeScript）
  4. 自定义（生成空白模板，手动填写）
  5. 跳过
```

选择后会将架构片段追加到项目 CLAUDE.md，包含技术栈、分层架构表、开发规范、测试规范等。
`/rd:dev` 和 `/rd:test` 依赖这些信息来生成实现方案和定位测试文件。

> **后续修改**：直接编辑项目 CLAUDE.md 的「项目架构」章节即可。

### 1.4 配置分支策略（强烈推荐）

```
/rd:branch init
```

> 未配置时，会话启动引导会持续提示；配置完成后提示自动消失。不配置也能用，使用默认行为（硬编码 `feat/` / `fix/` 前缀、不自动创建 PR）。

选择团队的分支管理策略：
- **GitHub Flow**（推荐）：所有分支从 main 拉，合回 main
- **Git Flow**：功能分支从 develop 拉，合回 develop
- **Trunk-Based**：短期分支，主干开发

然后选择仓库托管类型：
- **GitHub**：`/rd:pr` 时提示 `gh pr create` 命令
- **Gitea**：`/rd:pr` 时自动调用 Gitea REST API 创建 PR
- **其他**：仅展示 `git merge` 合并命令

配置后 `/rd:dev`、`/rd:commit`、`/rd:done`、`/rd:pr` 会自动遵循策略。

### 1.5 重新初始化

已有项目补充缺失文件（不覆盖已有内容）：

```
/rd:init my-saas --reinit
```

用途：
- 插件更新后补充新增的模板文件
- 补充缺失的目录结构（如 modules/、templates/）
- 重新引导 CLAUDE.md 架构描述
- 恢复被误删的 PRD.md 或模块文档

### 1.6 升级迁移

#### v2 → v3：配置迁到 `.devflow/`

v3 起配置从 `.claude/settings*.json` 迁到 `.devflow/`，并移除了全局缓存 `~/.claude-requirements/`。老项目升级插件后执行：

```
/rd:migrate
```

- `requirementProject` / `requirementRole` / `requirementsDir` / `branchStrategy` 搬到 `.devflow/settings.json`，`giteaToken` 搬到 `.devflow/settings.local.json`
- Claude Code 自身的 hooks / permissions 仍留在 `.claude/settings.json`
- 只读仓库需重新绑定：`/rd:use <主仓路径>`
- 确认主仓需求文档完整后，可手动删除 `~/.claude-requirements/projects/<项目名>/`

> 会话启动时若检测到 DevFlow 配置仍在 `.claude/`，会提示执行迁移。

#### req → rd（v4）：插件更名

v4 起 req 插件更名为 rd（R&D 研发），命令前缀 `/req:` 改为 `/rd:`，命令名与功能不变。已安装旧插件的项目按三步迁移：

```
claude plugins uninstall req@devflow
claude plugins install rd@devflow
/rd:migrate
```

- `/rd:migrate` 会列出本项目 `CLAUDE.md`、`docs/prompt/`、需求模板、`.claude/skills/` 中残留的旧前缀引用，逐处确认后替换
- 无需改动：`.devflow/` 配置、需求文档（`REQ-XXX`）、`.claude/.req-*` 本地开关
- 项目级 `.claude/settings.json` 的 `enabledPlugins` 若写了 `"req@devflow": true`，需改为 `rd@devflow`（`/rd:migrate` 会检测并在确认后替换，改完请提交），否则拉代码的成员仍启用旧插件
- 旧的 PR 审查命令已并入 `/rd:pr`：`review-pr review` → `/rd:review`，`review-pr merge` → `/rd:pr merge`，`review-pr fetch-comments` → `/rd:pr comments`，单独的 `review-pr` → `/rd:pr status`
- 注意：`/rd:pr` 不带参数是**创建 PR**（旧的 `review-pr` 不带参数是查看状态）
- 审查类命令已按模型档位拆分：需求评审 `/rd:review` → `/rd:req-review`（提审时增加 AI 预审）；AI 代码审查 `/rd:pr review` → `/rd:review`；`/rd:pr comments` 改为只读查看，按评论改代码用 `/rd:review comments`。`/rd:migrate` 会一并替换旧写法

> 旧插件 req 已从 marketplace 移除；若更新后 `/req:*` 命令全部消失，按上面三步改装 rd 即可。

### 1.7 同步模板（可选）

如果插件更新了模板，可以同步最新版：

```
/rd:update-template
```

### 1.8 配置 Gitea Token（Gitea 仓库必须）

如果 `/rd:branch init` 选择了 Gitea 仓库类型，需要配置 API Token 才能自动创建 PR。

**获取 Token：**

1. 登录 Gitea → 右上角头像 → **设置**
2. 左侧菜单 → **应用**
3. 「管理 Access Token」→ 输入令牌名称（如 `claude-pr`）
4. 选择权限范围：

| 权限类别 | 权限项 | 必须 | 说明 |
|---------|-------|------|------|
| issue | 读写 | ✅ | PR 本质是 issue 的扩展，创建/查询 PR 需要 |
| repository | 读写 | ✅ | 读取仓库信息、分支列表、推送代码 |
| user | 读取 | 可选 | 用于验证 Token 有效性 |

5. 点击 **生成令牌** → 复制保存（只显示一次）

**配置 Token：**

`/rd:branch init` 已把 `repoType`、`giteaUrl` 等策略字段写进 `.devflow/settings.json` 的 `branchStrategy`。Token 单独写在项目的 `.devflow/settings.local.json` **顶层**（不在 `branchStrategy` 里）：

```json
{
  "giteaToken": "your-token-here"
}
```

> **安全提示**：`.devflow/settings.local.json` 不应提交到 Git，确认已加入 `.gitignore`。

**验证 Token：**

```bash
curl -s -H "Authorization: token your-token-here" \
  https://your-gitea.com/api/v1/user
```

返回用户信息表示配置成功。

---

## 二、创建需求

### 2.1 正式需求（REQ）

```
/rd:new 用户积分规则管理 --type=后端
```

AI 会引导你逐章完善需求文档：

| 章节 | 内容 | 你需要做什么 |
|------|------|------------|
| 一、需求描述 | 背景、目标、客户场景、价值 | 描述业务背景，AI 帮你结构化 |
| 二、功能清单 | 可勾选的功能点列表 | 确认功能范围 |
| 三、业务规则 | 校验规则、状态转换、权限 | 补充业务细节 |
| 四、使用场景 | 角色、流程、异常处理 | 描述典型操作流程 |
| 五、接口需求 | 接口能力、输入输出、业务语义 | 确认接口需求 |
| 六、测试要点 | 需要验证的场景 | 补充测试关注点 |

完成后生成 `docs/requirements/active/REQ-001-用户积分规则管理.md`。

### 2.2 快速修复（QUICK）

适合小 bug 或小功能，流程更轻量：

```
/rd:new-quick 修复积分计算精度丢失
```

QUICK 模板更简洁：问题描述 → 实现方案 → 验证方式。生命周期只跳过评审：方案确认后 `/rd:dev` → `/rd:test`（按「验证方式」逐项验证）→ `/rd:done`，与正式需求走同一组命令。

### 2.3 需求拆分建议

不确定粒度是否合适？用拆分分析：

```
/rd:split 用户积分系统
```

AI 会分析粒度并建议拆分方案（只读，不创建文档）。

### 2.4 从 Git issue 创建需求

如果团队使用 Gitea / GitHub issue 作为需求入口，可以直接从 issue 创建需求文档，省去二次录入：

```
/rd:new --from-issue=#12           # 正式需求
/rd:new-quick --from-issue=#5      # 快速修复
/rd:do --from-issue=#42            # 无文档，仅把 issue 内容作为描述跑智能开发
```

**AI 的行为**：
1. 按 `branchStrategy.repoType` 调用对应 API 拉取 issue（Gitea → REST API + `giteaToken`；GitHub → `gh issue view`）
2. issue 标题作为需求默认标题，正文作为「问题与现状」的初始输入
3. 创建的文档元信息 `issue` 字段记录 `#N`，用于后续自动关联

**Gitea 仓库的前提**：`branchStrategy.giteaUrl` 和 `giteaToken` 必须配置（见 1.8）。AI **不会**从 git remote SSH 地址猜测 HTTPS URL，必须走配置。

#### issue 与分支/提交的自动关联

有 issue 关联时，整条链路都会自动带上 issue 编号：

| 环节 | 表现 |
|------|------|
| `/rd:dev` 创建分支 | 末尾自动追加 `-iN`（如 `feat/REQ-001-user-points-i12`） |
| `/rd:commit` 提交代码 | commit message 末尾自动追加 `closes #N`（PR 合并时 Git 平台自动关闭 issue） |
| `/rd:done` 归档 | 询问是否通过 API 直接关闭 issue |
| `/rd:do --from-issue` | 创建带 `-iN` 的分支；完成时询问关闭 issue |

**读取优先级**：需求文档 `issue` 字段 > 分支名 `-iN` 后缀。这样即使是无文档的 `/rd:do`，commit 和 done 也能从分支名推断 issue 编号。

---

## 三、评审流程

> QUICK 跳过评审，可直接进入开发。

### 3.1 提交评审

```
/rd:req-review
```

状态从「草稿」变为「待评审」。

### 3.2 评审决议

```
/rd:req-review pass     # 通过，进入「评审通过」
/rd:req-review reject   # 驳回，回到「草稿」
```

驳回后需要 `/rd:edit` 修改再重新提审。

---

## 四、开发阶段

### 4.1 启动开发

```
/rd:dev
```

执行流程：

```
前置检查（REQ 必须通过评审）
    ↓
分支管理（自动创建 feat/REQ-001-user-points-rule）
    ↓
读取 CLAUDE.md 项目架构（分层顺序、目录结构）
    ↓
加载需求上下文（章节一~六）
    ↓
生成实现方案（Plan Mode）
    ├── 10.1 数据模型
    ├── 10.2 API 设计（基于接口需求 + 项目代码生成）
    ├── 10.3 文件改动清单（按 CLAUDE.md 分层架构列出）
    └── 10.4 实现步骤（按 CLAUDE.md 分层顺序拆解）
    ↓
确认方案 → 状态改为「开发中」
    ↓
按 CLAUDE.md 分层架构逐步实现
```

### 4.2 分支管理

首次执行 `/rd:dev` 时，AI 自动：

1. 检查工作区是否干净（有未提交改动会终止）
2. 读取分支策略配置（如已配置 `/rd:branch init`）
3. 从需求标题生成英文分支名，供你确认：
   ```
   将创建开发分支：feat/REQ-001-user-points-rule
   基于分支：main（来源：branchStrategy.branchFrom）
   ```
4. 确认后创建分支并写入需求文档的 `branch` 字段

再次执行 `/rd:dev` 时，直接切换到已记录的分支。

分支命名规则（前缀可通过策略配置自定义）：
- REQ → `feat/REQ-XXX-<english-slug>[-iN]`
- QUICK → `fix/QUICK-XXX-<english-slug>[-iN]`
- `/rd:do --from-issue` → `<prefix><slug>-iN`（前缀由 AI 分析意图决定）
- 紧急修复 → `hotfix/<english-slug>`（通过 `/rd:branch hotfix` 创建）
- `-iN`：可选的 issue 后缀（如 `-i12`），当需求关联了 Git 平台 issue 时自动追加，用于后续命令识别关联（详见 2.8）

### 4.2.1 分支策略命令

```
/rd:branch              # 查看当前策略和分支状态
/rd:branch init         # 交互式配置分支策略 + 仓库类型
/rd:branch status       # 查看策略配置和各需求分支状态
/rd:branch hotfix 描述  # 从主分支创建紧急修复分支
```

### 4.2.2 创建 PR

开发完成后，创建 PR：

```
/rd:pr              # 根据当前分支自动匹配需求，创建 PR
/rd:pr REQ-001      # 指定需求创建 PR
```

根据 `/rd:branch init` 配置的仓库类型：
- **Gitea**：自动调用 Gitea REST API 创建 PR（需配置 `giteaToken`，见 1.8）
- **GitHub**：调用 `gh` CLI 创建 PR
- **其他**：推送分支到远程，展示合并命令

Git Flow 的 hotfix 分支会自动创建两个 PR（→ main + → develop）。

### 4.2.3 PR 审查与合并

PR 创建后，使用 AI 代码审查和合并：

```
/rd:pr status       # 查看 PR 状态
/rd:review          # AI 代码审查
/rd:pr comments     # 拉取 PR 评论（只读）
/rd:review comments # 按评论改代码
/rd:pr merge        # 合并 PR
```

**审查流程：**
1. AI 获取 PR diff，逐文件审查（正确性、安全性、规范、需求匹配）
2. 问题分三级：🔴 阻塞（必须修复）、🟡 建议、🔵 信息
3. 审查报告自动提交为 PR 评论（Gitea/GitHub 网页可见）
4. 无阻塞问题 → 可执行 merge

**合并方式：** 读取 `branchStrategy.mergeMethod` 配置（默认 `merge`），支持 `merge` / `squash` / `rebase`。

### 4.2.4 智能开发（/rd:do）

对于优化、重构、升级等无需创建需求文档的任务，使用智能开发命令：

```
/rd:do 优化订单查询性能
/rd:do 重构用户服务层
/rd:do 升级 Go 到 1.23
/rd:do 统一错误码格式
```

AI 自动：
1. **分析意图** — 判断类型（优化/重构/升级/规范/小功能/修复）和规模
2. **搜索代码** — 定位相关文件，生成修改方案
3. **确认方案** — 用户确认后创建分支（`improve/`、`feat/`、`fix/` 按类型自动选择）
4. **执行修改** — 按方案修改代码

规模较大时会建议切换到 `/rd:new-quick` 或 `/rd:new`。

**与 `/rd:fix` 的区别：**
- `/rd:fix` — 专门修 bug，AI 会做根因分析
- `/rd:do` — 优化/重构/升级等非 bug 场景，AI 分析意图后选择合适流程

### 4.3 继续开发

中断后再次进入，会恢复进度：

```
/rd:dev REQ-001
```

加 `--reset` 可以重新生成实现方案：

```
/rd:dev REQ-001 --reset
```

### 4.4 规范提交

开发过程中使用规范提交，自动关联需求编号：

```
/rd:commit
```

AI 分析改动内容，生成 Conventional Commits 格式的提交信息：

```
新功能: 实现积分规则 CRUD 接口 (REQ-001)
```

---

## 五、测试阶段

### 5.1 综合测试

```
/rd:test
```

包含回归测试 + 新功能测试，状态改为「测试中」。

### 5.2 分步测试

```
/rd:test_regression    # 运行已有自动化测试，生成回归报告
/rd:test_new           # 为新功能创建测试用例（UT/API/E2E）
```

---

## 六、完成归档

```
/rd:done
```

流程：
1. 检查测试完成情况
2. 展示完成摘要（功能点、测试点、文件统计、时间线）
3. 确认后归档：`active/REQ-001-*.md` → `completed/`
4. 更新 PRD 索引
5. 提醒合并开发分支

---

## 七、查看与管理

### 7.1 需求列表

```
/rd:req                          # 列出所有需求
/rd:req --type=后端              # 按类型筛选
/rd:req --module=用户            # 按模块筛选
/rd:req --type=前端 --module=用户 # 组合筛选
```

### 7.2 查看详情

```
/rd:show REQ-001     # 查看需求完整内容（只读）
/rd:status REQ-001   # 查看状态和进度
```

### 7.3 编辑需求

```
/rd:edit REQ-001     # 修改已有需求
```

---

## 八、模块管理

模块是按功能域划分的业务文档，帮助 AI 理解上下文。

```
/rd:modules                  # 列出所有模块
/rd:modules new 用户         # 创建用户模块文档
/rd:modules show 用户        # 查看模块详情
```

模块文档描述：职责边界、核心功能、数据模型、API 概览、关键文件路径。

---

## 九、PRD 管理

PRD 是项目级的产品需求文档，一个项目一份。

```
/rd:prd                      # 查看 PRD 状态概览，分析各章节填充情况
/rd:prd-edit                 # 编辑 PRD，AI 辅助补充内容
/rd:prd-edit 产品概述         # 编辑指定章节
```

PRD 的「需求追踪」章节会自动维护：
- `/rd:new` 时追加记录
- `/rd:done` 时更新状态和完成日期

---

## 十、版本管理

### 10.1 生成版本说明

```
/rd:changelog v1.2.0                          # 自动检测范围
/rd:changelog v1.2.0 --from=v1.1.0 --to=HEAD # 指定范围
```

AI 根据 Git 提交记录分类生成结构化 Changelog。

### 10.2 快速修复升级

QUICK 做到一半发现范围变大，可以升级为正式需求：

```
/rd:upgrade QUICK-003
```

---

## 十一、跨仓库协作

适用于前后端分仓的项目。

### 主仓库（后端）

```
# 初始化项目
/rd:init my-saas

# 正常创建和管理需求
/rd:new 用户积分-后端 --type=后端
```

### 关联仓库（前端）

```
# 绑定到主仓库（传主仓库根目录的本机路径）
/rd:use ../backend

# 可以查看需求（只读）
/rd:req
/rd:show REQ-001

# 可以基于需求开发（直读主仓需求目录）
/rd:dev REQ-002
```

关联仓库的角色为 `readonly`，主仓路径记录在 `.devflow/settings.local.json` 的 `requirementSource.path`（本机路径，不入 git）：
- 可以查看和读取需求
- 可以基于已完成需求开发
- 不能创建、编辑、变更需求状态

### 11.1 规范文档共享

主仓库可创建规范文档（数据类型定义、接口契约、错误码等），只读仓库可实时查阅：

**主仓库（后端）：**

```
/rd:specs new 订单数据类型        # 创建规范文档
/rd:specs edit order-types       # 编辑
/rd:specs                        # 列出所有规范
```

**只读仓库（前端）：**

```
/rd:specs                        # 查看规范列表
/rd:specs show order-types       # 查看订单数据类型定义
```

规范文档存储在主仓库的 `docs/requirements/specs/`，只读仓库直接读取主仓目录，无需同步。后端修改后，前端下次查看即为最新版本。

典型用途：
- 后端定义数据类型 → 前端查阅字段定义
- 统一错误码规范 → 前后端各自实现
- 接口契约约定 → 保证前后端一致

---

## 十二、完整流程图

```
                    创建需求
                /rd:new 标题
                      │
                      ▼
               ┌─────────────┐
               │   📝 草稿    │ ← /rd:edit 修改
               └──────┬──────┘
                      │ /rd:req-review
                      ▼
               ┌─────────────┐
               │  👀 待评审   │
               └──────┬──────┘
                      │ /rd:req-review pass
                      ▼
               ┌─────────────┐
               │ ✅ 评审通过  │
               └──────┬──────┘
                      │ /rd:dev（自动创建分支）
                      ▼
               ┌─────────────┐
               │  🔨 开发中   │ ← /rd:commit 提交代码
               │             │ ← /rd:pr 创建 PR
               │             │ ← /rd:review 审查
               │             │ ← /rd:pr merge 合并
               └──────┬──────┘
                      │ /rd:test
                      ▼
               ┌─────────────┐
               │  🧪 测试中   │
               └──────┬──────┘
                      │ /rd:done（提醒合并分支）
                      ▼
               ┌─────────────┐
               │  🎉 已完成   │ → archived to completed/
               └─────────────┘
```

---

## 十三、自然语言与一键模式

### 13.1 自然语言指令

无需记忆斜杠命令，直接用中文描述意图，插件会自动映射到对应命令。

**需求文档**

```
新增需求 用户积分管理          → /rd:new 用户积分管理
新建后端需求，做订单导出        → /rd:new 订单导出 --type=后端
修改025需求，增加导出功能      → /rd:edit REQ-025
```

**修复与开发（无文档）**

```
修个登录超时的 bug            → /rd:fix 登录超时
修 #42 这个 bug               → /rd:fix --from-issue=#42
优化订单查询性能              → /rd:do 优化订单查询性能
重构用户服务层                → /rd:do 重构用户服务层
升级 Go 到 1.23               → /rd:do 升级 Go 到 1.23
快速改一下分页默认值          → /rd:new-quick 分页默认值
```

**状态流转**（必须带编号）

```
开始开发025                   → /rd:dev REQ-025
025 开始测试                  → /rd:test REQ-025
025 评审通过 / 通过评审 025    → /rd:req-review pass
025 评审驳回                  → /rd:req-review reject
完成025 / 025 做完了           → /rd:done REQ-025
```

**版本与 PR**

```
规范提交                      → /rd:commit
创建 PR / 提 PR                → /rd:pr
审查 PR / review PR           → /rd:review
拉 PR 评论                    → /rd:pr comments
按评论改代码                  → /rd:review comments
合并 PR                       → /rd:pr merge
```

**直接粘贴 Git 平台 URL**（自动识别 issue / PR）

```
修复 owner/repo/issues/169    → /rd:fix --from-issue=#169
创建需求 owner/repo/issues/12  → /rd:new --from-issue=#12
审查 owner/repo/pulls/158     → /rd:review（需先切到 PR 对应分支）
```

单独粘贴 URL（不带动词）时，会展示选项让你选操作。

**编号解析规则**

| 输入 | 解析结果 |
|------|---------|
| `REQ-025` / `REQ025` | REQ-025 |
| `QUICK-003` / `QUICK003` | QUICK-003 |
| 纯数字 `025` / `25` | REQ-025（补零到 3 位） |
| `#42` / `issue 42` | `--from-issue=#42` |

**不会触发的情况**

- 查询 / 展示类："看一下025" 走 `/rd:show`
- 讨论 / 提问："这个 bug 怎么修"、"是不是该重构了"、"怎么新增需求"
- 关键词缺失必要信息："修改需求"无编号、"优化一下"无对象、"完成"无编号
- 已用斜杠命令开头（`/rd:`、`/pm:`、`/api:`）
- URL 指向其他仓库（与 `git remote` 不匹配）

### 13.2 一键修复（`--auto`）

`/rd:fix --auto` 跳过所有确认交互，自动串联 commit → push → PR。

> **前置说明**：rd 插件的确认默认就是**全部直通**。只有曾用自然语言告诉 Claude"开启提交确认"（由 Claude 创建 `.claude/.req-confirm-commit` marker 并写入 memory feedback）的用户，才会看到 `git commit` / `mv` / `rm` REQ 的原生确认弹框；对这部分用户，`--auto` 通过 `.claude/.req-auto` marker 让 Hook 放行。**默认设置下 `--auto` 仍有价值**——它会一并跳过命令层面的文本交互（方案确认、类型选择、issue 关闭询问等）并自动串联后续步骤。

**触发方式**

```
/rd:fix 登录超时 --auto                    # 显式
修下 Excel 导出中文乱码，不用确认            # 自然语言
一键修复登录超时                            # 自然语言
直接修 Excel 导出乱码并发 PR                # 自然语言
自动修 #42                                  # 自然语言 + issue
```

自然语言触发词：`一键修` / `自动修` / `修完直接发 PR` / `改完自动提交` / `不用确认` / `别问我` / `自动来` / `跑完再说`。

**会自动跳过的确认**

| 确认点 | 跳过方式 |
|-------|---------|
| 修复方案确认 | 命令内置跳过 |
| `git commit` 前的原生确认弹框 | 默认不存在；若通过自然语言开启（`.claude/.req-confirm-commit` marker），则由 `.claude/.req-auto` marker 让 Hook 放行 |
| `/rd:commit` 的类型交互式选择 | AI 自动推断为「修复」 |
| `--from-issue` 时的关闭 issue 询问 | 默认关闭 |
| `/rd:pr` 创建后的分支清理询问 | 默认保留 |
| 手工串联 commit → push → PR | 自动执行 |

**无法跳过**（Claude Code harness 层，需本地权限设置）

- 首次调用 Bash / Write / Edit 的工具权限确认
- Plan Mode approval（若开启 Plan Mode）

**不会跳过**（安全红线）

- 保护分支（`main` / `master` / `develop`）上的提交 —— 必须先切到开发分支
- AI 对代码的实际分析与修改（核心执行，非确认）

**底层机制**

`--auto` 启动时创建 `.claude/.req-auto` 标记文件（mtime 10 分钟 TTL）。默认状态（无 `.claude/.req-confirm-commit` marker）下本就没有原生确认弹框，`.req-auto` 不影响行为；当用户曾让 Claude 开启提交确认（创建了 `.req-confirm-commit` marker）时，`confirm-before-commit.sh` 检测到有效 `.req-auto` 标记直接放行 `git commit` 弹框。流程结束时清理标记；异常退出时 TTL 自动失效，避免残留长期放行。

`.claude/.req-auto` 已加入 `.gitignore`，不会入库。

**典型工作流**

```
用户：修下 Excel 导出中文乱码，不用确认
   ↓
AI：🧠 识别：/rd:fix Excel 导出中文乱码 --auto
    ⚙️ --auto 会自动跳过：[能力边界清单]
    🔒 无法跳过：[Claude Code harness 权限]
    🛑 不会跳过：[保护分支、实际代码修改]
    开始执行？
   ↓
定位问题 → 修改代码 → git commit → git push → 创建 PR
```

### 13.3 其他支持 `--auto` 的命令

**`/rd:review --auto`** — 跳过"是否上传评审评论"的询问

默认情况下（不带 `--auto`），AI 代码审查完成后会展示**精简版评论预览**并询问 `y/n`，避免审查结果直接对外发布。传入 `--auto` 跳过询问，直接上传。

```
/rd:review                 # 展示预览 → 等待 y/n 确认
/rd:review --auto          # 直接上传精简版评论
```

自然语言触发：`一键审查`、`自动审查`、`审查并提交`、`审完直接评论`、`别问我`。

> **只影响 `/rd:review` 的上传询问**。`/rd:pr merge` 的合并后分支清理询问由 `branchStrategy.deleteBranchAfterMerge` 控制；`/rd:review comments` 的"是否应用修改"询问保留，避免 AI 误改代码。

---

## 常用命令速查

| 场景 | 命令 |
|------|------|
| 看看有哪些需求 | `/rd:req` |
| 创建正式需求 | `/rd:new 标题 --type=后端` |
| 创建小修复（有文档） | `/rd:new-quick 标题` |
| 轻量修复（无文档） | `/rd:fix 问题描述` |
| 智能开发（优化/重构） | `/rd:do 描述` |
| 编辑需求 | `/rd:edit` |
| 提交评审 | `/rd:req-review` |
| 通过评审 | `/rd:req-review pass` |
| 启动开发 | `/rd:dev` |
| 提交代码 | `/rd:commit` |
| 创建 PR | `/rd:pr` |
| 查看 PR 状态 | `/rd:pr status` |
| AI 代码审查 | `/rd:review` |
| 查看 PR 评论 | `/rd:pr comments` |
| 按评论改代码 | `/rd:review comments` |
| 合并 PR | `/rd:pr merge` |
| 运行测试 | `/rd:test` |
| 完成归档 | `/rd:done` |
| 查看 PRD | `/rd:prd` |
| 生成 Changelog | `/rd:changelog v1.0.0` |
| 配置分支策略 | `/rd:branch init` |
| 查看分支状态 | `/rd:branch status` |
| 紧急修复 | `/rd:branch hotfix 描述` |
| 重新初始化 | `/rd:init my-project --reinit` |
| 升级迁移（v2→v3、req→rd） | `/rd:migrate` |
| 查看规范文档 | `/rd:specs show <名称>` |
| 创建规范文档 | `/rd:specs new <名称>` |
