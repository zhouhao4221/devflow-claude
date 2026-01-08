---
name: requirement-analyzer
description: |
  需求分析助手。在用户创建新需求、讨论需求细节、提到"需求分析"、"功能设计"、
  "API设计"、"数据模型"、"业务规则"时自动触发。帮助用户完善需求文档的各个章节。
---

# 需求分析助手

当用户讨论需求相关内容时，帮助分析和完善需求。

## 触发场景

- 用户说"新需求"、"新功能"、"我想要..."
- 用户讨论业务规则、数据校验
- 用户讨论 API 设计、接口定义
- 用户提供产品需求文档（PRD）
- 用户询问"怎么设计"、"需要哪些字段"

## 分析框架

### 1. 理解需求背景

首先确认：
- **业务目标**：这个需求要解决什么问题？
- **用户价值**：给谁用？带来什么价值？
- **使用场景**：在什么情况下使用？

### 2. 功能点拆解

将需求拆解为原子功能点：

```markdown
## 功能清单

- [ ] **功能点1**：描述（可独立开发和测试）
- [ ] **功能点2**：描述
  - 依赖：功能点1
- [ ] **功能点3**：描述
```

拆解原则：
- 每个功能点可独立开发
- 每个功能点可独立测试
- 明确功能点之间的依赖关系
- 按优先级排序

### 3. 业务规则提取

识别并明确所有业务规则：

| 规则类型 | 示例 |
|---------|------|
| 数据校验 | 字段必填、格式要求、长度限制 |
| 状态转换 | 订单状态流转规则 |
| 权限控制 | 谁可以做什么操作 |
| 边界条件 | 最大值、最小值、特殊情况处理 |
| 计算逻辑 | 金额计算、统计规则 |

### 4. 数据模型设计

如果涉及数据变更：

#### 4.1 识别实体
- 新增哪些实体？
- 修改哪些现有实体？
- 实体之间的关系？

#### 4.2 设计表结构
```sql
CREATE TABLE `table_name` (
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '主键ID',
    `tenant_id` BIGINT UNSIGNED NOT NULL DEFAULT 0 COMMENT '租户ID',
    -- 业务字段
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    KEY `idx_tenant_id` (`tenant_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='表注释';
```

#### 4.3 字段说明
| 字段 | 类型 | 必填 | 说明 |
|-----|------|-----|------|

### 5. API 设计

遵循项目 RESTful 规范设计接口：

#### 5.1 接口列表
| 方法 | 路径 | 说明 |
|-----|------|------|
| GET | /api/v1/module/resources | 列表查询 |
| POST | /api/v1/module/resources | 创建 |
| GET | /api/v1/module/resources/:id | 详情 |
| PUT | /api/v1/module/resources/:id | 更新 |
| DELETE | /api/v1/module/resources/:id | 删除 |

#### 5.2 接口详情
每个接口定义：
- 请求参数
- 响应结构
- 错误码
- 权限要求

### 6. 文件改动评估

基于项目分层架构评估涉及的文件：

| 层级 | 文件路径 | 改动说明 |
|-----|---------|---------|
| Model | `internal/xxx/model/xxx.go` | 新增/修改 |
| Store | `internal/xxx/store/xxx.go` | 新增/修改 |
| Biz | `internal/xxx/biz/xxx.go` | 新增/修改 |
| Ctrl | `internal/xxx/controller/v1/xxx.go` | 新增/修改 |
| API | `pkg/api/core/v1/xxx.go` | 新增/修改 |
| Router | `internal/xxx/router.go` | 新增路由 |

### 7. 实现步骤规划

生成标准化的开发步骤：

1. **数据库变更** - 执行迁移脚本
2. **Model 层** - 创建/修改模型
3. **Store 层** - 实现数据访问
4. **Biz 层** - 实现业务逻辑
5. **Ctrl 层** - 实现接口
6. **Router** - 注册路由
7. **Swagger** - 更新文档
8. **测试** - 接口测试验证

### 8. 测试要点

列出关键测试场景：

```markdown
## 测试要点

- [ ] 正常流程测试：描述预期结果
- [ ] 边界条件测试：描述预期结果
- [ ] 异常情况测试：描述预期结果
- [ ] 权限测试：描述预期结果
```

## 输出要求

- 使用项目的需求模板格式
- 内容清晰、完整、可执行
- 技术方案符合项目架构规范
- 估算合理的工作量

## 交互方式

1. 先理解用户的需求背景
2. 逐步引导完善各个章节
3. 有疑问主动询问确认
4. 最终输出完整的需求文档
