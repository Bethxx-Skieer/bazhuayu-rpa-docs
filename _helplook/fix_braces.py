# -*- coding: utf-8 -*-
"""修复 MDX 裸花括号：把正文(非 frontmatter)中的 { / } 转义为 \{ / \}。
从 mdxcheck 日志提取失败文件列表；对已转义的 \{ 不再重复转义。"""
import re
from pathlib import Path

REPO = Path(r"C:/Users/1/Documents/bazhuayu-rpa-docs")
log = REPO / "_helplook" / "mdxcheck_final.log"
files = []
for line in log.read_text(encoding="utf-8").splitlines():
    if line.startswith("FAIL "):
        files.append(REPO / line[5:].strip())
print("待修复文件:", len(files))

open_b = re.compile(r"(?<!\\)\{")
close_b = re.compile(r"(?<!\\)\}")
fixed = 0
for f in files:
    txt = f.read_text(encoding="utf-8")
    # 分离 frontmatter
    if txt.startswith("---"):
        m = re.match(r"^---\n(.*?)\n---\n", txt, re.S)
        if m:
            fm = m.group(0)
            body = txt[m.end():]
            body2 = open_b.sub(r"\\{", body)
            body2 = close_b.sub(r"\\}", body2)
            txt = fm + body2
            f.write_text(txt, encoding="utf-8")
            fixed += 1
            continue
    # 无 frontmatter 兜底
    body2 = open_b.sub(r"\\{", txt)
    body2 = close_b.sub(r"\\}", body2)
    f.write_text(body2, encoding="utf-8")
    fixed += 1
print("已修复:", fixed)
