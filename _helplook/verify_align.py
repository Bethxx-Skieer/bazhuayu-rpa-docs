# -*- coding: utf-8 -*-
import json, re
from pathlib import Path

d = json.load(open("docs.json", encoding="utf-8"))

def find_cc(o):
    if isinstance(o, dict):
        if o.get("group") == "自定义指令" and isinstance(o.get("pages"), list) and any("custom-commands/" in str(x) for x in o["pages"]):
            return o
        for v in o.values():
            r = find_cc(v)
            if r:
                return r
    elif isinstance(o, list):
        for i in o:
            r = find_cc(i)
            if r:
                return r
    return None

cc = find_cc(d)
pages = cc["pages"]
print("自定义指令分组 pages 数:", len(pages))
print("前5项:", pages[:5])

def group_for(slug):
    for p in pages:
        if isinstance(p, dict):
            for pg in p.get("pages", []):
                if isinstance(pg, str) and pg.endswith(f"/custom-commands/{slug}"):
                    return p["group"]
    return None

print("Xtu3Dyv8 group名:", group_for("Xtu3Dyv8"))
print("i2Vbj6Mp group名:", group_for("i2Vbj6Mp"))
print("group 对象数:", len([p for p in pages if isinstance(p, dict)]))
print("redirects 总数:", len(d["redirects"]))
print("custom redirects:", len([r for r in d["redirects"] if r["destination"].startswith("/commands/custom-commands/")]))

# title consistency
tree = json.load(open("_helplook/tree.json", encoding="utf-8"))["data"]["list"]
def find_node(n, tid):
    for c in n:
        if str(c.get("id")) == str(tid):
            return c
        r = find_node(c.get("child", []), tid)
        if r:
            return r
    return None

custom = find_node(tree, 351278)
hl_map = {c["slug"]: c["name"] for c in custom.get("child", []) if str(c.get("type")) == "2"}
mismatches = []
for s, name in hl_map.items():
    p = Path(f"commands/custom-commands/{s}.mdx")
    if p.exists():
        m = re.search(r'^title:\s*"([^"]+)"', p.read_text(encoding="utf-8"), re.M)
        if m and m.group(1) != name:
            mismatches.append((s, m.group(1), name))
print("标题不一致:", len(mismatches), mismatches[:10])
