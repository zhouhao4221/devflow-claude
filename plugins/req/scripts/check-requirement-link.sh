#!/bin/bash
# check-requirement-link.sh
# 检查代码提交是否关联需求编号

# 获取待提交的文件
STAGED_FILES=$(git diff --cached --name-only 2>/dev/null)

if [ -z "$STAGED_FILES" ]; then
    exit 0
fi

# 检查是否有业务代码变更
HAS_CODE_CHANGES=false
for file in $STAGED_FILES; do
    if [[ "$file" =~ ^internal/ ]] || [[ "$file" =~ ^pkg/ ]]; then
        HAS_CODE_CHANGES=true
        break
    fi
done

if [ "$HAS_CODE_CHANGES" = true ]; then
    echo ""
    echo "💡 提示：检测到业务代码变更"
    echo "   建议在提交信息中关联需求编号"
    echo "   格式：feat(module): 描述 (REQ-XXX)"
    echo ""
fi
