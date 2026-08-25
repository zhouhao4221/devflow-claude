#!/bin/bash
# validate-requirement.sh
# 验证需求文档格式和完整性
# 由 PostToolUse Hook 触发（Write/Edit 工具操作后）
#
# 仅对需求目录下的需求文档（REQ-XXX、QUICK-XXX）进行验证
# 需求目录取 .devflow 配置的 requirementsDir，省略时默认 docs/requirements
# 根据需求类型检查对应模板的所有必须章节

# 从 stdin JSON 中提取文件路径（PostToolUse hook 通过 stdin 传入工具信息）
INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty')

# 空路径或文件不存在，静默跳过
if [ -z "$FILE_PATH" ] || [ ! -f "$FILE_PATH" ]; then
    exit 0
fi

# 仅处理需求目录下的文件（requirementsDir 可配置，不能写死 docs/requirements）
REPO_ROOT=$(git rev-parse --show-toplevel 2>/dev/null || echo ".")
REQ_DIR="docs/requirements"
if command -v python3 >/dev/null 2>&1; then
    CONFIGURED=$(python3 - "$REPO_ROOT" <<'PY' 2>/dev/null || true
import json, os, sys

cfg = {}
for name in ('settings.json', 'settings.local.json'):
    try:
        with open(os.path.join(sys.argv[1], '.devflow', name), encoding='utf-8') as f:
            data = json.load(f)
        if isinstance(data, dict):
            cfg.update(data)
    except Exception:
        pass
print((cfg.get('requirementsDir') or '').strip().strip('/'))
PY
)
    [ -n "$CONFIGURED" ] && REQ_DIR="$CONFIGURED"
fi

case "$FILE_PATH" in
    "$REQ_DIR"/*|*"/$REQ_DIR"/*) ;;
    *) exit 0 ;;
esac

FILENAME=$(basename "$FILE_PATH")

# 正式需求 REQ-XXX：验证完整模板章节
if [[ "$FILENAME" =~ ^REQ-[0-9]+ ]]; then
    echo "验证需求文档: $FILENAME"

    MISSING=""

    # 元信息和生命周期
    grep -q "## 元信息" "$FILE_PATH" || MISSING="$MISSING\n  - 元信息"
    grep -q "## 生命周期" "$FILE_PATH" || MISSING="$MISSING\n  - 生命周期"

    # 需求定义章节（一 ~ 六）
    grep -q "## 一、需求描述" "$FILE_PATH" || MISSING="$MISSING\n  - 一、需求描述"
    grep -q "## 二、功能清单" "$FILE_PATH" || MISSING="$MISSING\n  - 二、功能清单"
    grep -q "## 三、业务规则" "$FILE_PATH" || MISSING="$MISSING\n  - 三、业务规则"
    grep -q "## 四、使用场景" "$FILE_PATH" || MISSING="$MISSING\n  - 四、使用场景"
    grep -q "## 五、数据与交互" "$FILE_PATH" || MISSING="$MISSING\n  - 五、数据与交互"
    grep -q "## 六、测试要点" "$FILE_PATH" || MISSING="$MISSING\n  - 六、测试要点"

    # 图示章节（七，可选，不做强制校验）

    # 流程章节（八 ~ 十）
    grep -q "## 八、评审记录" "$FILE_PATH" || MISSING="$MISSING\n  - 八、评审记录"
    grep -q "## 九、变更记录" "$FILE_PATH" || MISSING="$MISSING\n  - 九、变更记录"
    grep -q "## 十、关联信息" "$FILE_PATH" || MISSING="$MISSING\n  - 十、关联信息"

    # 实现方案章节（十一，dev 阶段填充）
    grep -q "## 十一、实现方案" "$FILE_PATH" || MISSING="$MISSING\n  - 十一、实现方案"

    if [ -n "$MISSING" ]; then
        echo -e "缺少章节:$MISSING"
        echo "请严格按照模板格式补全所有章节（参考 $REQ_DIR/templates/requirement-template.md）"
    fi
fi

# 快速修复 QUICK-XXX：验证简化模板章节
if [[ "$FILENAME" =~ ^QUICK-[0-9]+ ]]; then
    echo "验证快速需求文档: $FILENAME"

    MISSING=""

    grep -q "## 元信息" "$FILE_PATH" || MISSING="$MISSING\n  - 元信息"
    grep -q "## 生命周期" "$FILE_PATH" || MISSING="$MISSING\n  - 生命周期"
    grep -q "## 问题描述" "$FILE_PATH" || MISSING="$MISSING\n  - 问题描述"
    grep -q "## 实现方案" "$FILE_PATH" || MISSING="$MISSING\n  - 实现方案"
    grep -q "## 验证方式" "$FILE_PATH" || MISSING="$MISSING\n  - 验证方式"
    grep -q "## 开发记录" "$FILE_PATH" || MISSING="$MISSING\n  - 开发记录"

    if [ -n "$MISSING" ]; then
        echo -e "缺少章节:$MISSING"
        echo "请严格按照模板格式补全所有章节（参考 quick-template.md）"
    fi
fi
