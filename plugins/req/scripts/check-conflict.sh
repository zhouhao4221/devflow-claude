#!/bin/bash
# check-conflict.sh
# 检测本地与缓存需求文档的冲突

LOCAL_FILE="$1"
CACHE_FILE="$2"

# 参数检查
if [ -z "$LOCAL_FILE" ] || [ -z "$CACHE_FILE" ]; then
    echo "用法: check-conflict.sh <本地文件路径> <缓存文件路径>"
    exit 1
fi

# 如果任一文件不存在，无冲突
if [ ! -f "$LOCAL_FILE" ] || [ ! -f "$CACHE_FILE" ]; then
    echo '{"conflict": false}'
    exit 0
fi

# 提取本地文件信息
LOCAL_STATUS=$(grep -A5 "## 元信息" "$LOCAL_FILE" | grep "状态" | awk -F'|' '{print $3}' | xargs)
LOCAL_COMPLETED=$(grep -c "\- \[x\]" "$LOCAL_FILE" 2>/dev/null || echo "0")
LOCAL_TOTAL=$(grep -c "\- \[ \]" "$LOCAL_FILE" 2>/dev/null || echo "0")
LOCAL_LAST_CHANGE=$(grep -A2 "## .*变更记录" "$LOCAL_FILE" | grep -E "^| [0-9]{4}-[0-9]{2}-[0-9]{2}" | head -1 | awk -F'|' '{print $2}' | xargs)

# 提取缓存文件信息
CACHE_STATUS=$(grep -A5 "## 元信息" "$CACHE_FILE" | grep "状态" | awk -F'|' '{print $3}' | xargs)
CACHE_COMPLETED=$(grep -c "\- \[x\]" "$CACHE_FILE" 2>/dev/null || echo "0")
CACHE_TOTAL=$(grep -c "\- \[ \]" "$CACHE_FILE" 2>/dev/null || echo "0")
CACHE_LAST_CHANGE=$(grep -A2 "## .*变更记录" "$CACHE_FILE" | grep -E "^| [0-9]{4}-[0-9]{2}-[0-9]{2}" | head -1 | awk -F'|' '{print $2}' | xargs)

# 检测冲突
CONFLICT=false
CONFLICT_FIELDS=""

if [ "$LOCAL_STATUS" != "$CACHE_STATUS" ]; then
    CONFLICT=true
    CONFLICT_FIELDS="status"
fi

if [ "$LOCAL_COMPLETED" != "$CACHE_COMPLETED" ] || [ "$LOCAL_TOTAL" != "$CACHE_TOTAL" ]; then
    CONFLICT=true
    if [ -n "$CONFLICT_FIELDS" ]; then
        CONFLICT_FIELDS="$CONFLICT_FIELDS,progress"
    else
        CONFLICT_FIELDS="progress"
    fi
fi

if [ "$LOCAL_LAST_CHANGE" != "$CACHE_LAST_CHANGE" ]; then
    CONFLICT=true
    if [ -n "$CONFLICT_FIELDS" ]; then
        CONFLICT_FIELDS="$CONFLICT_FIELDS,lastChange"
    else
        CONFLICT_FIELDS="lastChange"
    fi
fi

# 输出 JSON 格式
cat << EOF
{
  "conflict": $CONFLICT,
  "conflictFields": "$CONFLICT_FIELDS",
  "local": {
    "status": "$LOCAL_STATUS",
    "progress": "$LOCAL_COMPLETED/$((LOCAL_COMPLETED + LOCAL_TOTAL))",
    "lastChange": "$LOCAL_LAST_CHANGE"
  },
  "cache": {
    "status": "$CACHE_STATUS",
    "progress": "$CACHE_COMPLETED/$((CACHE_COMPLETED + CACHE_TOTAL))",
    "lastChange": "$CACHE_LAST_CHANGE"
  }
}
EOF
