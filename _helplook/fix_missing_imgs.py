# -*- coding: utf-8 -*-
"""扫描自定义指令下所有 MDX，移除指向不存在图片的 ![]() 引用行，避免线上破图。"""
import re
from pathlib import Path

REPO = Path(r"C:/Users/1/Documents/bazhuayu-rpa-docs")
CUSTOM = REPO / "commands" / "custom-commands"

img_re = re.compile(r'!\[[^\]]*\]\((\.{0,2}/?images/[^)\s]+)\)')
removed = []
for mdx in sorted(CUSTOM.rglob("*.mdx")):
    txt = mdx.read_text(encoding="utf-8")
    lines = txt.split("\n")
    new_lines = []
    changed = False
    for ln in lines:
        m = img_re.search(ln)
        if m:
            ref = m.group(1)
            # 解析相对路径（相对 mdx 所在目录）
            target = (mdx.parent / ref).resolve()
            if not target.exists():
                removed.append((str(mdx.relative_to(REPO)), ref))
                changed = True
                continue
        new_lines.append(ln)
    if changed:
        mdx.write_text("\n".join(new_lines), encoding="utf-8")

print(f"共移除 {len(removed)} 处缺失图片引用:")
for f, ref in removed:
    print("  ", f, "->", ref)
if not removed:
    print("  (无缺失图片引用)")
