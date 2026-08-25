#!/bin/bash
# session-context.sh
# SessionStart Hook：在会话启动时自动加载当前需求上下文
#
# 加载内容：
#   1. 项目绑定信息（requirementProject / requirementRole / requirementsDir）
#   2. 当前分支名推断出的需求编号
#   3. 对应需求的状态、标题、模块
#   4. 进行中的需求总数
#
# 配置事实源：`.devflow/settings.json` + `.devflow/settings.local.json`（local 覆盖同名字段）。
# 只认 `.devflow/`，不回退 `.claude/`；检测到 `.claude/` 还留着 DevFlow 字段时打印迁移提示。
#
# 输出格式：stdout 纯文本，会作为 additionalContext 注入到会话

set -e

# 仅在 git 仓库内执行
if ! git rev-parse --git-dir >/dev/null 2>&1; then
    exit 0
fi

REPO_ROOT=$(git rev-parse --show-toplevel 2>/dev/null)
if [ -z "$REPO_ROOT" ]; then
    exit 0
fi

cd "$REPO_ROOT"

# 读不到配置时宁可不输出，也不谎报「尚未初始化」
if ! command -v python3 >/dev/null 2>&1; then
    exit 0
fi

# ============ 1. 读取项目绑定 ============
PROJECT_NAME=""
PROJECT_ROLE=""
REQ_ROOT=""
HAS_BRANCH_STRATEGY=""
SOURCE_ERROR=""
LEGACY_CONFIG=""

CONFIG_TSV=$(python3 - <<'PY' 2>/dev/null || true
import json, os

DEVFLOW_KEYS = ('requirementProject', 'requirementRole', 'requirementsDir',
                'branchStrategy', 'requirementSource')
DEFAULT_DIR = 'docs/requirements'


def load(path):
    try:
        with open(path, encoding='utf-8') as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def merged(root=''):
    """.devflow/settings.json 打底，settings.local.json 覆盖同名字段"""
    cfg = {}
    for name in ('settings.json', 'settings.local.json'):
        cfg.update(load(os.path.join(root, '.devflow', name)))
    return cfg


cfg = merged()

if not cfg.get('requirementProject'):
    # 未绑定：区分「从没初始化」和「v2.x 配置还留在 .claude/ 没迁移」
    legacy = {}
    for name in ('settings.json', 'settings.local.json'):
        legacy.update(load(os.path.join('.claude', name)))
    if any(legacy.get(k) for k in DEVFLOW_KEYS):
        print('legacy\t1')
    raise SystemExit(0)

role = cfg.get('requirementRole') or 'primary'
req_root = ''
source_error = ''

if role == 'readonly':
    # readonly 无本地需求目录：经 requirementSource.path 直读主仓，
    # 目录名以主仓自己的 requirementsDir 为准
    source = cfg.get('requirementSource')
    path = source.get('path') if isinstance(source, dict) else ''
    if not path or not os.path.isdir(path):
        source_error = '1'
    else:
        req_root = os.path.join(path, merged(path).get('requirementsDir') or DEFAULT_DIR)
else:
    req_root = cfg.get('requirementsDir') or DEFAULT_DIR

print('project\t' + str(cfg.get('requirementProject')))
print('role\t' + role)
print('reqroot\t' + req_root)
print('branch_strategy\t' + ('1' if cfg.get('branchStrategy') else ''))
print('source_error\t' + source_error)
PY
)

while IFS=$'\t' read -r key value; do
    case "$key" in
        project)         PROJECT_NAME="$value" ;;
        role)            PROJECT_ROLE="$value" ;;
        reqroot)         REQ_ROOT="$value" ;;
        branch_strategy) HAS_BRANCH_STRATEGY="$value" ;;
        source_error)    SOURCE_ERROR="$value" ;;
        legacy)          LEGACY_CONFIG="$value" ;;
    esac
done <<< "$CONFIG_TSV"

# 旧布局残留 → 提示迁移
if [ -n "$LEGACY_CONFIG" ]; then
    echo "# DevFlow 需求工作流 · 配置待迁移 ⚠️"
    echo ""
    echo "检测到 DevFlow 配置仍在 \`.claude/settings.json(.local)\`，v3 起只读 \`.devflow/\`，当前配置不生效。"
    echo ""
    echo "执行 \`/req:migrate\` 把 DevFlow 字段搬到 \`.devflow/\`（密钥进 \`settings.local.json\`）。"
    exit 0
fi

# 未绑定项目 → 输出欢迎引导
if [ -z "$PROJECT_NAME" ]; then
    echo "# DevFlow 需求工作流 · 欢迎使用 🎉"
    echo ""
    echo "当前仓库尚未初始化。只需两步即可开始："
    echo ""
    echo "1. \`/req:init <project-name>\` — 初始化需求项目（创建 \`docs/requirements/\`、生成 PRD、绑定仓库）"
    echo "2. \`/req:branch init\` — 配置分支策略（GitHub Flow / Git Flow / Trunk-Based）"
    echo ""
    echo "💡 完成后即可 \`/req:new <标题>\` 创建第一个需求。输入 \`/req:help\` 查看完整教程。"
    exit 0
fi

# ============ 2. 当前分支 → 需求编号 ============
BRANCH=$(git symbolic-ref --short HEAD 2>/dev/null || echo "")
REQ_ID=""

if [ -n "$BRANCH" ]; then
    # 匹配 feat/REQ-123-xxx、fix/QUICK-045-xxx 等
    REQ_ID=$(echo "$BRANCH" | grep -oE '(REQ|QUICK)-[0-9]+' | head -1)
fi

# ============ 3. 读取需求文档 ============
REQ_TITLE=""
REQ_STATUS=""
REQ_MODULE=""
REQ_FILE=""

# 从元信息表提取字段值，兼容 `| 模块 | xxx |` 与 `模块: xxx` 两种格式
extract_meta() {
    local file="$1" label="$2" line
    line=$(grep -m1 -E "^[[:space:]]*\|?[[:space:]]*($label)[[:space:]]*[|:：]" "$file" 2>/dev/null | head -1)
    [ -n "$line" ] || return 0
    case "$(printf '%s' "$line" | sed 's/^[[:space:]]*//')" in
        \|*) printf '%s\n' "$line" | awk -F'|' '{gsub(/^[[:space:]]+|[[:space:]]+$/, "", $3); print $3}' ;;
        *)   printf '%s\n' "$line" | sed -E 's/^[^:：]*[:：][[:space:]]*//; s/[[:space:]]+$//' ;;
    esac
}

find_req_file() {
    local id="$1"
    [ -n "$REQ_ROOT" ] && [ -d "$REQ_ROOT" ] || return 0
    find "$REQ_ROOT/active" "$REQ_ROOT/completed" -maxdepth 1 -type f -name "${id}-*.md" 2>/dev/null | head -1
}

if [ -n "$REQ_ID" ]; then
    REQ_FILE=$(find_req_file "$REQ_ID")
    if [ -n "$REQ_FILE" ] && [ -f "$REQ_FILE" ]; then
        # 提取元信息（兼容 | 状态 | xxx | 或 状态: xxx 两种格式）
        REQ_TITLE=$(grep -m1 '^# ' "$REQ_FILE" | sed 's/^# //' | sed "s/${REQ_ID}[:： ]*//" )
        REQ_STATUS=$(grep -m1 -E '(状态|Status)' "$REQ_FILE" | grep -oE '(草稿|待评审|评审通过|开发中|测试中|已完成|Draft|Review|Approved|InProgress|Testing|Done)' | head -1)
        REQ_MODULE=$(extract_meta "$REQ_FILE" '模块|Module')
    fi
fi

# ============ 4. 进行中需求数量 ============
ACTIVE_COUNT=0
if [ -n "$REQ_ROOT" ] && [ -d "$REQ_ROOT/active" ]; then
    ACTIVE_COUNT=$(find "$REQ_ROOT/active" -maxdepth 1 -type f -name '*.md' 2>/dev/null | wc -l | tr -d ' ')
fi

# ============ 5. 输出 system-reminder ============
echo "# DevFlow 需求上下文"
echo ""
echo "- 项目：\`$PROJECT_NAME\` (${PROJECT_ROLE:-primary})"
echo "- 分支：\`${BRANCH:-<detached>}\`"

if [ -n "$SOURCE_ERROR" ]; then
    echo "- ⚠️ 只读仓库未绑定主仓（\`requirementSource.path\` 缺失或路径不存在），执行 \`/req:use <primary-repo-path>\` 重新绑定"
elif [ -n "$REQ_ID" ]; then
    if [ -n "$REQ_FILE" ]; then
        echo "- 当前需求：**$REQ_ID** ${REQ_TITLE}"
        [ -n "$REQ_STATUS" ] && echo "  - 状态：$REQ_STATUS"
        [ -n "$REQ_MODULE" ] && echo "  - 模块：$REQ_MODULE"
        echo "  - 文档：\`$REQ_FILE\`"
    else
        echo "- 当前分支指向 **$REQ_ID**，但未找到需求文档（可能已归档或未创建）"
    fi
else
    echo "- 当前不在需求分支上"
fi

if [ -z "$SOURCE_ERROR" ]; then
    echo "- 进行中需求：$ACTIVE_COUNT 条"
fi

if [ -z "$HAS_BRANCH_STRATEGY" ]; then
    echo ""
    echo "⚠️ 尚未配置分支策略，建议执行 \`/req:branch init\` 选择分支模型（GitHub Flow / Git Flow / Trunk-Based）"
fi

echo ""
echo "💡 可用命令：\`/req\` 列表 · \`/req:status\` 详情 · \`/req:dev\` 继续开发"
