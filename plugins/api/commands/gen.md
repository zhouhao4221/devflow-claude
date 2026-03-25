---
description: 代码生成 - 根据接口定义生成 TypeScript 类型和请求函数
---

# 代码生成

根据 Swagger 接口定义，自动生成 TypeScript 类型定义和请求函数代码。

## 命令格式

```
/api:gen <METHOD> <path> [--name=服务名] [--type-only] [--request-only] [--tag=分组名]
```

## 参数说明

| 参数 | 必填 | 说明 |
|------|------|------|
| `METHOD` | 是 | HTTP 方法，或 `*` 表示该路径所有方法 |
| `path` | 是 | API 路径 |
| `--name` | 否 | 指定数据源 |
| `--type-only` | 否 | 仅生成类型定义 |
| `--request-only` | 否 | 仅生成请求函数 |
| `--tag` | 否 | 按 Tag 批量生成该分组下所有接口 |

## 执行流程

### 前置检查

1. 参考 `_common.md` 的「命令执行前置检查」
2. 执行请求库自动检测（参考 `_common.md`「请求库自动检测」）
3. 读取 `codegen.outputDir` 和 `codegen.typeDir`

### 生成流程

1. **解析接口定义**

   调用 Python 脚本获取接口完整 schema：

   ```bash
   python3 <plugin-path>/scripts/swagger-parser.py \
     --url "<source.url>" \
     --mode detail \
     --path "GET /api/v1/users/{id}"
   ```

2. **检测请求库**

   按 `_common.md`「请求库自动检测」规则检测，确定代码风格。

3. **生成类型定义文件**

   目标路径：`{typeDir}/{模块名}.ts`

   模块名从 API 路径推断：
   - `/api/v1/users/{id}` → `user.ts`
   - `/api/v1/orders/{id}/items` → `order.ts`
   - 同一资源的接口类型合并到同一文件

   **文件已存在时**：
   - 读取现有文件，检查是否已有同名 interface
   - 已有 → 提示用户确认是否覆盖
   - 未有 → 追加到文件末尾

4. **生成请求函数文件**

   目标路径：`{outputDir}/{模块名}.ts`

   同样合并同一资源到同一文件。

5. **展示生成结果**

### 输出格式

```
🔧 代码生成：GET /api/v1/users/{id}

检测请求库：axios（封装文件：src/utils/request.ts）

━━━ 生成文件 ━━━

1. src/types/api/user.ts（类型定义）
2. src/api/user.ts（请求函数）

━━━ 预览 ━━━

// src/types/api/user.ts

/** 用户详情 - 响应类型 */
export interface UserDetailResponse {
  id: number;
  userName: string;
  avatarUrl?: string;
  email: string;
  createdAt: string;
  isActive?: boolean;
  roleList?: {
    roleId: number;
    roleName: string;
  }[];
}

// src/api/user.ts

import request from '@/utils/request';
import type { UserDetailResponse } from '@/types/api/user';

/** 获取用户详情 */
export function getUserDetail(id: number) {
  return request.get<UserDetailResponse>(`/api/v1/users/${id}`);
}
```

确认后写入文件。

### 不同请求库的生成风格

#### 自定义封装（检测到 src/utils/request.ts 等）

```typescript
import request from '@/utils/request';

/** 获取用户列表 */
export function getUserList(params?: UserListParams) {
  return request.get<UserListResponse>('/api/v1/users', { params });
}

/** 创建用户 */
export function createUser(data: CreateUserParams) {
  return request.post<CreateUserResponse>('/api/v1/users', data);
}
```

#### axios（package.json 中有 axios）

```typescript
import axios from 'axios';

/** 获取用户列表 */
export function getUserList(params?: UserListParams) {
  return axios.get<UserListResponse>('/api/v1/users', { params });
}
```

#### umi-request

```typescript
import { request } from 'umi';

/** 获取用户列表 */
export function getUserList(params?: UserListParams) {
  return request<UserListResponse>('/api/v1/users', { method: 'GET', params });
}
```

#### 原生 fetch

```typescript
/** 获取用户列表 */
export async function getUserList(params?: UserListParams): Promise<UserListResponse> {
  const query = params ? '?' + new URLSearchParams(params as any).toString() : '';
  const res = await fetch(`/api/v1/users${query}`);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}
```

#### @tanstack/react-query

```typescript
import { useQuery, useMutation } from '@tanstack/react-query';

/** 获取用户详情 */
export function useUserDetail(id: number) {
  return useQuery({
    queryKey: ['user', id],
    queryFn: async () => {
      const res = await fetch(`/api/v1/users/${id}`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      return res.json() as Promise<UserDetailResponse>;
    },
  });
}

/** 创建用户 */
export function useCreateUser() {
  return useMutation({
    mutationFn: async (data: CreateUserParams) => {
      const res = await fetch('/api/v1/users', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      return res.json() as Promise<CreateUserResponse>;
    },
  });
}
```

#### swr

```typescript
import useSWR from 'swr';

const fetcher = (url: string) => fetch(url).then(res => res.json());

/** 获取用户详情 */
export function useUserDetail(id: number) {
  return useSWR<UserDetailResponse>(`/api/v1/users/${id}`, fetcher);
}
```

### 批量生成

#### 按 Tag 批量生成

```
/api:gen --tag=用户管理

→ 生成该 Tag 下所有接口的类型和请求函数
→ 合并到同一个模块文件
```

#### 按路径通配

```
/api:gen * /api/v1/users
/api:gen * /api/v1/users/{id}

→ 生成该路径下所有 HTTP 方法的代码
```

### 文件合并策略

同一模块（如 user）的多个接口生成到同一文件：

```
/api:gen * /api/v1/users
/api:gen * /api/v1/users/{id}

→ src/types/api/user.ts   包含 UserListResponse, UserDetailResponse, CreateUserParams 等
→ src/api/user.ts          包含 getUserList, getUserDetail, createUser 等
```

**合并规则：**
- 同名 interface 已存在 → 覆盖（确认后）
- 同名函数已存在 → 覆盖（确认后）
- 新增的 → 追加到文件末尾
- import 语句自动去重
