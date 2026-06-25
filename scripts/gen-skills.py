#!/usr/bin/env python3
"""gen-skills.py — 从 command 单源派生 skill（REQ-003）。

command（plugins/<p>/commands/<name>.md）是唯一权威源；本脚本据此生成
对应的 skill（plugins/<p>/skills/<name>/SKILL.md），保证两份永不漂移、
且 skill 自包含（供不支持 slash 的 Claude 客户端读取，无外部文件依赖）。

转换规则：
  1. frontmatter 降级：仅保留 name + description，去除 model/allowed-tools/argument-hint。
  2. 子文件传递内联：command 正文引用的共享子文件（_*.md / *-rationale.md），
     连同它们之间的相互引用，做传递闭包收集，去重后作为「附录」章节内联。
  3. 正文中所有子文件链接 [text](./_x.md#a) 降级为纯文本并提示「见附录」。
  4. helper skill（无同名 command）不处理。

用法：
  gen-skills.py                   全量生成，写入 skills/
  gen-skills.py --check           只比对，报漂移清单，不写文件（有差异则非零退出）
  gen-skills.py --plugin req      只处理某插件
  gen-skills.py --plugin req --command commit   只处理某命令
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
    return {m.group(2) for m in SUBFILE_RE.finditer(body)}


def strip_links(text):
    def repl(m):
        return f"{m.group(1)}（见附录：{m.group(2)}）"
    return SUBFILE_RE.sub(repl, text)


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
            sub_body = f.read()
        for ref in referenced_subfiles(sub_body):
            if ref not in seen:
                queue.append(ref)
    return ordered


def build_skill(cmd_path, commands_dir, name):
    with open(cmd_path, encoding="utf-8") as f:
        raw = f.read()
    fm, body = split_frontmatter(raw)
    description = fm.get("description", "").strip().strip('"')
    skill_name = fm.get("name", name).strip().strip('"')
    closure = transitive_closure(referenced_subfiles(body), commands_dir)
    out_body = strip_links(body).rstrip()
    parts = ["---", f"name: {skill_name}", f"description: {description}", "---", "", out_body]
    if closure:
        parts += ["", "---", "", "# 附录（自动内联的共享约定）", ""]
        parts.append(
            "> 以下内容由 command 引用的共享子文件自动内联，供不支持 slash 的 "
            "Claude 客户端离线阅读。请勿手动编辑本文件——改动应在对应 command 进行。"
        )
        for sub in closure:
            with open(os.path.join(commands_dir, sub), encoding="utf-8") as f:
                _, sub_body = split_frontmatter(f.read())
            sub_body = strip_links(sub_body).strip()
            parts += ["", f"## 附录：{sub}", "", sub_body]
    return "\n".join(parts).rstrip() + "\n"


def iter_commands(plugins, only_command):
    for p in plugins:
        commands_dir = os.path.join(ROOT, "plugins", p, "commands")
        if not os.path.isdir(commands_dir):
            continue
        for fn in sorted(os.listdir(commands_dir)):
            if not fn.endswith(".md") or fn.startswith("_"):
                continue
            name = fn[:-3]
            if only_command and name != only_command:
                continue
            yield (p, name, os.path.join(commands_dir, fn), commands_dir,
                   os.path.join(ROOT, "plugins", p, "skills", name, "SKILL.md"))


def main():
    ap = argparse.ArgumentParser(description="从 command 单源派生 skill")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--plugin")
    ap.add_argument("--command")
    args = ap.parse_args()
    if args.plugin and args.plugin not in PLUGINS:
        print(f"未知插件: {args.plugin}", file=sys.stderr)
        return 2
    plugins = [args.plugin] if args.plugin else PLUGINS
    written, drifted, unchanged = [], [], 0
    for p, name, cmd_path, commands_dir, skill_path in iter_commands(plugins, args.command):
        new_text = build_skill(cmd_path, commands_dir, name)
        old_text = ""
        if os.path.isfile(skill_path):
            with open(skill_path, encoding="utf-8") as f:
                old_text = f.read()
        if new_text == old_text:
            unchanged += 1
            continue
        if args.check:
            drifted.append(f"{p}/{name}")
            continue
        os.makedirs(os.path.dirname(skill_path), exist_ok=True)
        with open(skill_path, "w", encoding="utf-8") as f:
            f.write(new_text)
        kb = round(len(new_text.encode("utf-8")) / 1024, 1)
        written.append(f"{p}/{name} ({kb}KB){'  WARN>30KB' if kb > 30 else ''}")
    if args.check:
        if drifted:
            print(f"[X] {len(drifted)} 个 skill 与 command 不一致:")
            for d in drifted:
                print(f"   ~ {d}")
            return 1
        print(f"[OK] 全部 {unchanged} 个 skill 与 command 一致")
        return 0
    for w in written:
        print(f"  + {w}")
    print(f"\n生成 {len(written)} 个，未变 {unchanged} 个。helper skill 未触碰。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
