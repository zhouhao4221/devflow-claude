---
name: dev-guide
description: |
  开发引导助手。仅在执行 /req:dev 命令时触发。按项目分层架构引导开发。
---

# 开发引导助手

仅在 `/req:dev` 命令执行时激活，引导按分层架构实现代码。

## 分层架构

```
Model → Store → Biz → Controller → Router
```

## 开发顺序

1. **Model** - 数据模型定义
   - 包含 TenantID（多租户）
   - 定义 TableName()

2. **Store** - 数据访问层
   - 定义接口 + 实现
   - CRUD 操作

3. **Biz** - 业务逻辑层
   - 业务校验
   - 使用 errno 返回错误
   - 使用结构化日志

4. **Controller** - 接口层
   - Swagger 注解
   - 参数绑定校验
   - response 包封装响应

5. **Router** - 路由注册
   - 权限标识：`module:resource:action`

## 代码规范

- 文件名：kebab-case
- 日志：`log.Info/Error(msg, ctx, k, v...)`
- 错误：`errno.ErrXxx`
- 事务：`store.DB().Transaction()`

## 检查清单

- [ ] 分层架构正确
- [ ] 多租户支持
- [ ] 日志规范
- [ ] 错误处理
- [ ] Swagger 注解
