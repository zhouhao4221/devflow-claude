---
description: 编辑需求 - 修改已有需求文档
---

# 编辑需求

编辑已有需求文档，仅修改内容，不触发开发流程。

## 命令格式

```
/req:edit [REQ-XXX]
```

**说明**：编号可选，省略时自动选择最近活跃的需求。

---

## 执行流程

### 0. 自动识别需求

如果未提供 REQ-XXX 编号：

```python
# 查找所有活跃需求，按修改时间排序
candidates = find_requirements(dir="active", sort_by="mtime")

if len(candidates) == 0:
    print("❌ 没有活跃的需求")
    print("💡 请先创建需求：/req:new")
    exit()
elif len(candidates) == 1:
    REQ_ID = candidates[0]
    print(f"📌 自动选择：{REQ_ID}")
else:
    print("📋 发现多个活跃需求，请选择：")
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
    # 全局缓存路径（同步副本）
    CACHE_ROOT=~/.claude-requirements/projects/$PROJECT
    CACHE_ACTIVE=$CACHE_ROOT/active
    CACHE_COMPLETED=$CACHE_ROOT/completed
fi
```

### 2. 前置检查（优先读本地）

```bash
# 优先从本地查找
REQ_FILE=$(ls $LOCAL_ACTIVE/REQ-XXX-*.md 2>/dev/null | head -1)

# 本地不存在时，从缓存读取
if [ -z "$REQ_FILE" ] && [ -n "$PROJECT" ]; then
    CACHE_FILE=$(ls $CACHE_ACTIVE/REQ-XXX-*.md 2>/dev/null | head -1)
    if [ -n "$CACHE_FILE" ]; then
        # 从缓存复制到本地
        cp $CACHE_FILE $LOCAL_ACTIVE/
        REQ_FILE=$LOCAL_ACTIVE/$(basename $CACHE_FILE)
    fi
fi

if [ -z "$REQ_FILE" ]; then
    echo "❌ 未找到需求：REQ-XXX"
    exit 1
fi
```

### 3. 加载需求文档

读取并解析需求文档内容。

### 4. 状态提示

如果需求已在开发中或测试中：

```
⚠️ 警告：需求 REQ-XXX 当前状态为「开发中」
修改需求可能影响已完成的开发工作。

是否继续编辑？(y/n)
```

### 5. 选择编辑章节

询问用户要编辑的内容：

```
请选择要编辑的章节：
1. 需求描述
2. 功能清单
3. 业务规则
4. 数据模型
5. API 设计
6. 文件改动清单
7. 实现步骤
8. 测试要点
9. 全部重新分析

请输入编号（可多选，如 1,2,3）：
```

### 6. 交互式编辑

根据选择进入对应章节的编辑模式：
- 展示当前内容
- 接收用户输入
- 智能补充和优化

### 7. 变更影响分析

如果需求已在开发中，分析变更影响：

```
📊 变更影响分析

修改内容：
- API 设计：新增字段 channel_ids

影响评估：
- 直接影响：Controller、API 层需要修改
- 间接影响：前端需配合调整

受影响文件：
- internal/sys/controller/v1/sys_dept.go
- pkg/api/core/v1/sys_dept.go

建议：完成当前开发后再进行变更
```

### 8. 记录变更

更新「变更记录」章节：

```markdown
## 十、变更记录

| 日期 | 变更内容 | 影响范围 |
|-----|---------|---------|
| 2026-01-08 | 修改 API 设计，新增字段 | Controller、API |
| 2026-01-07 | 初始版本 | - |
```

### 9. 保存并同步（先本地，后缓存）

```bash
# 1. 先写入本地（主存储）
write_to $LOCAL_ACTIVE/REQ-XXX-标题.md

# 2. 同步到缓存（如已绑定项目）
if [ -n "$PROJECT" ]; then
    cp $LOCAL_ACTIVE/REQ-XXX-标题.md $CACHE_ACTIVE/
fi
```

### 10. 输出结果

```
✅ 需求已更新：REQ-XXX

📁 本地存储：docs/requirements/active/REQ-XXX-标题.md
🔄 缓存同步：已同步到全局缓存

📝 变更摘要：
- 修改了 API 设计
- 新增了 2 个功能点

💡 下一步：
- 继续编辑：/req:edit REQ-XXX
- 提交评审：/req:review
- 查看状态：/req:status
```

---

## 编辑模式说明

### 增量编辑
保留原有内容，仅修改/新增指定部分。

### 全量重写
如选择「全部重新分析」，将重新引导需求分析流程，但保留元信息和变更记录。

---

## 注意事项

- 编辑不会改变需求状态
- 已开发的需求变更需谨慎
- 所有变更都会记录到变更历史
- **存储策略**：本地优先写入，成功后同步到全局缓存

## 用户输入

$ARGUMENTS