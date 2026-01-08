#!/bin/bash
# validate-requirement.sh
# 验证需求文档格式和完整性

FILE_PATH="$1"

if [ -z "$FILE_PATH" ]; then
    echo "⚠️ 未指定文件路径"
    exit 0
fi

if [ ! -f "$FILE_PATH" ]; then
    echo "⚠️ 文件不存在: $FILE_PATH"
    exit 0
fi

# 检查是否是需求文档
if [[ ! "$FILE_PATH" =~ REQ-[0-9]+ ]]; then
    exit 0
fi

echo "📋 验证需求文档: $(basename "$FILE_PATH")"

# 检查必要章节
MISSING=""

if ! grep -q "## 元信息" "$FILE_PATH"; then
    MISSING="$MISSING\n  - 元信息"
fi

if ! grep -q "## 一、需求描述" "$FILE_PATH"; then
    MISSING="$MISSING\n  - 需求描述"
fi

if ! grep -q "## 二、功能清单" "$FILE_PATH"; then
    MISSING="$MISSING\n  - 功能清单"
fi

if [ -n "$MISSING" ]; then
    echo -e "⚠️ 缺少章节:$MISSING"
else
    echo "✅ 文档格式正确"
fi
