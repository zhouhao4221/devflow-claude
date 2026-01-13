---
description: 完成需求 - 标记完成并归档
---

# 完成需求

标记需求为已完成，归档文档。

## 命令格式

```
/req:done [REQ-XXX]
```

**说明**：编号可选，省略时自动识别当前测试中的需求。

---

## 执行流程

### 0. 自动识别需求

如果未提供 REQ-XXX 编号：

```python
# 查找状态为「测试中」的需求
candidates = find_requirements(status=["测试中"])

if len(candidates) == 0:
    print("❌ 没有可完成的需求")
    print("💡 请先完成测试：/req:test")
    exit()
elif len(candidates) == 1:
    REQ_ID = candidates[0]
    print(f"📌 自动选择：{REQ_ID}")
else:
    print("📋 发现多个测试中的需求，请选择：")
    for i, req in enumerate(candidates):
        print(f"  {i+1}. {req}")
```

### 1. 解析存储路径（本地优先 + 缓存同步）

```bash
# 本地存储路径（主存储）
LOCAL_ROOT=docs/requirements
LOCAL_ACTIVE=$LOCAL_ROOT/active
LOCAL_COMPLETED=$LOCAL_ROOT/completed

# 检查当前仓库绑定的项目（用于缓存同步）
PROJECT=$(cat .claude/settings.local.json 2>/dev/null | jq -r '.requirementProject // empty')

if [ -n "$PROJECT" ]; then
    CACHE_ROOT=~/.claude-requirements/projects/$PROJECT
    CACHE_ACTIVE=$CACHE_ROOT/active
    CACHE_COMPLETED=$CACHE_ROOT/completed
fi
```

### 2. 前置检查

```python
if 状态 != "测试中":
    print("❌ 错误：需求尚未完成测试")
    print("💡 请先执行：/req:test REQ-XXX")
    exit()

# 检查测试完成情况
未通过的测试 = 获取未通过测试点()
if 未通过的测试:
    print("⚠️ 警告：存在未通过的测试点")
    显示未通过列表
    print("是否强制完成？(y/n)")
    if 用户选择 n:
        exit()
```

### 3. 生成完成摘要

```
📋 需求完成确认：REQ-001 部门渠道关联

📊 完成统计：
- 功能点：6/6 ✅
- 测试点：8/8 ✅
- 涉及文件：12 个
- 开发周期：2 天（2026-01-07 ~ 2026-01-08）

📁 代码变更：
新增文件（4）：
- internal/sys/model/sys_dept_channel_model.go
- internal/sys/store/sys_dept_channel_store.go
- internal/sys/biz/dept_channel.go
- docs/migrations/1.2/1.2.3.sql

修改文件（8）：
- internal/sys/biz/sys_dept.go
- internal/sys/controller/v1/sys_dept.go
- internal/sys/router.go
- pkg/api/core/v1/sys_dept.go
- internal/oms/store/sales_order_store.go
- internal/oms/biz/sales_order_biz.go
- internal/dashboard/store/sales_dashboard_store.go
- internal/dashboard/biz/sales_dashboard_biz.go

是否确认完成？(y/n)
```

### 4. 更新需求文档

- 修改元信息状态为「已完成」
- 勾选生命周期「已完成」
- 记录完成时间

```markdown
## 元信息

| 属性 | 值 |
|-----|-----|
| 编号 | REQ-001 |
| 状态 | ✅ 已完成 |
| 完成日期 | 2026-01-08 |
| ... | ... |

## 生命周期

- [x] 📝 草稿（编写中）
- [x] 👀 待评审
- [x] ✅ 评审通过
- [x] 🔨 开发中
- [x] 🧪 测试中
- [x] 🎉 已完成
```

### 5. 归档文档（先本地，后缓存）

将需求文档移动到完成目录：

```bash
# 1. 先归档本地（主存储）
mv $LOCAL_ACTIVE/REQ-001-部门渠道关联.md \
   $LOCAL_COMPLETED/REQ-001-部门渠道关联.md

# 2. 同步到缓存
if [ -n "$PROJECT" ]; then
    mv $CACHE_ACTIVE/REQ-001-部门渠道关联.md \
       $CACHE_COMPLETED/REQ-001-部门渠道关联.md
fi
```

### 6. 生成完成报告

```
🎉 需求已完成！

═══════════════════════════════════════════════
📋 需求完成报告
═══════════════════════════════════════════════

📌 基本信息
- 编号：REQ-001
- 标题：部门渠道关联
- 优先级：P1
- 负责人：-

📅 时间线
- 创建：2026-01-07
- 评审通过：2026-01-07
- 开发完成：2026-01-08
- 测试通过：2026-01-08
- 完成：2026-01-08
- 总周期：2 天

📊 工作量
- 功能点：6 个
- 测试点：8 个
- 新增文件：4 个
- 修改文件：8 个

📁 归档位置
$REQ_COMPLETED/REQ-001-部门渠道关联.md

═══════════════════════════════════════════════

💡 后续操作：
- 查看历史需求：ls docs/requirements/completed/
- 创建新需求：/req:new
- 查看活跃需求：/req
```

### 7. 可选：Git 提交关联

如果有关联的 Git 提交，显示提交记录：

```
📝 关联的 Git 提交：
- d7929c9 feat(sys): 实现部门渠道关联 (REQ-001)
- 36c055f feat(sys): 添加部门渠道缓存机制 (REQ-001)
```

---

## 回滚操作

如果需要将已完成的需求重新激活：

```bash
# 手动操作
mv $REQ_COMPLETED/REQ-001-*.md $REQ_ACTIVE/
# 然后修改文档状态
```

---

## 统计数据

完成需求时自动统计：
- 需求总数
- 平均完成周期
- 功能点完成率
- 测试通过率

数据可用于团队效能分析。

## 用户输入

$ARGUMENTS
