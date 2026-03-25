#!/bin/bash
# parse-requirement.sh
# 解析需求文档，提取关键信息

FILE_PATH="$1"

if [ -z "$FILE_PATH" ] || [ ! -f "$FILE_PATH" ]; then
    echo "用法: parse-requirement.sh <需求文档路径>"
    exit 1
fi

# 提取需求编号
REQ_ID=$(basename "$FILE_PATH" | grep -oE 'REQ-[0-9]+')

# 提取标题（第一行 # 开头的内容）
TITLE=$(head -1 "$FILE_PATH" | sed 's/^# //')

# 提取状态
STATUS=$(grep -A5 "## 元信息" "$FILE_PATH" | grep "状态" | awk -F'|' '{print $3}' | xargs)

# 提取功能点数量
TOTAL_FEATURES=$(grep -c "\- \[ \]" "$FILE_PATH" 2>/dev/null || echo "0")
COMPLETED_FEATURES=$(grep -c "\- \[x\]" "$FILE_PATH" 2>/dev/null || echo "0")

# 输出 JSON 格式
cat << EOF
{
  "id": "$REQ_ID",
  "title": "$TITLE",
  "status": "$STATUS",
  "progress": {
    "total": $TOTAL_FEATURES,
    "completed": $COMPLETED_FEATURES
  }
}
EOF
