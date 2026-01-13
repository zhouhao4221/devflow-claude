# REQ-XXX: 需求标题

## 元信息

| 属性 | 值 |
|-----|-----|
| 编号 | REQ-XXX |
| 类型 | 后端 / 前端 / 全栈 |
| 状态 | 草稿 |
| 模块 | - |
| 优先级 | P2 |
| 创建日期 | YYYY-MM-DD |
| 负责人 | - |

## 生命周期

<!-- 需求状态流转：草稿 → 待评审 → 评审通过 → 开发中 → 测试中 → 已完成 -->

- [ ] 📝 草稿（编写中）
- [ ] 👀 待评审
- [ ] ✅ 评审通过
- [ ] 🔨 开发中
- [ ] 🧪 测试中
- [ ] 🎉 已完成

---

## 一、需求描述

### 1.1 背景

简要说明需求产生的背景...

### 1.2 目标

本需求要实现的目标...

### 1.3 价值

实现后带来的业务价值...

---

## 二、功能清单

> 列出所有功能点，开发完成后勾选

- [ ] **功能点1**：描述...
- [ ] **功能点2**：描述...
- [ ] **功能点3**：描述...

---

## 三、业务规则

| 规则 | 说明 |
|-----|------|
| 规则1 | 详细说明 |
| 规则2 | 详细说明 |

---

## 四、数据模型

### 4.1 新增/修改表

```sql
-- 表结构定义
CREATE TABLE `table_name` (
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '主键ID',
    `tenant_id` BIGINT UNSIGNED NOT NULL DEFAULT 0 COMMENT '租户ID',
    -- 字段定义...
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (`id`),
    KEY `idx_tenant_id` (`tenant_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='表注释';
```

### 4.2 字段说明

| 字段 | 类型 | 必填 | 说明 |
|-----|------|-----|------|
| id | bigint | 是 | 主键 |
| tenant_id | bigint | 是 | 租户ID |

---

## 五、API 设计

### 5.1 接口1：创建XXX

```
POST /api/v1/module/resource
```

**请求参数：**

| 字段 | 类型 | 必填 | 说明 |
|-----|------|-----|------|
| name | string | 是 | 名称 |

**响应示例：**

```json
{
  "code": 0,
  "msg": "success",
  "data": {
    "id": 1
  }
}
```

### 5.2 接口2：查询XXX

```
GET /api/v1/module/resource
```

**查询参数：**

| 字段 | 类型 | 必填 | 说明 |
|-----|------|-----|------|
| page | int | 否 | 页码，默认1 |
| page_size | int | 否 | 每页数量，默认20 |

---

## 六、文件改动清单

> 列出需要修改的文件，便于代码审查和影响评估

| 层级 | 文件路径 | 改动说明 |
|-----|---------|---------|
| Model | `internal/xxx/model/xxx.go` | 新增模型 |
| Store | `internal/xxx/store/xxx.go` | 新增存储层 |
| Biz | `internal/xxx/biz/xxx.go` | 新增业务层 |
| Ctrl | `internal/xxx/controller/v1/xxx.go` | 新增控制器 |
| API | `pkg/api/core/v1/xxx.go` | 新增请求响应结构 |
| Router | `internal/xxx/router.go` | 新增路由 |

---

## 七、实现步骤

> 按顺序列出开发步骤

1. **数据库变更** - 执行迁移脚本
2. **Model 层** - 创建模型
3. **Store 层** - 实现数据访问
4. **Biz 层** - 实现业务逻辑
5. **Ctrl 层** - 实现接口
6. **Router** - 注册路由
7. **Swagger** - 更新文档 `make swagger-doc-mac`
8. **测试** - 接口测试验证

---

## 八、测试要点

- [ ] 测试点1：描述测试场景和预期结果
- [ ] 测试点2：描述测试场景和预期结果

---

## 九、评审记录

| 日期 | 评审人 | 结论 | 意见 |
|-----|-------|------|------|
| - | - | - | - |

---

## 十、变更记录

| 日期 | 变更内容 | 影响范围 |
|-----|---------|---------|
| YYYY-MM-DD | 初始版本 | - |

---

## 十一、关联信息

- **关联需求**：REQ-XXX（前端/后端对应需求）
- **相关文档**：链接
- **协作说明**：描述前后端协作要点
