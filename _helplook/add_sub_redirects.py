#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把 732 条自定义子指令的 /commands/{子slug} 跳转合并进 docs.json。

机制依据（已线上验证）：
  /helpcenter/docs/{slug} 由服务端按 docs.json 里 /commands/{slug} 的
  redirect 目标做 308。大分类 geamt8fB 因有 /commands/geamt8fB 跳转，
  旧链接 /docs/geamt8fB 能跳到 /commands/custom-commands/geamt8fB。
  子指令缺这条跳转 -> /docs/{子slug} 直接 404。

 action: 为每篇子指令补 /commands/{子slug} -> /commands/custom-commands/{大分类slug}/{子slug}
"""
import json
from pathlib import Path

REPO = Path(r"C:/Users/1/Documents/bazhuayu-rpa-docs")
TREE = REPO / "_helplook" / "tree.json"
DOC = REPO / "docs.json"

def find_node(n, tid):
    for c in n:
        if str(c.get("id")) == str(tid):
            return c
        r = find_node(c.get("child", []), tid)
        if r:
            return r
    return None

def main():
    tree = json.load(open(TREE, encoding="utf-8"))["data"]["list"]
    custom = find_node(tree, 351278)
    bigs = [c for c in custom.get("child", []) if str(c.get("type")) == "2"]

    pairs = []  # (subslug, bigslug)
    for b in bigs:
        bigslug = b["slug"]
        for ch in b.get("child", []):
            if str(ch.get("type")) == "2":
                pairs.append((ch["slug"], bigslug))
            for ch2 in ch.get("child", []):
                if str(ch2.get("type")) == "2":
                    pairs.append((ch2["slug"], bigslug))

    d = json.load(open(DOC, encoding="utf-8"))
    reds = d.get("redirects", [])
    existing_src = {r["source"] for r in reds}

    new_reds = []
    collisions = []
    seen = set()
    for subslug, bigslug in pairs:
        src = f"/commands/{subslug}"
        dst = f"/commands/custom-commands/{bigslug}/{subslug}"
        if src in seen:
            continue
        seen.add(src)
        if src in existing_src:
            collisions.append((src, dst, "已存在相同 source 的 redirect"))
            continue
        new_reds.append({"source": src, "destination": dst})

    print(f"子指令对总数: {len(pairs)}（唯一 source: {len(seen)}）")
    print(f"将新增 redirect 数: {len(new_reds)}")
    print(f"冲突（跳过）数: {len(collisions)}")
    for c in collisions[:20]:
        print("  COLLISION:", c)

    d["redirects"] = reds + new_reds
    json.dump(d, open(DOC, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"docs.json redirects 现总数: {len(d['redirects'])}")

if __name__ == "__main__":
    main()
