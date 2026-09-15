#!/bin/bash
# validate-hooks.sh — PreToolUse Bash Hook（会话内首条 ssh 命令时校验完整性）
# 确保 Diag 所有 Hook 已注册且可执行，防止被人为禁用

INPUT=$(cat)
# shellcheck disable=SC1091
source "$(dirname "${BASH_SOURCE[0]}")/_common.sh"

# 只对含 ssh 的命令校验：风控链只管 ssh，其他 bash 直接放行（启用 diag 后所有项目的 Bash 都会经过这里）
# 子串匹配是 parse-ssh.py 识别范围的超集（nohup / env / timeout 包装同样命中），不会漏判
CMD=$(diag_read_command "$INPUT")
case "$CMD" in
    *ssh*) ;;
    *) exit 0 ;;
esac

# 会话内只校验一次。marker 只按会话 id 区分——不能带 $$，每次 Hook 调用都是新进程，带了等于每次都校验
# 取不到会话 id 时不写 marker，退化为每次校验
SESSION=$(printf '%s' "$INPUT" | jq -r '.session_id // empty')
SESSION="${SESSION:-${CLAUDE_SESSION_ID:-}}"
MARKER=""
if [ -n "$SESSION" ]; then
    RUNTIME_DIR="${DIAG_HOME:-$HOME/.claude-diag}/runtime"
    MARKER="$RUNTIME_DIR/validated-${SESSION//[^A-Za-z0-9-]/_}"
    [ -f "$MARKER" ] && exit 0
fi

HOOKS_DIR="$DIAG_PLUGIN_ROOT/hooks"
REQUIRED_HOOKS=(
    "sensitive-input-guard.sh"
    "host-whitelist.sh"
    "command-whitelist.sh"
    "write-guard.sh"
    "audit-log.sh"
)

MISSING=()
for h in "${REQUIRED_HOOKS[@]}"; do
    if [ ! -x "$HOOKS_DIR/$h" ]; then
        MISSING+=("$h(不可执行或缺失)")
    fi
done

if [ "${#MISSING[@]}" -gt 0 ]; then
    diag_deny "Diag 风控 Hook 完整性校验失败：$(IFS=,; echo "${MISSING[*]}")。请检查 plugins/diag/hooks/ 目录和文件权限。"
fi

HOOKS_JSON="$HOOKS_DIR/hooks.json"
if [ ! -f "$HOOKS_JSON" ]; then
    diag_deny "Diag hooks.json 未找到：$HOOKS_JSON"
fi

for h in "${REQUIRED_HOOKS[@]}"; do
    if ! grep -q "$h" "$HOOKS_JSON"; then
        diag_deny "Hook $h 未在 hooks.json 中注册，风控链可能被绕过。"
    fi
done

if [ -n "$MARKER" ]; then
    mkdir -p "$RUNTIME_DIR" 2>/dev/null || true
    # 顺手清理一天前的旧会话 marker（每个会话只走到这里一次，开销可忽略）
    find "$RUNTIME_DIR" -maxdepth 1 -name 'validated-*' -mtime +1 -delete 2>/dev/null || true
    touch "$MARKER" 2>/dev/null || true
fi
exit 0
