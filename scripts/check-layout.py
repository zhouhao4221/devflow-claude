#!/usr/bin/env python3
"""check-layout.py — 校验 5 个插件的目录布局，防止斜杠菜单被污染。

Claude Code 把 `commands/` 下的**每个** `.md` 和 `skills/` 下的**每个**
子目录都注册成斜杠菜单项。两类东西混进去就会污染菜单、白占 always-on token：

  A. 命令镜像 skill —— `skills/<n>/` 与 `commands/<n>.md` 同名，
     description 还一模一样，用户看到每条命令重复两遍。
     （2026-08 前由 gen-skills.py 派生 51 个，已整体移除）
  B. 共享参考文档 —— `_*.md`、`*-rationale.md` 这类给命令 Read 的片段，
     放在 `commands/` 下会变成 `/req:_storage` 这种伪命令。
     它们统一放 `plugins/<p>/shared/`，命令用 `../shared/x.md` 链接引用。

顺带校验所有 Markdown 相对链接可达，避免搬迁后留下悬空引用。

用法：check-layout.py [--check] [--plugin P]
  默认        自动清理能自动清理的（镜像目录、skills/ 散落文件）并报告其余
  --check     只报告，发现任何问题退出码 1（发布前置 / CI 用）
"""
import argparse
import os
import re
import shutil
import sys

PLUGINS = ["req", "api", "pm", "diag", "uat"]
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LINK_RE = re.compile(r"\[[^\]]*\]\(([^)\s]+)\)")


def frontmatter(path):
    with open(path, encoding="utf-8") as f:
        text = f.read()
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n", text, re.S)
    if not m:
        return None
    fm = {}
    for line in m.group(1).splitlines():
        km = re.match(r"^([A-Za-z_-]+):\s*(.*)$", line)
        if km:
            fm[km.group(1)] = km.group(2).strip().strip('"')
    return fm


def check_skills(plugins):
    """返回 (mirrors, strays, malformed, helpers)。mirrors/strays 可自动清理。"""
    mirrors, strays, malformed, helpers = [], [], [], []
    for p in plugins:
        cdir = os.path.join(ROOT, "plugins", p, "commands")
        sdir = os.path.join(ROOT, "plugins", p, "skills")
        if not os.path.isdir(sdir):
            continue
        for entry in sorted(os.listdir(sdir)):
            path = os.path.join(sdir, entry)
            if not os.path.isdir(path):
                strays.append((f"{p}/skills/{entry}", path))
            elif os.path.isfile(os.path.join(cdir, entry + ".md")):
                mirrors.append((f"{p}/{entry}", path))
            elif not os.path.isfile(os.path.join(path, "SKILL.md")):
                malformed.append(f"{p}/skills/{entry}: 缺少 SKILL.md")
            else:
                fm = frontmatter(os.path.join(path, "SKILL.md")) or {}
                if not fm.get("description"):
                    malformed.append(f"{p}/skills/{entry}: frontmatter 缺 description")
                elif fm.get("name") and fm["name"] != entry:
                    malformed.append(
                        f"{p}/skills/{entry}: frontmatter name={fm['name']} 与目录名不符")
                helpers.append(f"{p}/{entry}")
    return mirrors, strays, malformed, helpers


def check_commands(plugins):
    """commands/ 下只能放真命令：必须有 frontmatter 且带 description。"""
    bad, commands = [], []
    for p in plugins:
        cdir = os.path.join(ROOT, "plugins", p, "commands")
        if not os.path.isdir(cdir):
            continue
        for fn in sorted(os.listdir(cdir)):
            if not fn.endswith(".md"):
                bad.append(f"{p}/commands/{fn}: 非 .md 文件")
                continue
            fm = frontmatter(os.path.join(cdir, fn))
            if fm is None:
                bad.append(f"{p}/commands/{fn}: 无 frontmatter，"
                           f"共享参考文档应移到 plugins/{p}/shared/")
            elif not fm.get("description"):
                bad.append(f"{p}/commands/{fn}: frontmatter 缺 description")
            else:
                commands.append(f"{p}/{fn[:-3]}")
    return bad, commands


def check_links(plugins):
    """所有插件 Markdown 的相对链接必须可达（含搬迁后的 ../shared/ 引用）。"""
    broken, total = [], 0
    for p in plugins:
        base = os.path.join(ROOT, "plugins", p)
        for dirpath, dirnames, filenames in os.walk(base):
            # templates/ 里的链接指向渲染后的目标项目目录，不在本仓解析
            dirnames[:] = [d for d in dirnames if d != "templates"]
            if os.path.basename(dirpath) == "templates":
                continue
            for fn in sorted(filenames):
                if not fn.endswith(".md"):
                    continue
                src = os.path.join(dirpath, fn)
                with open(src, encoding="utf-8") as f:
                    text = f.read()
                for target in LINK_RE.findall(text):
                    # 跳过外链、纯锚点、以及含占位符/变量的目标
                    if re.match(r"^(https?:|mailto:|#)", target) or \
                            any(c in target for c in "<{$"):
                        continue
                    total += 1
                    resolved = os.path.normpath(
                        os.path.join(dirpath, target.split("#", 1)[0]))
                    if not os.path.exists(resolved):
                        broken.append(
                            f"{os.path.relpath(src, ROOT)} -> {target}")
    return broken, total


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--plugin")
    a = ap.parse_args()
    if a.plugin and a.plugin not in PLUGINS:
        print(f"未知插件: {a.plugin}", file=sys.stderr)
        return 2
    plugins = [a.plugin] if a.plugin else PLUGINS

    mirrors, strays, malformed, helpers = check_skills(plugins)
    bad_cmds, commands = check_commands(plugins)
    broken, link_total = check_links(plugins)

    if not a.check:
        for name, path in mirrors:
            shutil.rmtree(path)
            print(f"  - {name}（命令镜像 skill，已删除）")
        for name, path in strays:
            os.remove(path)
            print(f"  - {name}（skills/ 散落文件，已删除）")
        if mirrors or strays:
            print()
        mirrors, strays = [], []

    problems = []
    if mirrors:
        problems.append(f"{len(mirrors)} 个命令镜像 skill（斜杠菜单会重复两遍）: "
                        + ", ".join(n for n, _ in mirrors))
    if strays:
        problems.append(f"{len(strays)} 个 skills/ 散落文件（skill 必须是 <name>/SKILL.md）: "
                        + ", ".join(n for n, _ in strays))
    if malformed:
        problems.append(f"{len(malformed)} 个 helper skill 有问题: " + "; ".join(malformed))
    if bad_cmds:
        problems.append(f"{len(bad_cmds)} 个 commands/ 违规文件: " + "; ".join(bad_cmds))
    if broken:
        problems.append(f"{len(broken)} 个悬空链接: " + "; ".join(broken))

    if problems:
        print("[X] " + "\n    ".join(problems))
        if not a.check:
            print("    以上需手工修复（清理类问题已自动处理）")
        return 1
    print(f"[OK] {len(commands)} 个命令 + {len(helpers)} 个 helper skill = "
          f"{len(commands) + len(helpers)} 个菜单项，无重复；"
          f"{link_total} 个相对链接全部可达")
    return 0


if __name__ == "__main__":
    sys.exit(main())
