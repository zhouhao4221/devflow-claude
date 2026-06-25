#!/usr/bin/env python3
"""gen-skills.py — 从 command 单源派生 skill（REQ-003）。

command（plugins/<p>/commands/<name>.md）是唯一权威源；据此生成对应
skill（plugins/<p>/skills/<name>/SKILL.md），保证两份永不漂移、且 skill
自包含（供不支持 slash 的 Claude 客户端读取）。

规则：① frontmatter 仅留 name+description；② command 引用的共享子文件
（_*.md / *-rationale.md，含传递依赖）去重内联为「附录」；③ 正文链接降级为
纯文本；④ helper skill（无同名 command）不处理。确定性：所有去重均按出现
顺序，避免 set 迭代顺序导致的不幂等。

用法：gen-skills.py [--check] [--plugin P] [--command C]
"""
import argparse
import os
import re
import sys

PLUGINS = ["req", "api", "pm", "diag", "uat"]
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SUBFILE_RE = re.compile(
    r"\[([^\]]*)\]\((?:\./)?((?:_[A-Za-z0-9_-]+|[A-Za-z0-9-]+-rationale)\.md)(#[^)]*)?\)"
)


def split_frontmatter(text):
    if text.startswith("---"):
        m = re.match(r"^---\s*\n(.*?)\n---\s*\n?(.*)$", text, re.S)
        if m:
            fm = {}
            for line in m.group(1).splitlines():
                km = re.match(r"^([A-Za-z_-]+):\s*(.*)$", line)
                if km:
                    fm[km.group(1)] = km.group(2).strip()
            return fm, m.group(2)
    return {}, text


def referenced_subfiles(body):
    seen, out = set(), []
    for m in SUBFILE_RE.finditer(body):
        if m.group(2) not in seen:
            seen.add(m.group(2))
            out.append(m.group(2))
    return out


def strip_links(text):
    return SUBFILE_RE.sub(lambda m: f"{m.group(1)}（见附录：{m.group(2)}）", text)


def transitive_closure(direct, commands_dir):
    ordered, seen, queue = [], set(), list(direct)
    while queue:
        name = queue.pop(0)
        if name in seen:
            continue
        path = os.path.join(commands_dir, name)
        if not os.path.isfile(path):
            continue
        seen.add(name)
        ordered.append(name)
        with open(path, encoding="utf-8") as f:
            for ref in referenced_subfiles(f.read()):
                if ref not in seen:
                    queue.append(ref)
    return ordered


def build_skill(cmd_path, commands_dir, name):
    with open(cmd_path, encoding="utf-8") as f:
        fm, body = split_frontmatter(f.read())
    parts = ["---", f"name: {fm.get('name', name).strip().strip(chr(34))}",
             f"description: {fm.get('description', '').strip().strip(chr(34))}",
             "---", "", strip_links(body).rstrip()]
    closure = transitive_closure(referenced_subfiles(body), commands_dir)
    if closure:
        parts += ["", "---", "", "# 附录（自动内联的共享约定）", "",
                  "> 以下内容由 command 引用的共享子文件自动内联，供不支持 slash 的 "
                  "Claude 客户端离线阅读。请勿手动编辑本文件——改动应在对应 command 进行。"]
        for sub in closure:
            with open(os.path.join(commands_dir, sub), encoding="utf-8") as f:
                _, sub_body = split_frontmatter(f.read())
            parts += ["", f"## 附录：{sub}", "", strip_links(sub_body).strip()]
    return "\n".join(parts).rstrip() + "\n"


def iter_commands(plugins, only_command):
    for p in plugins:
        cdir = os.path.join(ROOT, "plugins", p, "commands")
        if not os.path.isdir(cdir):
            continue
        for fn in sorted(os.listdir(cdir)):
            if not fn.endswith(".md") or fn.startswith("_"):
                continue
            name = fn[:-3]
            if only_command and name != only_command:
                continue
            yield p, name, os.path.join(cdir, fn), cdir, \
                os.path.join(ROOT, "plugins", p, "skills", name, "SKILL.md")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--plugin")
    ap.add_argument("--command")
    a = ap.parse_args()
    if a.plugin and a.plugin not in PLUGINS:
        print(f"未知插件: {a.plugin}", file=sys.stderr)
        return 2
    plugins = [a.plugin] if a.plugin else PLUGINS
    written, drifted, unchanged = [], [], 0
    for p, name, cmd, cdir, skill in iter_commands(plugins, a.command):
        new = build_skill(cmd, cdir, name)
        old = open(skill, encoding="utf-8").read() if os.path.isfile(skill) else ""
        if new == old:
            unchanged += 1
        elif a.check:
            drifted.append(f"{p}/{name}")
        else:
            os.makedirs(os.path.dirname(skill), exist_ok=True)
            open(skill, "w", encoding="utf-8").write(new)
            kb = round(len(new.encode("utf-8")) / 1024, 1)
            written.append(f"{p}/{name} ({kb}KB){'  WARN>30KB' if kb > 30 else ''}")
    if a.check:
        if drifted:
            print(f"[X] {len(drifted)} 个 skill 不一致: " + ", ".join(drifted))
            return 1
        print(f"[OK] 全部 {unchanged} 个 skill 与 command 一致")
        return 0
    for w in written:
        print(f"  + {w}")
    print(f"\n生成 {len(written)} 个，未变 {unchanged} 个。helper 未触碰。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
