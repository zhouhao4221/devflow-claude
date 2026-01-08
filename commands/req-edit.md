---
description: 编辑需求 - 修改已有需求文档
---

# 编辑需求

编辑已有需求文档，仅修改内容，不触发开发流程。

## 命令格式

```
/req edit <REQ-XXX>
```

---

## 执行流程

### 0. 解析需求路径

```bash
# 检查当前仓库绑定的项目
PROJECT=$(cat .claude/settings.local.json 2>/dev/null | jq -r '.requirementProject // empty')

if [ -n "$PROJECT" ]; then
    REQ_ROOT=~/.claude-requirements/projects/$PROJECT
else
    REQ_ROOT=docs/requirements
fi

REQ_ACTIVE=$REQ_ROOT/active
REQ_COMPLETED=$REQ_ROOT/completed
```

### 1. 前置检查

```
验证需求文档是否存在：
- $REQ_ACTIVE/REQ-XXX-*.md
- 如果不存在，提示错误并退出
```

### 2. 加载需求文档

读取并解析需求文档内容。

### 3. 状态提示

如果需求已在开发中或测试中：

```
⚠️ 警告：需求 REQ-XXX 当前状态为「开发中」
修改需求可能影响已完成的开发工作。

是否继续编辑？(y/n)
```

### 4. 选择编辑章节

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

### 5. 交互式编辑

根据选择进入对应章节的编辑模式：
- 展示当前内容
- 接收用户输入
- 智能补充和优化

### 6. 变更影响分析

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

### 7. 记录变更

更新「变更记录」章节：

```markdown
## 十、变更记录

| 日期 | 变更内容 | 影响范围 |
|-----|---------|---------|
| 2026-01-08 | 修改 API 设计，新增字段 | Controller、API |
| 2026-01-07 | 初始版本 | - |
```

### 8. 保存并提示

```
✅ 需求已更新：REQ-XXX

📝 变更摘要：
- 修改了 API 设计
- 新增了 2 个功能点

💡 下一步：
- 继续编辑：/req edit REQ-XXX
- 提交评审：/req review REQ-XXX
- 查看状态：/req status REQ-XXX
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

## 用户输入

$ARGUMENTS