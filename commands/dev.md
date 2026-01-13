---
description: 需求开发 - 启动或继续开发
---

# 需求开发

启动或继续需求开发，生成开发任务并逐步实现。

## 命令格式

```
/req:dev [REQ-XXX]
```

**说明**：编号可选，省略时自动识别当前进行中的需求。

---

## 执行流程

### 0. 自动识别需求

如果未提供 REQ-XXX 编号：

```python
# 查找状态为「评审通过」或「开发中」的需求
candidates = find_requirements(status=["评审通过", "开发中"])

if len(candidates) == 0:
    print("❌ 没有可开发的需求")
    print("💡 请先创建需求：/req:new")
    exit()
elif len(candidates) == 1:
    REQ_ID = candidates[0]
    print(f"📌 自动选择：{REQ_ID}")
else:
    print("📋 发现多个可开发的需求，请选择：")
    for i, req in enumerate(candidates):
        print(f"  {i+1}. {req}")
    # 等待用户选择
```

### 1. 解析存储路径（本地优先 + 缓存同步）

```bash
# 本地存储路径（主存储）
LOCAL_ROOT=docs/requirements
LOCAL_ACTIVE=$LOCAL_ROOT/active

# 检查当前仓库绑定的项目（用于缓存同步）
PROJECT=$(cat .claude/settings.local.json 2>/dev/null | jq -r '.requirementProject // empty')

if [ -n "$PROJECT" ]; then
    CACHE_ROOT=~/.claude-requirements/projects/$PROJECT
    CACHE_ACTIVE=$CACHE_ROOT/active
fi
```

### 2. 前置检查

```python
if 状态 not in ["评审通过", "开发中", "测试中"]:
    print("❌ 错误：需求尚未通过评审")
    print("💡 请先执行：/req:review REQ-XXX")
    exit()
```

### 3. 加载需求上下文

优先读取本地，本地不存在时从缓存读取：
- 功能清单（识别已完成/未完成）
- 文件改动清单
- 实现步骤
- 数据模型
- API 设计

### 4. 显示开发概览

```
📋 需求开发：REQ-001 部门渠道关联

📊 进度概览：
- 功能点：2/6 已完成
- 当前状态：🔨 开发中

📝 功能清单：
- [x] 部门渠道关联 - Model/Store 层
- [x] 渠道范围校验
- [ ] 获取可选渠道接口      ← 当前
- [ ] 订单数据过滤
- [ ] Dashboard数据过滤
- [ ] 缓存机制

📁 涉及文件：
- internal/sys/model/sys_dept_channel_model.go
- internal/sys/store/sys_dept_channel_store.go
- ... (共 12 个文件)
```

### 5. 更新状态为「开发中」（先本地，后缓存）

首次进入开发时：
- 修改元信息状态为「开发中」
- 勾选生命周期「开发中」
- 先写入本地，再同步到缓存

### 6. 生成开发任务

使用 TodoWrite 创建任务列表：

```
根据实现步骤和功能清单生成：

1. [ ] 数据库变更 - 创建 sys_dept_channel 表
2. [ ] Model 层 - SysDeptChannelModel
3. [ ] Store 层 - SysDeptChannelStore CRUD
4. [ ] Biz 层 - DeptChannelService（含缓存）
5. [ ] Biz 层 - 修改 SysDeptBiz 添加校验
6. [ ] Controller 层 - 修改部门接口
7. [ ] Controller 层 - 新增获取可选渠道接口
8. [ ] Router - 注册新路由
9. [ ] 订单模块 - 渠道过滤
10. [ ] Dashboard 模块 - 渠道过滤
11. [ ] Swagger 文档更新
```

### 6. 逐步开发引导

按照任务顺序逐步实现：

#### 6.1 开发前检查
- 确认相关文件存在
- 理解现有代码结构

#### 6.2 生成代码
按照项目规范生成代码：
- Model：数据模型定义
- Store：数据访问层
- Biz：业务逻辑层
- Controller：接口层
- Router：路由注册

#### 6.3 代码规范检查
实时检查：
- 命名规范（kebab-case 文件名）
- 日志规范（结构化日志）
- 错误处理（errno 包）
- 多租户（TenantID）
- Swagger 注解

### 7. 进度更新

每完成一个步骤：
- 更新 TodoWrite 任务状态
- 更新需求文档中的功能点 checkbox
- 显示进度摘要

### 8. 变更处理

如果需求在开发中被修改：

```
⚠️ 检测到需求变更

变更内容：
- 新增功能点：渠道删除时校验
- 修改 API：新增 force 参数

影响评估：
- 需要新增：Store 层删除方法
- 需要修改：Controller 层删除接口

是否接受变更并调整任务？(y/n)
```

### 9. 开发完成

全部功能点完成后：

```
🎉 开发完成！

📊 完成统计：
- 功能点：6/6 ✅
- 新增文件：4 个
- 修改文件：8 个

📋 下一步操作：

1. 代码审查（推荐）
   /code-reviewer

2. 更新 Swagger 文档
   make swagger-doc-mac

3. 进入测试
   /req:test REQ-001
```

询问是否执行代码审查和 Swagger 更新。

---

## 开发模式说明

### 全量开发
首次进入，从头开始所有步骤。

### 增量开发
继续上次进度，跳过已完成步骤。

### 重新开发
强制从头开始：`/req:dev REQ-XXX --reset`

---

## 与现有工具集成

| 工具 | 集成点 |
|------|-------|
| code-reviewer | 开发完成后自动触发 |
| git-commit | 支持关联需求编号 |
| api-tester | 接口开发后验证 |

## 用户输入

$ARGUMENTS