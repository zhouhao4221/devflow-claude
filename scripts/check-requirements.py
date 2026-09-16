#!/usr/bin/env python3
"""仓库根薄包装：真正的守卫随 rd 插件分发在 plugins/rd/scripts/check-requirements.py。

本仓库 CI 与 /rd:release 发布前置从这里调用；下游项目直接用
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/check-requirements.py --check
"""
import os
import runpy
import sys

TARGET = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                      "plugins", "rd", "scripts", "check-requirements.py")
if "--root" not in sys.argv:
    sys.argv += ["--root", os.path.dirname(os.path.dirname(os.path.abspath(__file__)))]
runpy.run_path(TARGET, run_name="__main__")
