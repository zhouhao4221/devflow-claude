---
description: 分析代码和接口定义生成测试指导文件
argument-hint: "[module]"
allowed-tools: Read, Write, Edit, Glob, Bash(find:*, grep:*)
---

# 分析代码生成测试指导文件

扫描项目代码和接口定义，推导测试场景，生成结构化的 flow 文档草稿。

## 命令格式

```
/uat:analyze [module]
```

---

## 执行流程

### 1. 确定模块名和分析范围

- 若参数已传入模块名，直接使用
- 否则询问：`请输入测试模块名称（如：客户管理、用户登录）`

检查 `docs/uat/flows/<module>.md` 是否已存在：
- 已存在 → 提示 `该模块已有流程文档，是否覆盖？(y/n)` —— 选 n 则改为「补充分析」模式（仅新增场景）

询问分析目标（可多选，默认全选）：
```
选择分析来源（直接回车全选）：
  A. 前端路由 / 页面组件（Vue/React）
  B. 表单组件（提取字段与校验规则）
  C. API 接口文档（OpenAPI/Swagger）
  D. 后端路由（FastAPI/Express/Spring/Go）
```

### 2. 自动扫描（按选中项执行）

**A. 前端路由扫描**

查找路径：`src/router/`, `src/routes/`, `router.ts`, `router.js`, `app-routing.module.ts`，提取：
- 路由路径 + 对应组件文件路径
- 路由 meta（页面标题、权限标识）

无结果时跳过，打印 `⚠️ 未找到前端路由文件`。

**B. 表单组件分析**

在 `src/` 下扫描 `*.vue`, `*.tsx`, `*.jsx`，查找包含表单标签（`<form`, `<el-form`, `<a-form`, `<van-form`）的文件，提取：
- 字段名（label 文本 / v-model 绑定名 / name 属性）
- 字段类型（input/select/datepicker/upload 等）
- 校验规则（required, maxlength, minlength, pattern, rules 属性）
- 提交按钮和取消按钮的位置

**C. API 接口文档分析**

按优先级查找：
1. `docs/openapi.yaml`, `docs/swagger.json`, `openapi.yaml`, `swagger.yaml`
2. `src/api/`, `src/apis/`, `api/` 目录下的 `*.ts`/`*.js` 文件（提取 URL 常量和方法调用）

从 OpenAPI 文档提取：
- 路径 + HTTP 方法 + summary
- 请求体字段（必填/选填）
- 响应结构
- 重点关注 POST/PUT/PATCH/DELETE（有副作用）

**D. 后端路由分析**

扫描常见模式：
- FastAPI：`@router.get/post/put/delete`, `@app.get/post`
- Express：`router.get/post`, `app.get/post`
- Spring：`@GetMapping`, `@PostMapping`, `@RestController`
- Go Gin：`r.GET/POST`, `group.GET/POST`

提取：路径、HTTP 方法、处理函数名（从名称推断功能）。

### 3. 推导测试场景

根据扫描结果，按以下规则推导场景候选：

| 发现内容 | 推导场景 |
|---------|---------|
| 列表页路由 | 列表浏览（含分页/搜索） |
| 含 POST 接口的表单页 | 新增场景 |
| 含 PUT/PATCH 接口的表单页 | 编辑场景 |
| 含 DELETE 接口的列表页 | 删除场景（含二次确认） |
| 登录页路由 | 正常登录 + 错误提示 |
| 有 required 字段的表单 | 必填校验场景 |

同一表单的新增 + 表单字段 → 合并建议「表单边界 & 字符类型」场景。

### 4. 展示分析摘要并确认

```
📊 代码分析结果：<module>

  前端路由：5 个页面
  表单组件：3 个（共 14 个字段）
  API 接口：18 个（POST×6 PUT×3 DELETE×2 GET×7）

📋 推导场景（9 个）：

  来自路由 + API 分析：
    S01 客户列表浏览        GET /api/customers（分页/搜索）
    S02 新增客户            POST /api/customers（5 个必填字段）
    S03 编辑客户            PUT /api/customers/:id
    S04 删除客户            DELETE /api/customers/:id（含确认弹窗）
    S05 客户详情查看        GET /api/customers/:id

  来自 API 分析（无对应前端路由）：
    S06 批量导出客户        GET /api/customers/export

  建议补充边界测试：
    S07 客户表单 - 边界 & 字符类型（6 个字段待覆盖）

确认生成哪些场景？（回车全选，或输入编号如 1,2,4）
```

若无任何有效发现，提示：
```
⚠️ 未找到可分析的代码文件

💡 可以尝试：
   - 指定源码目录：/uat:analyze --src=src/modules/customer
   - 手动创建测试文档：/uat:new <module>
```

### 5. 生成流程文档

按确认的场景，严格套用 `plugins/uat/templates/flow-template.md` 格式生成文档：

- 步骤用**意图语言**描述（不写选择器）；已知字段名写入步骤，如「在客户名称输入框输入测试值」
- 字段约束（maxlength 等）从代码提取后填入表单边界测试矩阵
- 测试数据表格：将分析到的必填字段作为占位行，值留空等用户补填
- 元信息追加两行：

```
| 生成方式 | 代码分析（/uat:analyze） |
| 分析时间 | YYYY-MM-DD |
```

- 分析到字段时，在对应步骤末尾标注代码来源，如：

```
2. 填写客户名称（maxlength: 50，来源：CustomerForm.vue:38）
```

### 6. 输出结果

```
✅ 测试指导文件已生成（基于代码分析）

📁 docs/uat/flows/<module>.md
📊 场景数：7
⚠️  以下字段来源无法自动推断，请手动补充：
    - 测试数据（账号/密码等）
    - S02 步骤 4 的预期提示文本

💡 检查并补充文档后执行：/uat:run <module>
💡 若有遗漏场景，继续追加：/uat:new <module>（补充模式）
```
