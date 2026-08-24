---
name: test_regression
description: 回归测试 - 运行已有自动化测试用例
---

> **重要**：本命令的测试文件位置、运行命令、代码示例均从项目 CLAUDE.md 的「测试规范」章节读取，不内置任何项目细节。

# 回归测试

运行项目中已存在的自动化测试用例，验证功能正确性。

> 存储路径和缓存同步规则见 _storage.md（见附录：_storage.md）

## 命令格式

```
/req:test_regression [选项]
```

### 选项

| 选项 | 说明 | 示例 |
|-----|------|------|
| `--all` | 全量回归（默认） | `/req:test_regression --all` |
| `--changed` | 仅测试变更相关 | `/req:test_regression --changed` |
| `--module=<name>` | 指定模块 | `/req:test_regression --module=user` |
| `--failed` | 仅运行上次失败的 | `/req:test_regression --failed` |
| `--type=<ut\|api\|e2e>` | 指定测试类型 | `/req:test_regression --type=ut` |
| `--verbose` | 显示详细输出 | `/req:test_regression --verbose` |
| `--coverage` | 生成覆盖率报告 | `/req:test_regression --coverage` |
| `--skip-env` | 跳过环境检查（仅 UT） | `/req:test_regression --type=ut --skip-env` |

---

## 测试环境要求

不同类型的测试需要不同的环境（具体服务和启动命令参考 CLAUDE.md）：

| 测试类型 | 依赖服务 | 后端服务 | 前端服务 |
|---------|---------|---------|---------|
| UT | 否 | 否 | 否 |
| API | 是 | 是 | 否 |
| E2E | 是 | 是 | 是 |

---

## 执行流程

### 0. 环境准备（API/E2E 需要）

如果测试类型包含 API 或 E2E，先检查并启动测试环境：

```
检查测试环境...

依赖服务状态：
<依赖服务 1>    ❌ 未启动
<依赖服务 2>    ❌ 未启动

按 CLAUDE.md 测试环境配置启动服务...
<CLAUDE.md中定义的测试环境启动命令>

等待服务就绪...
<依赖服务 1>  ✅ 就绪
<依赖服务 2>  ✅ 就绪

启动后端服务...
<CLAUDE.md中定义的后端启动命令>

等待后端服务...
<后端服务>  ✅ 就绪

启动前端服务（E2E 需要）...
<CLAUDE.md中定义的前端启动命令>

等待前端服务...
<前端服务>  ✅ 就绪

✅ 测试环境准备完成
```

### 1. 检测项目类型

从 CLAUDE.md 读取项目技术栈和测试框架配置：

```
检测项目类型...

项目类型：<CLAUDE.md中定义的技术栈>
测试框架：
单元测试：<CLAUDE.md中定义的UT框架>
API 测试：<CLAUDE.md中定义的API测试框架>
E2E 测试：<CLAUDE.md中定义的E2E框架>

测试目录：
<CLAUDE.md中定义的UT目录> (N 个文件)
<CLAUDE.md中定义的API测试目录> (N 个文件)
<CLAUDE.md中定义的E2E测试目录> (N 个文件)
```

### 2. 确定测试范围

根据选项确定要执行的测试：

#### 全量模式 (--all)
执行所有测试文件

#### 变更模式 (--changed)
```
检测变更文件...

变更文件：
<source-file-1>
<source-file-2>
<source-file-3>

关联测试：
<test-file-1>
<test-file-2>
<test-file-3>
```

#### 失败重试模式 (--failed)
从上次测试结果中读取失败用例

### 3. 执行测试

按类型依次执行：

```
执行回归测试...


单元测试 (<CLAUDE.md中的UT运行命令>)


<test-file-1>
<TestCase_1>           ✅ PASS
<TestCase_2>           ✅ PASS
<TestCase_3>           ✅ PASS
<TestCase_4>           ✅ PASS

<test-file-2>
<TestCase_5>           ✅ PASS
<TestCase_6>           ❌ FAIL
  Expected: <预期值>
  Actual:   <实际值>
<TestCase_7>           ✅ PASS

单元测试结果：N/N 通过


API 测试 (<CLAUDE.md中的API测试运行命令>)


<api-test-file-1>
<HTTP_METHOD> <endpoint-1>    ✅ PASS
<HTTP_METHOD> <endpoint-2>    ✅ PASS
<HTTP_METHOD> <endpoint-3>    ❌ FAIL
    Expected: 200
    Actual:   500 (Internal Server Error)

API 测试结果：N/N 通过
```

### 4. 生成测试报告

```

回归测试报告


测试时间：<timestamp>
测试范围：<全量回归 | 变更相关 | 失败重试>
总耗时：<duration>


类型     总数   通过   失败   通过率  

单元测试 N      N      N      XX.X%   
API 测试 N      N      N      XX.X%   
E2E 测试 N      N      N      XX.X%   

合计     N      N      N      XX.X%   


❌ 失败用例（N 个）：

1. <失败用例名>
   文件：<test-file>:<line>
   原因：<失败原因描述>

2. <失败用例名>
   文件：<test-file>:<line>
   原因：<失败原因描述>

下一步操作：
- 修复后重新测试：/req:test_regression --failed
- 查看失败详情：/req:test_regression --verbose
- 忽略失败继续：/req:test --force
```

### 5. 覆盖率报告（--coverage）

```
代码覆盖率报告


模块/目录                    覆盖率   状态     

<module-1>                  XX.X%    ✅ 达标   
<module-2>                  XX.X%    ⚠️ 接近   
<module-3>                  XX.X%    ❌ 不足   
<module-4>                  XX.X%    ✅ 达标   

总计                        XX.X%    <状态>    


目标覆盖率：<CLAUDE.md中定义的覆盖率目标>
建议补充测试：<覆盖率不足的模块>
```

---

## 测试框架配置

所有测试运行命令、目录结构、框架配置均从项目 CLAUDE.md 的「测试规范」章节读取，包括：

### 单元测试 (UT)

```bash
# 运行所有单元测试
<CLAUDE.md中的UT运行命令>

# 带覆盖率
<CLAUDE.md中的UT覆盖率命令>

# 指定模块
<CLAUDE.md中的UT运行命令> <module-path>

# 仅失败重试
<CLAUDE.md中的UT运行命令> <failed-test-filter>
```

### API 测试

```bash
# 前提：确保测试环境已启动（参考 CLAUDE.md 测试环境配置）

# 运行 API 测试
<CLAUDE.md中的API测试运行命令>

# 带详细输出
<CLAUDE.md中的API测试运行命令> --verbose

# 指定接口
<CLAUDE.md中的API测试运行命令> <test-filter>
```

### E2E 测试

```bash
# 前提：确保测试环境已启动（参考 CLAUDE.md 测试环境配置，包括前端服务）

# 运行所有 E2E 测试
<CLAUDE.md中的E2E运行命令>

# 带 UI 调试
<CLAUDE.md中的E2E运行命令> --ui

# 仅失败重试
<CLAUDE.md中的E2E运行命令> --last-failed

# 指定测试文件
<CLAUDE.md中的E2E运行命令> <test-file>
```

---

## 与 CI/CD 集成

回归测试结果可输出为 CI 友好格式：

```bash
/req:test_regression --ci --output=junit.xml
```

生成的报告可用于：
- GitHub Actions
- GitLab CI
- Jenkins

---

## 用户输入

$ARGUMENTS

---

# 附录（自动内联的共享约定）

> 以下内容由 command 引用的共享子文件自动内联，供不支持 slash 的 Claude 客户端离线阅读。请勿手动编辑本文件——改动应在对应 command 进行。

## 附录：_storage.md

# 公共逻辑参考 - 存储与配置

> 此文档定义 settings 文件写入、存储路径、缓存同步、需求编号、元信息等共用规则。
>
> 同伴文档（同目录，按需 Read；此处不用链接，避免生成器传递内联）：`_branch.md`（分支策略）、`_issue.md`（Issue 关联）、`_template.md`（模板与状态确认）、`_granularity.md`（需求粒度）、`_claude-md.md`（架构检查）。

## settings 文件写入规范

DevFlow 配置存储在项目根的 `.devflow/` 目录，按是否含密钥分两个文件：

| 字段 | 文件 | 纳入 git | 说明 |
|------|------|----------|------|
| `requirementProject` | `.devflow/settings.json` | ✅ | 团队共享配置 |
| `requirementRole` | `.devflow/settings.json` | ✅ | 团队共享配置 |
| `requirementsDir` | `.devflow/settings.json` | ✅ | 需求文档根目录，省略时默认 `docs/requirements` |
| `branchStrategy`（不含 token） | `.devflow/settings.json` | ✅ | 团队共享配置 |
| `giteaToken` | `.devflow/settings.local.json` | ❌ | 个人密钥，禁止提交 |

> **`.devflow/` 与 `.claude/` 的分工**：`.devflow/` 只放 DevFlow 业务配置（上表字段）；Claude Code 自身的 hooks、permissions 仍在 `.claude/settings.json`，两者互不迁移。项目级窄知识 skill 仍在 `.claude/skills/`。

**写入规则（强制）**：

1. **禁止独立配置文件**：DevFlow 字段一律合并进 `.devflow/settings.json` 或 `.devflow/settings.local.json`，禁止另建 `devflow.json`、`branchStrategy.json` 等
2. **合并写入**：先读取已有文件内容，合并需要更新的字段后写回，**不得覆盖已有字段**
3. **目录检查**：`.devflow/` 目录不存在时先创建
4. **读取合并顺序**：命令读配置时先读 `.devflow/settings.json`，再用 `.devflow/settings.local.json` 覆盖同名字段（`giteaToken` 以 local 为准）
5. **无写入权限的回退**：当 Write/Edit 工具被拒绝时，**不得**改写到其他文件，而应直接输出可复制执行的 shell 命令：

   ```bash
   # 写入 .devflow/settings.json（团队配置）
   python3 -c "import json,os; p='.devflow/settings.json'; os.makedirs('.devflow',exist_ok=True); d=json.load(open(p)) if os.path.exists(p) else {}; d['requirementProject']='my-project'; d['requirementRole']='primary'; json.dump(d,open(p,'w'),indent=2,ensure_ascii=False)"
   # 写入 .devflow/settings.local.json（本地密钥）
   python3 -c "import json,os; p='.devflow/settings.local.json'; os.makedirs('.devflow',exist_ok=True); d=json.load(open(p)) if os.path.exists(p) else {}; d['giteaToken']='YOUR_TOKEN'; json.dump(d,open(p,'w'),indent=2,ensure_ascii=False)"
   ```

```python
# 写入团队配置（.devflow/settings.json）
import json, os

path = ".devflow/settings.json"
os.makedirs(".devflow", exist_ok=True)
existing = json.load(open(path)) if os.path.exists(path) else {}
existing["requirementProject"] = "..."  # 只更新需要的字段
with open(path, "w") as f:
    json.dump(existing, f, indent=2, ensure_ascii=False)

# 写入本地密钥（.devflow/settings.local.json）
path = ".devflow/settings.local.json"
existing = json.load(open(path)) if os.path.exists(path) else {}
existing["giteaToken"] = "YOUR_TOKEN"
with open(path, "w") as f:
    json.dump(existing, f, indent=2, ensure_ascii=False)
```

### 读取惯例

命令读取 `requirementProject` / `requirementRole` / `requirementsDir` / `branchStrategy` 时，统一按以下顺序合并：

```
config = merge(.devflow/settings.json, .devflow/settings.local.json)
# .devflow/settings.local.json 中的同名字段覆盖 settings.json
```

**Legacy Claude 迁移（breaking change）**：v2.x 旧项目的 DevFlow 字段在 `.claude/settings.json(.local)`。**读取只认 `.devflow/`，不再回退 `.claude/`**——升级后未迁移的项目读不到配置。迁移方式（任选其一）：
- 运行 `scripts/migrate-config.sh`（搬运 DevFlow 字段到 `.devflow/`，密钥进 `settings.local.json`）
- 重新运行 `/req:init --reinit` 或 `/req:branch init`

> SessionStart hook 检测到 `.claude/` 存在 DevFlow 字段但 `.devflow/` 缺失时，会打印迁移提示。

---

## 存储路径解析

```
需求存储（唯一源，在 primary 仓库）: <requirementsDir>/   默认 docs/requirements/
modules/      # 模块文档
specs/        # 规范文档（数据类型、接口契约等，跨仓库共享）
active/       # 进行中需求
completed/    # 已完成需求
INDEX.md      # 索引
```

**无全局缓存**：需求文档只存在于 primary 仓库的 `requirementsDir`，是唯一事实源。readonly 仓库不复制、不缓存，直接读 primary 仓库目录。

**解析规则**：
1. 读 `.devflow/settings.json` 的 `requirementRole` / `requirementsDir` / `requirementSource`，再用 `.devflow/settings.local.json` 覆盖同名字段
2. `primary`：需求根目录 = 本仓 `requirementsDir`（省略时默认 `docs/requirements/`；下文 `docs/requirements/` 均指此解析结果）
3. `readonly`：需求根目录 = `requirementSource.path` 指向的主仓根 + 该主仓的 `requirementsDir`；未配置 `requirementSource` 时报错，提示先 `/req:use <primary-repo-path>` 绑定

**仓库角色**（`requirementRole` 字段）：

| 角色 | 值 | 说明 |
|------|------|------|
| 主仓库 | `primary` | 拥有本地 `requirementsDir`，可读写，写入即生效 |
| 只读仓库 | `readonly` | 无本地需求目录，经 `requirementSource.path` 直接读主仓，不可创建/编辑/变更状态 |

**读取策略**：
- `primary`：读写本仓 `requirementsDir`
- `readonly`：直接读 `requirementSource.path` 下的需求目录（实时，无副本）

## 写入规则（无缓存，主仓唯一源）

**核心原则**：需求文档**只有一份**，位于 primary 仓库的 `requirementsDir`。不存在缓存层，因此没有同步动作。

- **primary**：所有修改需求的命令（new、new-quick、edit、review、dev、test、done、upgrade、modules/specs/prd 编辑）直接写本仓 `requirementsDir`，写完即生效，**无任何后续同步或 cp**。
- **readonly**：禁止一切写操作（创建、编辑、状态更新）。仅读取 `requirementSource.path`。

> **历史说明（v2.x → v3 breaking change）**：v2.x 曾用 `~/.claude-requirements/` 全局缓存 + PostToolUse `sync-cache.sh` 单向同步，readonly 从缓存读。v3 起**移除缓存**：readonly 改为经 `requirementSource.path` 直读主仓，`sync-cache.sh` 不再注册。命令内**不应再有任何缓存读写、cp 到缓存、或全局索引（`~/.claude-requirements/index.json`）操作**。

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
