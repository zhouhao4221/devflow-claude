# 公共逻辑参考

> 此文档定义所有命令共用的逻辑，各命令直接引用，避免重复。

## 存储路径解析

```
本地存储（主）: docs/requirements/
├── modules/      # 模块文档
├── active/       # 进行中需求
├── completed/    # 已完成需求
└── INDEX.md      # 索引

全局缓存（副）: ~/.claude-requirements/projects/<project>/
```

**解析规则**：
1. 读取 `.claude/settings.local.json` 的 `requirementProject`
2. 有值 → 使用全局缓存路径
3. 无值 → 使用本地 `docs/requirements/`

**写入策略**：先本地 → 后同步缓存

## 需求编号生成

扫描 active/ 和 completed/ 目录，找最大编号 +1，格式 `REQ-XXX`

## 状态流转

```
📝 草稿 → 👀 待评审 → ✅ 评审通过 → 🔨 开发中 → 🧪 测试中 → 🎉 已完成
```

## 元信息字段

| 字段 | 说明 |
|------|------|
| 编号 | REQ-XXX |
| 类型 | 后端/前端/全栈 |
| 状态 | 当前状态 |
| 模块 | 所属模块 |
| 关联需求 | 前后端对应需求 |
