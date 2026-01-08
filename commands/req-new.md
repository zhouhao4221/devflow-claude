---
description: 创建新需求 - 基于模板创建需求文档
---

# 创建新需求

基于模板创建新的需求文档，引导用户完成需求分析。

## 命令格式

```
/req new [需求标题]
```

---

## 执行流程

### 0. 解析需求路径

```bash
# 检查当前仓库绑定的项目
PROJECT=$(cat .claude/settings.local.json 2>/dev/null | jq -r '.requirementProject // empty')

if [ -n "$PROJECT" ]; then
    # 使用全局缓存路径
    REQ_ROOT=~/.claude-requirements/projects/$PROJECT
else
    # 回退到本地路径
    REQ_ROOT=docs/requirements
fi

REQ_ACTIVE=$REQ_ROOT/active
REQ_COMPLETED=$REQ_ROOT/completed
REQ_TEMPLATE=$REQ_ROOT/template.md
```

### 1. 生成需求编号

扫描现有需求文档，生成下一个编号：

```bash
# 获取最大编号
ls $REQ_ACTIVE/ $REQ_COMPLETED/ 2>/dev/null | grep -oE 'REQ-[0-9]+' | sort -t'-' -k2 -n | tail -1
```

新编号 = 最大编号 + 1，格式：REQ-XXX（三位数字，如 REQ-001）

### 2. 收集基本信息

如果未提供标题，询问用户：

**需要收集的信息：**
- 需求标题（必填）
- 优先级（P1/P2/P3，默认 P2）
- 负责人（可选）

### 3. 创建需求文档

从模板创建文件：`$REQ_ACTIVE/REQ-XXX-标题.md`

**初始化内容：**
- 填充元信息（编号、标题、状态=草稿、日期）
- 生命周期勾选「草稿」

### 4. 进入需求分析模式

引导用户完成需求分析，依次完善以下章节：

#### 4.1 需求描述
- 业务背景
- 用户价值
- 预期目标

#### 4.2 功能清单
将需求拆解为原子功能点：
- 每个功能点可独立开发
- 标注优先级和依赖关系

#### 4.3 业务规则
提取关键业务规则：
- 数据校验规则
- 状态转换规则
- 权限控制规则
- 边界条件

#### 4.4 数据模型（如涉及）
- 新增/修改表结构
- 字段定义
- 索引设计
- SQL 迁移脚本

#### 4.5 API 设计（如涉及）
遵循项目 RESTful 规范：
- 接口路径
- 请求/响应参数
- 错误码

#### 4.6 文件改动清单
基于项目结构评估：
- Model 层
- Store 层
- Biz 层
- Controller 层
- Router
- 其他

#### 4.7 实现步骤
生成标准化开发步骤：
1. 数据库变更
2. Model 层
3. Store 层
4. Biz 层
5. Controller 层
6. Router 注册
7. Swagger 文档
8. 测试验证

#### 4.8 测试要点
列出关键测试场景和预期结果。

### 5. 保存并提示

```
✅ 需求文档已创建：$REQ_ACTIVE/REQ-XXX-标题.md

📋 当前状态：📝 草稿

💡 下一步：
- 继续完善：/req edit REQ-XXX
- 提交评审：/req review REQ-XXX
```

---

## 注意事项

- 需求编号不复用已废弃的编号
- 标题使用中文，文件名使用编号+标题
- 创建后状态为「草稿」，需评审通过才能开发

## 用户输入

$ARGUMENTS