# 公共逻辑参考

> 此文档定义所有 /api 命令共用的逻辑，各命令直接引用，避免重复。

## 配置文件

项目根目录 `.api-config.json`，存储 Swagger 数据源和代码生成配置。

### 配置结构

```json
{
  "swagger": {
    "sources": [
      {
        "name": "服务名称",
        "url": "http://localhost:8080/swagger/doc.json",
        "prefix": "/api/v1"
      },
      {
        "name": "其他服务",
        "file": "./docs/swagger.json",
        "prefix": "/pay/v1"
      }
    ]
  },
  "codegen": {
    "outputDir": "src/api",
    "typeDir": "src/types/api",
    "fieldCase": "camelCase"
  }
}
```

### 字段说明

| 字段 | 必填 | 说明 |
|------|------|------|
| `swagger.sources[].name` | 是 | 服务名称，用于标识和搜索 |
| `swagger.sources[].url` | 否 | Swagger JSON/YAML 的 URL 地址 |
| `swagger.sources[].file` | 否 | 本地 Swagger 文件路径（url 和 file 至少一个） |
| `swagger.sources[].prefix` | 否 | API 路径前缀，用于过滤接口 |
| `codegen.outputDir` | 否 | 请求函数输出目录，默认 `src/api` |
| `codegen.typeDir` | 否 | 类型定义输出目录，默认 `src/types/api` |
| `codegen.fieldCase` | 否 | 字段命名风格：`camelCase`（默认）、`snake_case`、`original` |

### 读取规则

1. 读取项目根目录的 `.api-config.json`
2. **不存在** → 提示用户执行 `/api:config init` 初始化
3. **sources 为空** → 提示用户添加 Swagger 数据源

## 请求库自动检测

代码生成时自动检测项目使用的请求库，**不需要用户配置**。

### 检测顺序

```
1. 检查项目中已有的 request 封装文件（优先级最高）：
   - 用 Glob 搜索: **/request.{ts,js}, **/http.{ts,js}, **/fetch.{ts,js}
   - 常见路径: src/utils/request.ts, src/lib/request.ts, src/services/request.ts
   - 找到 → 读取文件确认是请求封装 → 使用其导出的实例

2. 检查 package.json dependencies：
   - axios → 生成 axios 风格代码
   - umi-request / @umijs/max → 生成 umi-request 风格
   - @tanstack/react-query → 生成 fetch + react-query hooks
   - swr → 生成 fetch + swr hooks
   - ky → 生成 ky 风格代码

3. 都未检测到 → 使用原生 fetch
```

### 检测结果格式

```json
{
  "type": "custom | axios | umi-request | react-query | swr | ky | fetch",
  "importPath": "@/utils/request",
  "importName": "request",
  "example": "request.get<T>('/path')"
}
```

## Swagger 解析

### 解析方式

使用 Python 脚本 `scripts/swagger-parser.py` 解析 Swagger/OpenAPI 文档。

**支持格式：**
- OpenAPI 2.0 (Swagger)
- OpenAPI 3.0.x
- OpenAPI 3.1.x
- JSON 和 YAML 格式

### 脚本调用

脚本路径用 `${CLAUDE_PLUGIN_ROOT}/scripts/swagger-parser.py`（插件安装目录，**不是**本仓库的 `plugins/api/`）。每个 source 调一次，数据源二选一 `--url` / `--file`，输出 JSON 到 stdout。

命令里写的 `mode=xxx` 对应 `--mode`，**必须显式传**（缺省是 `summary`，漏传不会报错，只会拿到错误的结果）：

| mode | 附加参数 | 用途 |
|------|---------|------|
| `summary` | — | 接口总数与分组概览 |
| `list` | `--tag`（可选） | 接口列表 |
| `search` | `--keyword <关键词>` | 搜索接口（没有 `--search` 参数） |
| `detail` | `--path "<METHOD> <path>"` | 单个接口完整 schema（$ref 已解析） |

## 字段映射规则

### 命名转换

| 原始风格 | 目标 camelCase | 规则 |
|---------|---------------|------|
| `user_name` | `userName` | snake_case → camelCase |
| `UserName` | `userName` | PascalCase → camelCase |
| `user-name` | `userName` | kebab-case → camelCase |
| `username` | `username` | 全小写保持不变 |
| `ID` | `id` | 全大写缩写转小写 |
| `userID` | `userId` | 尾部大写缩写处理 |

### 类型映射

| Swagger 类型 | TypeScript 类型 | 备注 |
|-------------|----------------|------|
| `integer` / `int32` / `int64` | `number` | — |
| `number` / `float` / `double` | `number` | — |
| `string` | `string` | — |
| `string` + `format: date-time` | `string` | 日期时间保持 string |
| `boolean` | `boolean` | — |
| `array` + `items` | `T[]` | 递归解析 items |
| `object` + `properties` | `interface` | 递归解析 properties |
| `$ref` | 引用对应 interface | 解析引用链 |
| `enum` | 联合类型 | `'a' \| 'b' \| 'c'` |
| `oneOf` / `anyOf` | 联合类型 | `A \| B` |
| `allOf` | 交叉类型 | `A & B` |

### 必填/可选判断

- Swagger `required` 数组中的字段 → TypeScript 必填属性
- 不在 `required` 中的字段 → TypeScript 可选属性 `?`

## 代码生成模板

### TypeScript 类型

```typescript
/** {接口描述} - 响应类型 */
export interface {PascalCase接口名}Response {
  {字段名}: {类型};
  {字段名}?: {类型};  // 可选
}

/** {接口描述} - 请求参数 */
export interface {PascalCase接口名}Params {
  {字段名}: {类型};
}
```

### 请求函数

根据检测到的请求库生成对应风格的代码，参见「请求库自动检测」章节。

## 命令执行前置检查

所有命令（除 `/api:config init`）执行前需检查：

1. `.api-config.json` 是否存在
2. `swagger.sources` 是否有数据源
3. Python 3 是否可用（`python3 --version`）

缺失时给出明确提示和修复建议。
