---
description: 查看需求状态 - 详细状态和进度
argument-hint: "[REQ-XXX|QUICK-XXX]"
allowed-tools: Read, Glob, Grep, Bash(git:*)
model: claude-haiku-4-5-20251001
---

# 查看需求状态

查看需求的详细状态和进度信息。

## 命令格式

```
/rd:status [REQ-XXX|QUICK-XXX]
```

**说明**：编号可选，省略时自动选择最近活跃的需求。

---

## 执行流程

### 0. 自动识别需求

如果未提供 REQ-XXX 编号：

按修改时间排序扫描需求根目录的 `active/`（根目录解析见步骤 1）。无结果时提示创建；唯一时自动选中；多个时列表让用户输入序号选择。

### 1. 解析存储路径（按角色）

读取 `.devflow/settings.json` 的 `requirementRole` / `requirementsDir`（`.devflow/settings.local.json` 同名字段覆盖），确定需求根目录 `ROOT`：
- `readonly`：`<requirementSource.path>/<主仓 requirementsDir>`；未配置 `requirementSource` 时提示先 `/rd:use <primary-repo-path>` 绑定
- `primary` / 未配置角色：本仓 `requirementsDir`（缺省 `docs/requirements`）

`$ACTIVE` = `ROOT/active`，`$COMPLETED` = `ROOT/completed`。

### 2. 查找需求文档（按角色）

两种角色搜索顺序相同（无缓存，readonly 的 `ROOT` 即主仓目录）：
1. `$ACTIVE/<编号>-*.md`
2. `$COMPLETED/<编号>-*.md`

编号为 `REQ-XXX` 或 `QUICK-XXX`，两者同样处理。

如果未找到：
```
❌ 未找到需求：REQ-XXX

可用操作：
- 查看所有需求：/rd:req
- 创建新需求：/rd:new
```

### 3. 解析需求文档

提取关键信息：
- 元信息
- 生命周期状态
- 功能清单进度（REQ）
- 验证进度：REQ 读「六、测试要点」，QUICK 读「验证方式」（见 `_storage.md`「双轨状态机」）
- 文件改动清单（REQ）/ 涉及文件（QUICK）
- 变更记录（REQ）/ 开发记录（QUICK）

### 4. 输出详细状态

```

需求状态：REQ-001 部门渠道关联


元信息
编号：REQ-001
状态：开发中
优先级：P1
创建日期：2026-01-07
负责人：-
数据来源：本地 (primary)
项目：my-saas-product

生命周期
[x] 草稿         2026-01-07
[x] 待评审       2026-01-07
[x] ✅ 评审通过      2026-01-07
[>] 开发中       2026-01-08 ← 当前
[ ] 测试中
[ ] 已完成

功能清单（4/6 完成）
[x] 部门渠道关联
[x] 渠道范围校验
[x] 获取可选渠道接口
[x] 订单数据过滤
[ ] Dashboard数据过滤      ← 进行中
[ ] 缓存机制

测试要点（0/8 完成）
[ ] 部门创建时关联渠道
[ ] 部门更新时修改渠道关联
[ ] 上级部门未设置渠道，下级可任意选择
[ ] 上级部门已设置渠道，下级必须设置且为子集
[ ] 选择超出范围的渠道报错
[ ] 订单列表按渠道正确过滤
[ ] Dashboard 数据按渠道正确过滤
[ ] 缓存正确失效

文件改动（8/12 完成）
已完成：
internal/sys/model/sys_dept_channel_model.go ✅
internal/sys/store/sys_dept_channel_store.go ✅
internal/sys/biz/dept_channel.go ✅
internal/sys/biz/sys_dept.go ✅
internal/sys/controller/v1/sys_dept.go ✅
pkg/api/core/v1/sys_dept.go ✅
internal/sys/router.go ✅
internal/oms/store/sales_order_store.go ✅

待处理：
internal/oms/biz/sales_order_biz.go
internal/dashboard/store/sales_dashboard_store.go
internal/dashboard/biz/sales_dashboard_biz.go
docs/swagger/docs.go

变更记录
2026-01-07 初始版本

评审记录
2026-01-07 张三 通过 - 方案合理，可以开发



可用操作：
# primary 角色显示完整操作
- 继续开发：/rd:dev REQ-001
- 编辑需求：/rd:edit REQ-001
- 进入测试：/rd:test REQ-001

# readonly 角色仅显示只读操作
# - 查看需求列表：/rd:req
# - 查看模块：/rd:modules
```

---

## 简洁模式

使用 `--brief` 参数输出简洁信息：

```
/rd:status REQ-001 --brief
```

输出：
```
REQ-001 部门渠道关联
状态：开发中 | 功能：4/6 | 测试：0/8
```

QUICK 输出 `状态：开发中 | 验证：1/3`。

---

## 批量查看

查看所有活跃需求状态：

```
/rd:status --all
```

输出：
```
活跃需求状态一览

| 编号 | 标题 | 状态 | 功能进度 | 测试进度 |
|------|------|------|---------|---------|
| REQ-001 | 部门渠道关联 | 开发中 | 4/6 | 0/8 |
| REQ-002 | 用户积分系统 | 待评审 | - | - |
| REQ-003 | 订单导出优化 | 草稿 | - | - |
```

## 用户输入

$ARGUMENTS
