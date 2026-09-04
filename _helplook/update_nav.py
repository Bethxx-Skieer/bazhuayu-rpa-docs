# -*- coding: utf-8 -*-
"""
更新 docs.json 自定义指令分组导航: 把每个大分类(如 geamt8fB)从字符串 page
改成嵌套 group, 下挂其所有子指令 page。
用法:
  python _helplook/update_nav.py geamt8fB            # 仅领星
  python _helplook/update_nav.py --all               # 全量
"""
import os, sys, json
from pathlib import Path

REPO = Path(r"C:/Users/1/Documents/bazhuayu-rpa-docs")
TMP = REPO / "_helplook"
CUSTOM_ID = 351278

def find_cc(o):
    if isinstance(o, dict):
        if o.get("group") == "自定义指令" and isinstance(o.get("pages"), list) \
           and any("custom-commands/" in str(p) for p in o["pages"]):
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

def find_node(tree, tid):
    for n in tree:
        if str(n.get("id")) == str(tid):
            return n
        r = find_node(n.get("child", []), tid)
        if r:
            return r
    return None

def build_big_map(tree):
    custom = find_node(tree, CUSTOM_ID)
    big = {}
    if not custom:
        return big
    def walk(n):
        for c in n.get("child", []):
            if c.get("type") == "2":
                kids = [k["slug"] for k in c.get("child", []) if k.get("type") == "2"]
                big[c["slug"]] = (c.get("name"), kids)
            walk(c)
    walk(custom)
    return big

def main():
    args = sys.argv[1:]
    if not args:
        print("usage: update_nav.py <slug>... | --all"); return
    docs = json.loads((REPO / "docs.json").read_text(encoding="utf-8"))
    tree = json.loads((TMP / "tree.json").read_text(encoding="utf-8"))["data"]["list"]
    cc = find_cc(docs)
    if not cc:
        print("未找到自定义指令分组"); return
    big_map = build_big_map(tree)
    targets = list(big_map.keys()) if args == ["--all"] else args
    pages = cc["pages"]
    newpages = []
    changed = 0
    for p in pages:
        if isinstance(p, str) and p.startswith("commands/custom-commands/"):
            slug = p.split("/")[-1]
            if slug in targets and slug in big_map:
                name, kids = big_map[slug]
                grp = {"group": name, "pages": [p] + [f"commands/custom-commands/{slug}/{k}" for k in kids]}
                newpages.append(grp)
                changed += 1
                continue
        newpages.append(p)
    cc["pages"] = newpages
    (REPO / "docs.json").write_text(json.dumps(docs, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"已更新 {changed} 个大分类导航; 目标数={len(targets)}")

if __name__ == "__main__":
    main()
