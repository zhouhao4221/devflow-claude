---
description: 缓存管理 - 查看、清理全局需求缓存
---

# 缓存管理

管理全局需求缓存，支持查看、清理、重建等操作。

## 命令格式

```
/req cache <action> [project-name]
```

## 子命令

| 子命令 | 说明 | 示例 |
|-------|------|------|
| `info` | 查看缓存信息 | `/req cache info` |
| `clear` | 清理缓存 | `/req cache clear my-project` |
| `clear-all` | 清理所有缓存 | `/req cache clear-all` |
| `rebuild` | 重建索引 | `/req cache rebuild` |
| `export` | 导出需求 | `/req cache export my-project` |

---

## /req cache info

显示全局缓存状态。

### 执行流程

```bash
CACHE_PATH=~/.claude-requirements

# 检查缓存是否存在
if [ ! -d "$CACHE_PATH" ]; then
    echo "📭 全局缓存未初始化"
    echo "💡 使用 /req init <project-name> 创建第一个项目"
    exit 0
fi

# 统计信息
TOTAL_PROJECTS=$(ls $CACHE_PATH/projects/ 2>/dev/null | wc -l)
TOTAL_SIZE=$(du -sh $CACHE_PATH 2>/dev/null | cut -f1)
```

### 输出

```
📁 全局需求缓存信息

路径: ~/.claude-requirements/
大小: 1.2 MB
项目数: 3

📊 项目统计:
| 项目 | 活跃 | 已完成 | 大小 | 关联仓库 |
|------|------|--------|------|---------|
| my-saas-product | 5 | 12 | 500 KB | 2 |
| internal-tools | 2 | 8 | 300 KB | 1 |
| client-portal | 0 | 0 | 50 KB | 0 |

📌 当前仓库绑定: my-saas-product

💡 可用操作:
- /req cache clear <project>  清理指定项目
- /req cache clear-all        清理所有缓存
- /req cache export <project> 导出项目需求
```

---

## /req cache clear <project-name>

清理指定项目的缓存。

### 执行流程

```bash
PROJECT_PATH=~/.claude-requirements/projects/<project-name>

# 检查项目是否存在
if [ ! -d "$PROJECT_PATH" ]; then
    echo "❌ 项目不存在: <project-name>"
    exit 1
fi

# 统计将删除的内容
ACTIVE_COUNT=$(ls $PROJECT_PATH/active/*.md 2>/dev/null | wc -l)
COMPLETED_COUNT=$(ls $PROJECT_PATH/completed/*.md 2>/dev/null | wc -l)
```

### 确认提示

```
⚠️ 即将删除项目: <project-name>

📊 将删除的内容:
- 活跃需求: X 个
- 已完成需求: Y 个
- 模板文件: 1 个

🔗 关联仓库 (将自动解绑):
- /Users/xxx/backend
- /Users/xxx/frontend

⚠️ 此操作不可恢复！

确认删除？请输入项目名称以确认:
```

### 执行删除

```bash
# 删除项目目录
rm -rf $PROJECT_PATH

# 更新全局索引
# 从 index.json 移除项目记录

# 清理关联仓库的绑定配置
# 遍历 index.json 中记录的仓库，删除其 .claude/settings.local.json 中的 requirementProject
```

### 输出

```
✅ 项目 "<project-name>" 已删除

📊 已清理:
- 需求文档: X 个
- 释放空间: XXX KB

🔗 以下仓库的绑定已自动解除:
- /Users/xxx/backend
- /Users/xxx/frontend

💡 这些仓库现在将使用本地模式 (docs/requirements/)
```

---

## /req cache clear-all

清理所有全局缓存。

### 确认提示

```
🚨 危险操作：清理所有全局缓存

📊 将删除的内容:
- 项目数: 3 个
- 总需求: 27 个
- 总大小: 1.2 MB

项目列表:
- my-saas-product (17 个需求, 2 个关联仓库)
- internal-tools (10 个需求, 1 个关联仓库)
- client-portal (0 个需求, 0 个关联仓库)

⚠️ 此操作将删除所有项目和需求文档，不可恢复！

确认删除？请输入 "DELETE ALL" 以确认:
```

### 执行

```bash
# 删除整个缓存目录
rm -rf ~/.claude-requirements

# 清理所有关联仓库的绑定配置
```

### 输出

```
✅ 全局缓存已清理

📊 已删除:
- 项目: 3 个
- 需求文档: 27 个
- 释放空间: 1.2 MB

💡 所有仓库现在将使用本地模式
💡 使用 /req init <project-name> 重新创建项目
```

---

## /req cache rebuild

重建全局索引文件。

### 使用场景

- 索引文件损坏
- 手动修改了缓存目录
- 需要同步实际文件状态

### 执行流程

```bash
CACHE_PATH=~/.claude-requirements

# 扫描所有项目
for project in $CACHE_PATH/projects/*/; do
    project_name=$(basename $project)

    # 统计需求数量
    active_count=$(ls $project/active/*.md 2>/dev/null | wc -l)
    completed_count=$(ls $project/completed/*.md 2>/dev/null | wc -l)

    # 更新索引
done

# 重建 index.json
```

### 输出

```
🔄 重建全局索引

扫描项目: 3 个
├── my-saas-product: 5 活跃, 12 已完成
├── internal-tools: 2 活跃, 8 已完成
└── client-portal: 0 活跃, 0 已完成

✅ 索引重建完成

📁 索引文件: ~/.claude-requirements/index.json
```

---

## /req cache export <project-name>

导出项目需求到本地目录。

### 执行流程

```bash
PROJECT_PATH=~/.claude-requirements/projects/<project-name>
EXPORT_PATH=./requirements-export-<project-name>-<date>

# 创建导出目录
mkdir -p $EXPORT_PATH

# 复制所有文件
cp -r $PROJECT_PATH/* $EXPORT_PATH/
```

### 输出

```
✅ 导出完成

📁 导出路径: ./requirements-export-my-saas-product-2026-01-08/
📊 导出内容:
- 活跃需求: 5 个
- 已完成需求: 12 个
- 模板文件: 1 个

💡 可用于备份或分享给团队成员
```

---

## 错误处理

| 错误场景 | 处理方式 |
|---------|---------|
| 缓存不存在 | 提示使用 `/req init` |
| 项目不存在 | 列出可用项目 |
| 权限不足 | 提示检查目录权限 |
| 索引损坏 | 建议执行 `/req cache rebuild` |

## 用户输入

$ARGUMENTS
