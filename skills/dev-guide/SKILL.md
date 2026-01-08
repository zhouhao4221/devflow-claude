---
name: dev-guide
description: |
  开发引导助手。在执行 /req dev 开发需求时自动激活，或用户讨论"怎么实现"、
  "代码怎么写"、"帮我写这个功能"时触发。按照项目架构引导代码实现。
---

# 开发引导助手

按照项目分层架构引导开发实现。

## 触发场景

- 执行 `/req dev` 命令进入开发模式
- 用户问"这个功能怎么实现"
- 用户说"帮我写这个代码"
- 开发过程中遇到问题

## 项目架构理解

### 分层架构

```
Router (路由层)
   ↓
Controller (控制器层) - 参数校验、响应封装
   ↓
Biz (业务层) - 业务逻辑、事务处理
   ↓
Store (存储层) - 数据访问、CRUD
   ↓
Model (模型层) - 数据结构定义
```

### 文件命名规范

- 文件名：kebab-case（如 `sys-dept-channel.go`）
- 变量名：camelCase
- 类型名：PascalCase
- 常量名：PascalCase 或 UPPER_SNAKE_CASE

## 开发引导流程

### 1. Model 层

```go
// internal/xxx/model/xxx_model.go
package model

import "tuangou/internal/core/model"

// Xxx 资源中文名
type Xxx struct {
    model.Model
    TenantID uint64 `gorm:"column:tenant_id;not null;index" json:"-"`
    // 业务字段...
}

func (m *Xxx) TableName() string {
    return "table_name"
}
```

**检查点：**
- [ ] 包含 TenantID 字段（多租户）
- [ ] 正确定义 TableName
- [ ] 字段标签完整（gorm、json）
- [ ] 添加中文注释

### 2. Store 层

```go
// internal/xxx/store/xxx_store.go
package store

import (
    "context"
    "tuangou/internal/xxx/model"
    "tuangou/internal/core/store"
)

type XxxStore interface {
    Create(ctx context.Context, m *model.Xxx) error
    Update(ctx context.Context, m *model.Xxx) error
    Delete(ctx context.Context, id uint64) error
    Get(ctx context.Context, id uint64) (*model.Xxx, error)
    List(ctx context.Context, tenantID uint64, opts ...store.QueryOption) ([]*model.Xxx, int64, error)
}

type xxxStore struct{}

var _ XxxStore = (*xxxStore)(nil)

func NewXxxStore() XxxStore {
    return &xxxStore{}
}

func (s *xxxStore) Create(ctx context.Context, m *model.Xxx) error {
    return store.DB().WithContext(ctx).Create(m).Error
}

// 其他方法实现...
```

**检查点：**
- [ ] 定义接口
- [ ] 实现接口检查 `var _ Interface = (*impl)(nil)`
- [ ] 使用 `store.DB()` 获取数据库连接
- [ ] 正确处理 context

### 3. Biz 层

```go
// internal/xxx/biz/xxx_biz.go
package biz

import (
    "context"
    "tuangou/internal/xxx/model"
    "tuangou/internal/xxx/store"
    "tuangou/pkg/errno"
    "tuangou/pkg/log"
)

type XxxBiz struct {
    store store.XxxStore
}

func NewXxxBiz() *XxxBiz {
    return &XxxBiz{
        store: store.NewXxxStore(),
    }
}

func (b *XxxBiz) Create(ctx context.Context, req *api.CreateXxxReq) (*model.Xxx, error) {
    // 业务逻辑校验

    m := &model.Xxx{
        // 字段映射
    }

    if err := b.store.Create(ctx, m); err != nil {
        log.Error("创建失败", ctx, "error", err)
        return nil, errno.ErrDatabase
    }

    return m, nil
}
```

**检查点：**
- [ ] 使用 errno 包返回错误
- [ ] 使用结构化日志 `log.Info/Error`
- [ ] 复杂操作使用事务
- [ ] 正确的错误处理

### 4. Controller 层

```go
// internal/xxx/controller/v1/xxx.go
package v1

import (
    "github.com/gin-gonic/gin"
    "tuangou/internal/xxx/biz"
    "tuangou/internal/core/response"
    "tuangou/pkg/api/core/v1"
)

type XxxController struct {
    biz *biz.XxxBiz
}

func NewXxxController() *XxxController {
    return &XxxController{
        biz: biz.NewXxxBiz(),
    }
}

// List 获取列表
// @Summary 获取Xxx列表
// @Description 获取Xxx列表
// @Tags Xxx管理
// @Security ApiKeyAuth
// @Param page query int false "页码"
// @Param page_size query int false "每页数量"
// @Success 200 {object} response.Response{data=v1.XxxListResp}
// @Router /api/v1/xxx/xxxs [get]
func (c *XxxController) List(ctx *gin.Context) {
    // 实现...
    response.Success(ctx, data)
}
```

**检查点：**
- [ ] 完整的 Swagger 注解
- [ ] 使用 response 包封装响应
- [ ] 正确的参数绑定和校验
- [ ] 权限标识正确

### 5. Router 层

```go
// internal/xxx/router.go

// Xxx管理
xxxCtrl := v1.NewXxxController()
xxxGroup := apiV1.Group("/xxxs")
{
    xxxGroup.GET("", rp("xxx:xxx:list"), xxxCtrl.List)
    xxxGroup.POST("", rp("xxx:xxx:create"), xxxCtrl.Create)
    xxxGroup.GET("/:id", rp("xxx:xxx:get"), xxxCtrl.Get)
    xxxGroup.PUT("/:id", rp("xxx:xxx:update"), xxxCtrl.Update)
    xxxGroup.DELETE("/:id", rp("xxx:xxx:delete"), xxxCtrl.Delete)
}
```

**检查点：**
- [ ] 路由分组正确
- [ ] 权限标识格式：`module:resource:action`
- [ ] RESTful 风格

### 6. API 定义

```go
// pkg/api/core/v1/xxx.go
package v1

// CreateXxxReq 创建请求
type CreateXxxReq struct {
    Name string `json:"name" binding:"required" example:"示例"`
}

// XxxResp 响应
type XxxResp struct {
    ID   uint64 `json:"id"`
    Name string `json:"name"`
}
```

### 7. Swagger 文档

开发完成后执行：
```bash
make swagger-doc-mac
```

## 代码规范提醒

### 日志规范
```go
// ✅ 正确
log.Info("操作成功", ctx, "id", id, "name", name)
log.Error("操作失败", ctx, "error", err)

// ❌ 错误
fmt.Println("debug")
log.Printf("xxx")
```

### 错误处理
```go
// ✅ 正确
return errno.ErrDatabase
return errno.ErrNotFound
return errno.New(errno.ErrBadRequest, "自定义消息")

// ❌ 错误
return errors.New("xxx")
return fmt.Errorf("xxx")
```

### 事务处理
```go
// 多步操作使用事务
err := store.DB().Transaction(func(tx *gorm.DB) error {
    if err := tx.Create(&m1).Error; err != nil {
        return err
    }
    if err := tx.Create(&m2).Error; err != nil {
        return err
    }
    return nil
})
```

## 完成检查清单

开发完成前确认：
- [ ] 代码符合分层架构
- [ ] 命名符合规范
- [ ] 日志完整且规范
- [ ] 错误处理正确
- [ ] 多租户支持
- [ ] Swagger 注解完整
- [ ] 无安全漏洞