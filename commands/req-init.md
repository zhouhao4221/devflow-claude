---
description: 初始化需求项目 - 创建新项目或绑定当前仓库到已有项目
---

# 初始化需求项目

在全局缓存中创建新项目，或将当前仓库绑定到已有项目。

## 命令格式

```
/req init <project-name>
```

## 参数

- `project-name`: 项目名称（建议使用 kebab-case，如 `my-saas-product`）

---

## 执行流程

### 1. 解析参数

```
项目名称: $ARGUMENTS
全局缓存路径: ~/.claude-requirements
```

### 2. 检查全局缓存目录

```bash
# 确保全局缓存目录存在
mkdir -p ~/.claude-requirements/projects
```

### 3. 检查项目是否已存在

```bash
ls ~/.claude-requirements/projects/
```

**如果项目已存在**：
- 提示用户项目已存在
- 询问是否要绑定当前仓库到该项目

**如果项目不存在**：
- 创建新项目目录结构

### 4. 创建项目目录结构（新项目）

```bash
PROJECT_PATH=~/.claude-requirements/projects/<project-name>

mkdir -p $PROJECT_PATH/active
mkdir -p $PROJECT_PATH/completed
```

### 5. 复制模板文件

从插件模板目录复制到项目目录：

```bash
cp <plugin-path>/templates/requirement-template.md $PROJECT_PATH/template.md
```

### 6. 更新全局索引

更新 `~/.claude-requirements/index.json`：

```json
{
  "projects": {
    "<project-name>": {
      "created": "2026-01-08",
      "repos": []
    }
  }
}
```

### 7. 绑定当前仓库

在当前仓库创建/更新配置文件 `.claude/settings.local.json`：

```json
{
  "requirementProject": "<project-name>"
}
```

同时更新全局索引，添加仓库路径：

```json
{
  "projects": {
    "<project-name>": {
      "created": "2026-01-08",
      "repos": [
        "/path/to/current/repo"
      ]
    }
  }
}
```

### 8. 输出结果

**新项目创建成功**：
```
✅ 项目 "<project-name>" 创建成功！

📁 项目路径: ~/.claude-requirements/projects/<project-name>/
📂 结构:
   ├── active/      # 进行中的需求
   ├── completed/   # 已完成的需求
   └── template.md  # 需求模板

🔗 当前仓库已绑定到此项目

💡 下一步:
   - /req new <标题>  创建新需求
   - /req             查看需求列表
```

**绑定已有项目成功**：
```
✅ 当前仓库已绑定到项目 "<project-name>"

📊 项目状态:
   - 活跃需求: X 个
   - 已完成: Y 个
   - 关联仓库: Z 个

💡 使用 /req 查看需求列表
```

---

## 错误处理

| 错误场景 | 处理方式 |
|---------|---------|
| 未提供项目名 | 提示：请提供项目名称，如 `/req init my-project` |
| 项目名包含非法字符 | 提示：项目名只能包含字母、数字、连字符 |
| 权限不足 | 提示：无法创建目录，请检查 ~/.claude-requirements 权限 |

---

## 用户输入

$ARGUMENTS
