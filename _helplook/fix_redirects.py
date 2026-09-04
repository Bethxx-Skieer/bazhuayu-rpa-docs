# -*- coding: utf-8 -*-
"""外科手术修复 docs.json redirects：
- 137 大分类级(/3): 仅保留 source 真实属于 137 大分类目录的跳转，剔除 rebuild 误加的 330 条子指令级(/3)
- 732 子指令级(/4): 全部保留(正确)
- 330 普通(other): 全部保留(正确)
"""
import json, re
from pathlib import Path

REPO = Path(r"C:/Users/1/Documents/bazhuayu-rpa-docs")
CUSTOM = REPO / "commands" / "custom-commands"
docs = json.loads((REPO / "docs.json").read_text(encoding="utf-8"))
rd = docs["redirects"]

# 真实 137 大分类 slug = 扁平目录名
big_slugs = {p.name for p in CUSTOM.iterdir() if p.is_dir()}
print("真实大分类目录数:", len(big_slugs))

kept, removed = [], []
for r in rd:
    dst = r.get("destination", "")
    if dst.startswith("/commands/custom-commands/") and dst.count("/") == 3:
        # /3: /commands/custom-commands/{x}
        x = dst[len("/commands/custom-commands/"):].strip("/")
        if x in big_slugs:
            kept.append(r)
        else:
            removed.append(r)  # 错误地把子指令当大分类
    else:
        kept.append(r)

docs["redirects"] = kept
(REPO / "docs.json").write_text(json.dumps(docs, ensure_ascii=False, indent=2), encoding="utf-8")

sub = [r for r in kept if r["destination"].count("/") == 4]
big = [r for r in kept if r["destination"].count("/") == 3]
other = [r for r in kept if not r["destination"].startswith("/commands/custom-commands/")]
print(f"修复后: 总 {len(kept)} | /4子指令 {len(sub)} | /3大分类 {len(big)} | 其他 {len(other)}")
print(f"移除错误 /3 跳转: {len(removed)}")
assert len(sub) == 732 and len(big) == 137 and len(other) == 330, "redirects 仍未正确!"
print("OK: 732 + 137 + 330 = 1199 正确")
