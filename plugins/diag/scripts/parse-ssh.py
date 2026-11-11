#!/usr/bin/env python3
"""
parse-ssh.py — 从 bash 命令字符串中提取首个 ssh 段的主机和远程命令。

输入：stdin 读取完整 bash 命令
输出：stdout JSON {is_ssh, host, remote, error?}

原则：
- 只做 shlex 词法拆分 + 线性扫描，绝不 eval
- 失败即拦截：确定是单个 ssh 调用才给 host/remote，确定没有 ssh 才 is_ssh=false，
  其余（多个 ssh、xargs/sudo/管道给 shell、解析失败）返回 ambiguous，Hook 据此拒绝
- 使用 punctuation_chars 让 shell 分隔符（| & ;）成为独立 token，
  正确区分"本地管道"和"SSH 远程命令"：
    `ssh host cmd | head` 的 `| head` 属于本地，不纳入 remote。
- 不处理 scp/rsync（本期只拦 ssh）
"""
import sys
import json
import re
import shlex

OPTS_WITH_ARG = {
    "-b", "-B", "-c", "-D", "-E", "-e", "-F", "-I", "-i", "-J", "-L",
    "-l", "-m", "-O", "-o", "-p", "-Q", "-R", "-S", "-W", "-w",
}

PUNCT = "|&;()`\n"   # 换行、子 shell、命令替换、反引号都切段，防止把第二条命令藏进去

# 已知本地包装器 / shell 关键字，允许出现在 ssh 之前而不影响 ssh 的识别
# (例: `nohup ssh host cmd`、`env FOO=bar ssh ...`、`timeout 60 ssh ...`、`if ssh ...; then`)
# sudo / su / doas 等提权工具不在此列：前缀不安全 → 落到「提及 ssh」兜底，判为无法确定
SAFE_WRAPPERS = {
    "nohup", "exec", "setsid", "time", "chronic",
    "env", "timeout", "nice", "ionice", "taskset",
    "stdbuf", "tsp", "command", "builtin",
    "if", "then", "else", "elif", "do", "while", "until", "!", "{", "}", "$",
}

# 只读、不会执行参数的本地命令：整条命令只由它们组成时，提到 ssh 不算调用
# （`grep ssh file`、`man ssh`、`which ssh`、`echo "用 ssh 登录" | head`）
BENIGN = {
    "grep", "egrep", "fgrep", "zgrep", "rg", "ag", "ack", "man", "info",
    "which", "whereis", "type", "apropos", "whatis", "echo", "printf",
    "cat", "less", "more", "head", "tail", "ls", "file", "stat", "wc",
    "sort", "uniq", "cut", "tr", "nl", "column", "locate",
}

SHELLS = {"bash", "sh", "zsh", "dash", "ksh", "fish"}

# 词元里出现独立的 ssh 词（含 /usr/bin/ssh 这类路径）；ssh-keygen、ssh://、/etc/ssh/x 不算
SSH_WORD = re.compile(r"(?:^|[\s;&|(`'\"])(?:[^\s'\"]*/)?ssh(?=$|[\s;&|)`'\"])")
MAX_DEPTH = 3


def _basename(tok):
    return tok.rsplit("/", 1)[-1]


def _is_safe_prefix(tokens):
    """判断 ssh 之前的 tokens 是否全部是安全包装器 / 环境变量赋值 / 选项 / 数值参数。

    True  → 可以把 ssh 当作命令动词
    False → 前缀里有未知命令（`grep ssh file` / `man ssh` 不是 ssh 调用，交给提及兜底）
    """
    for t in tokens:
        if t in SAFE_WRAPPERS:
            continue
        if t.startswith("-"):
            continue
        # 环境变量赋值 VAR=value
        if "=" in t and not t.startswith("="):
            name = t.split("=", 1)[0]
            if name and name[0].isalpha() and all(c.isalnum() or c == "_" for c in name):
                continue
        # 数值参数 (如 timeout 60 / nice 10)
        if t.replace(".", "", 1).isdigit():
            continue
        return False
    return True


def _verb(seg):
    """段内第一个不是安全前缀的词元（命令动词），取 basename。"""
    for idx, t in enumerate(seg):
        if not _is_safe_prefix([t]):
            return idx, _basename(t)
    return None, None


def _ambiguous(reason):
    return {"is_ssh": True, "ambiguous": True, "error": reason}


def _tokenize(cmd):
    lex = shlex.shlex(cmd, posix=True, punctuation_chars=PUNCT)
    lex.whitespace = " \t\r"
    lex.whitespace_split = True
    return list(lex)


def _split(tokens):
    segments, cur = [], []
    for t in tokens:
        if t and all(c in PUNCT for c in t):
            segments.append(cur)
            cur = []
        else:
            cur.append(t)
    segments.append(cur)
    return [s for s in segments if s]


def _parse_invocation(seg, start):
    i = start + 1  # skip "ssh"
    while i < len(seg):
        t = seg[i]
        if t == "--":
            i += 1
            break
        if not t.startswith("-"):
            break
        if len(t) > 2 and t[:2] in OPTS_WITH_ARG:
            i += 1
            continue
        if t in OPTS_WITH_ARG:
            i += 2
            continue
        i += 1  # 布尔或未知短选项

    if i >= len(seg):
        return {"is_ssh": True, "error": "no_host"}

    result = {"is_ssh": True, "host": seg[i], "remote": " ".join(seg[i + 1:])}
    if start > 0:
        result["local_prefix"] = " ".join(seg[:start])
    return result


def parse(cmd: str, depth: int = 0) -> dict:
    """失败即拦截：确定是单个 ssh 调用才给出 host/remote；
    确定没有 ssh 才返回 is_ssh=false；其余一律 ambiguous（is_ssh=true、无 host，Hook 会拒绝）。"""
    mentions = bool(SSH_WORD.search(cmd))
    try:
        tokens = _tokenize(cmd)
    except ValueError as e:
        return _ambiguous(f"shlex: {e}") if mentions else {"is_ssh": False, "error": f"shlex: {e}"}

    segments = _split(tokens)
    invocations, others = [], False   # invocations: (段下标, ssh 下标) 或 ("inner", 结果)
    for n, seg in enumerate(segments):
        idx, verb = _verb(seg)
        if verb is None:
            continue
        if verb == "ssh":
            # `command -v ssh` 是查询不是调用
            if not ("command" in seg[:idx] and any(t in ("-v", "-V") for t in seg[:idx])):
                invocations.append((n, idx))
            continue
        if verb in SHELLS or verb == "eval":
            rest = seg[idx + 1:]
            script = None
            if verb == "eval":
                script = " ".join(rest)
            else:
                for j, t in enumerate(rest):
                    if t.startswith("-") and not t.startswith("--") and "c" in t[1:]:
                        script = rest[j + 1] if j + 1 < len(rest) else ""
                        break
            if script is not None:
                if depth >= MAX_DEPTH:
                    if SSH_WORD.search(script):
                        return _ambiguous("嵌套 shell 层数过多")
                    continue
                inner = parse(script, depth + 1)
                if inner.get("ambiguous"):
                    return inner
                if inner.get("is_ssh"):
                    invocations.append(("inner", inner))
                continue
            others = True  # 从 stdin 读脚本的 shell：内容无法静态确定
            continue
        if verb not in BENIGN:
            others = True

    if len(invocations) > 1:
        return _ambiguous("一条命令里有多个 ssh 调用，请拆开逐条执行")
    if len(invocations) == 1:
        n, idx = invocations[0]
        if n == "inner":
            return idx
        # 调用之外还有可执行任意内容的段又提到 ssh（如 `ssh ok tail; echo 'ssh evil rm' | bash`）
        rest = " ".join(t for m, seg in enumerate(segments) if m != n for t in seg)
        if others and SSH_WORD.search(rest):
            return _ambiguous("ssh 调用之外的命令也涉及 ssh，无法确定实际执行的远程命令")
        return _parse_invocation(segments[n], idx)

    if mentions and others:
        return _ambiguous("命令以无法静态确认的方式涉及 ssh（如 xargs / sudo / 管道给 shell），请改为直接 ssh <host> <只读命令>")
    return {"is_ssh": False}


if __name__ == "__main__":
    cmd = sys.stdin.read()
    sys.stdout.write(json.dumps(parse(cmd), ensure_ascii=False))
