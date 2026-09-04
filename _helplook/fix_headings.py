# -*- coding: utf-8 -*-
"""稳健清洗自定义指令子页：
1) 合并孤立标题行(#{1,4} 独占一行)与下一行有意义文字
2) 删除空标题(## 等无文字)与空列表项(仅 '-')
3) 兼容 \\r\\n
"""
import re, glob
from pathlib import Path

REPO = Path(r"C:/Users/1/Documents/bazhuayu-rpa-docs")
files = glob.glob(str(REPO / "commands" / "custom-commands" / "*" / "*.mdx"))
hash_re = re.compile(r"^(#{1,4})\s*$")
empty_heading2 = re.compile(r"^#{1,4}\s*-\s*$")  # 标题合并空列表项后的残留: ## -
empty_bullet = re.compile(r"^-\s*$")

changed_total = 0
for f in files:
    raw = Path(f).read_text(encoding="utf-8")
    lines = raw.split("\n")
    out = []
    i = 0
    n = len(lines)
    changed = False
    while i < n:
        line = lines[i].rstrip("\r")
        m = hash_re.match(line)
        if m:
            # 看下一行是否有意义文字
            nxt = lines[i + 1].rstrip("\r").strip() if i + 1 < n else ""
            if nxt and not hash_re.match(nxt) and not empty_bullet.match(nxt):
                out.append(m.group(1) + " " + nxt)
                changed = True
                i += 2
                continue
            else:
                # 空标题 -> 删除
                changed = True
                i += 1
                continue
        if empty_heading2.match(line):
            # 标题合并空列表项后的残留 -> 删除
            changed = True
            i += 1
            continue
        if empty_bullet.match(line):
            changed = True
            i += 1
            continue
        out.append(line)
        i += 1
    if changed:
        Path(f).write_text("\n".join(out), encoding="utf-8")
        changed_total += 1

print(f"清洗完成, 处理文件: {changed_total}")
