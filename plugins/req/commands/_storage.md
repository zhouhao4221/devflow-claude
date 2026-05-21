# 公共逻辑参考 - 存储与配置

> 此文档定义 settings 文件写入、存储路径、缓存同步、需求编号、元信息等共用规则。
>
> 同伴文档：[`_branch.md`](./_branch.md)（分支策略）、[`_issue.md`](./_issue.md)（Issue 关联）、[`_template.md`](./_template.md)（模板与状态确认）、[`_granularity.md`](./_granularity.md)（需求粒度）、[`_claude-md.md`](./_claude-md.md)（架构检查）。

## settings 文件写入规范

插件配置分两个文件存储，按是否含密钥区分：

| 字段 | 文件 | 纳入 git | 说明 |
|------|------|----------|------|
| `requirementProject` | `settings.json` | ✅ | 团队共享配置 |
| `requirementRole` | `settings.json` | ✅ | 团队共享配置 |
| `branchStrategy`（不含 token） | `settings.json` | ✅ | 团队共享配置 |
| `giteaToken` | `settings.local.json` | ❌ | 个人密钥，禁止提交 |

**写入规则（强制）**：

1. **禁止独立配置文件**：禁止创建 `.claude/devflow.json`、`branchStrategy.json` 等独立文件，独立文件不会被 Claude Code 识别
2. **合并写入**：先读取已有文件内容，合并需要更新的字段后写回，**不得覆盖已有字段**
3. **目录检查**：`.claude/` 目录不存在时先创建
4. **读取合并顺序**：命令读配置时先读 `settings.json`，再用 `settings.local.json` 覆盖同名字段（`giteaToken` 以 local 为准）
5. **无写入权限的回退**：当 Write/Edit 工具被拒绝时，**不得**改写到其他文件，而应直接输出可复制执行的 shell 命令：

   ```bash
   # 写入 settings.json（团队配置）
   python3 -c "import json,os; p='.claude/settings.json'; os.makedirs('.claude',exist_ok=True); d=json.load(open(p)) if os.path.exists(p) else {}; d['requirementProject']='my-project'; d['requirementRole']='primary'; json.dump(d,open(p,'w'),indent=2,ensure_ascii=False)"
   # 写入 settings.local.json（本地密钥）
   python3 -c "import json,os; p='.claude/settings.local.json'; os.makedirs('.claude',exist_ok=True); d=json.load(open(p)) if os.path.exists(p) else {}; d['giteaToken']='YOUR_TOKEN'; json.dump(d,open(p,'w'),indent=2,ensure_ascii=False)"
   ```

```python
# 写入团队配置（settings.json）
import json, os

path = ".claude/settings.json"
os.makedirs(".claude", exist_ok=True)
existing = json.load(open(path)) if os.path.exists(path) else {}
existing["requirementProject"] = "..."  # 只更新需要的字段
with open(path, "w") as f:
    json.dump(existing, f, indent=2, ensure_ascii=False)

# 写入本地密钥（settings.local.json）
path = ".claude/settings.local.json"
existing = json.load(open(path)) if os.path.exists(path) else {}
existing["giteaToken"] = "YOUR_TOKEN"
with open(path, "w") as f:
    json.dump(existing, f, indent=2, ensure_ascii=False)
```

### 读取惯例（兼容旧项目）

命令读取 `requirementProject` / `requirementRole` / `branchStrategy` 时，统一按以下顺序合并：

```
config = merge(settings.json, settings.local.json)
# settings.local.json 中的同名字段覆盖 settings.json
```

**兼容旧项目**：旧项目若将所有字段写在 `settings.local.json`（未拆分），读取时仍能正常工作，无需迁移。只有在显式重新运行 `/req:init --reinit` 或 `/req:branch init` 后才会迁移到新布局。

---

## 存储路径解析

```
本地存储（主）: docs/requirements/
modules/      # 模块文档
specs/        # 规范文档（数据类型、接口契约等，跨仓库共享）
active/       # 进行中需求
completed/    # 已完成需求
INDEX.md      # 索引

全局缓存（副）: ~/.claude-requirements/projects/<project>/
```

**解析规则**：
1. 先读 `.claude/settings.json` 的 `requirementProject` 和 `requirementRole`，再用 `.claude/settings.local.json` 中同名字段覆盖
2. 有值 → 使用全局缓存路径
3. 无值 → 使用本地 `docs/requirements/`

**仓库角色**（`requirementRole` 字段）：

| 角色 | 值 | 说明 |
|------|------|------|
| 主仓库 | `primary` | 拥有本地 `docs/requirements/`，可读写，修改后自动同步到缓存 |
| 只读仓库 | `readonly` | 无本地存储，仅从缓存读取需求，不可创建/编辑/变更状态 |

**读取策略**：
- `primary`：优先本地 → 本地不存在时从缓存读取
- `readonly`：直接从缓存读取

## 缓存同步规则（强制自动，无需确认）

**核心原则**：需求文档修改后**强制自动同步**到全局缓存，无需用户确认。

| 操作 | 本地 | 缓存同步 |
|-----|------|---------|
| 创建需求 | 写入 active/ | **强制**复制到缓存 active/ |
| 编辑需求 | 更新文件 | **强制**复制到缓存覆盖 |
| 状态变更 | 更新文件 | **强制**复制到缓存覆盖 |
| 完成归档 | 移动到 completed/ | **强制**缓存同步移动 |

**强制同步机制**：

通过 PostToolUse Hook **自动强制触发**，仅当命令涉及需求文档修改时触发缓存同步：

触发同步的命令：
- `/req:new` - 创建需求文档
- `/req:new-quick` - 创建快速修复文档
- `/req:edit` - 编辑需求文档
- `/req:review` - 更新评审状态
- `/req:dev` - 更新开发状态和进度
- `/req:test` - 更新测试状态和结果
- `/req:done` - 完成归档
- `/req:upgrade` - 升级 QUICK 为 REQ
- `/req:modules new` - 创建模块文档
- `/req:prd-edit` - 编辑 PRD 文档
- `/req:specs new` - 创建规范文档
- `/req:specs edit` - 编辑规范文档

不触发同步的命令（只读操作）：`/req`、`/req:status`、`/req:show`、`/req:specs`（列表/show）、`/req:projects`、`/req:cache`、`/req:use`、`/req:init`、`/req:migrate`、`/req:test_regression`、`/req:test_new`、`/req:prd`、`/req:changelog`、`/req:commit`、`/req:fix`、`/req:do`、`/req:review-pr`

同步配置：
- Hook 脚本：`scripts/sync-cache.sh`
- 触发条件：**Write 或 Edit 工具**操作 `docs/requirements/` 目录下的文件后
- 同步范围：REQ-XXX、QUICK-XXX 需求文档、模块文档（modules/）、规范文档（specs/）及 PRD.md，不含 INDEX.md、template.md
- **执行方式**：静默自动执行，仅输出同步状态提示

**重要原则**：
1. **强制同步**：缓存同步是强制行为，不可跳过，不需要用户确认
2. **本地优先**：所有修改需求的命令（new、edit、review、dev、test、done）都必须先更新本地 `docs/requirements/` 中的文档
3. **本地成功后立即同步**：本地操作成功后**立即自动**同步到全局缓存
4. **只读仓库禁止写操作**：`requirementRole=readonly` 的仓库不执行创建、编辑、状态更新、缓存同步等写操作，仅允许读取和查看
5. **以本地为准**：同步时直接用本地版本覆盖缓存，不进行冲突检测

## 需求编号生成

扫描 active/ 和 completed/ 目录，找最大编号 +1，格式 `REQ-XXX`

## 元信息字段

| 字段 | 说明 |
|------|------|
| 编号 | REQ-XXX |
| 类型 | 后端/前端/全栈 |
| 状态 | 当前状态 |
| 模块 | 所属模块 |
| 关联需求 | 前后端对应需求 |
| branch | 开发分支名（/req:dev 首次进入时生成） |
| issue | 关联的 Git 平台 issue 编号（如 `#123`），无关联为 `-`。`/req:new --from-issue` 自动填充，`/req:done` 读取后可选关闭 |
