#!/usr/bin/env python3
"""
parse-ssh.py — 从 bash 命令字符串中提取首个 ssh 段的主机和远程命令。

输入：stdin 读取完整 bash 命令
输出：stdout JSON {is_ssh, host, remote, error?}

原则：
- 只做 shlex 词法拆分 + 线性扫描，绝不 eval
- 不处理嵌套管道中的多个 ssh，只抓第一个
- 不处理 scp/rsync（本期只拦 ssh）
"""
import sys
import json
import shlex

OPTS_WITH_ARG = {
    "-b", "-B", "-c", "-D", "-E", "-e", "-F", "-I", "-i", "-J", "-L",
    "-l", "-m", "-O", "-o", "-p", "-Q", "-R", "-S", "-W", "-w",
}


def parse(cmd: str) -> dict:
    try:
        tokens = shlex.split(cmd, posix=True)
    except ValueError as e:
        return {"is_ssh": False, "error": f"shlex: {e}"}

    n = len(tokens)
    i = 0
    while i < n and tokens[i] != "ssh":
        i += 1

    if i >= n:
        return {"is_ssh": False}

    i += 1  # skip "ssh"

    # 跳过选项
    while i < n:
        t = tokens[i]
        if t == "--":
            i += 1
            break
        if not t.startswith("-"):
            break

        # 粘连形式 -p22 / -iKEY
        if len(t) > 2 and t[:2] in OPTS_WITH_ARG:
            i += 1
            continue
        if t in OPTS_WITH_ARG:
            i += 2
            continue
        # 未知 / 布尔短选项：保守视为无参
        i += 1

    if i >= n:
        return {"is_ssh": True, "error": "no_host"}

    host = tokens[i]
    remote_tokens = tokens[i + 1:]
    # 回拼 remote 时保留原有 quoting，便于下游 grep/eval 安全
    remote = " ".join(shlex.quote(t) for t in remote_tokens)

    return {"is_ssh": True, "host": host, "remote": remote}


if __name__ == "__main__":
    cmd = sys.stdin.read()
    sys.stdout.write(json.dumps(parse(cmd), ensure_ascii=False))
