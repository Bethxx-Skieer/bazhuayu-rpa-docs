# -*- coding: utf-8 -*-
import os, json, ssl, urllib.request
from pathlib import Path
from collections import Counter

KEY = os.environ["HELPLOOK_API_KEY"]
TMP = Path(r"C:/Users/1/Documents/bazhuayu-rpa-docs/_helplook")
TMP.mkdir(exist_ok=True)
ctx = ssl.create_default_context()

def fetch(url, headers):
    req = urllib.request.Request(url, headers=headers)
    return json.loads(urllib.request.urlopen(req, timeout=60, context=ctx).read())

d = fetch("https://api.helplook.net/api/content",
          {"User-Agent": "Mozilla/5.0", "x-api-key": KEY})
tree = d["data"]["list"]
(TMP / "tree.json").write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")

CUSTOM_ID = 351278  # 自定义指令 栏目

def find(node, tid):
    if str(node.get("id")) == str(tid):
        return node
    for c in node.get("child", []):
        r = find(c, tid)
        if r:
            return r
    return None

target = None
for n in tree:
    target = find(n, CUSTOM_ID)
    if target:
        break

def walk(node, depth, out):
    out.append((depth, str(node.get("id")), node.get("slug"), node.get("name"),
                node.get("type"), str(node.get("parent_id"))))
    for c in node.get("child", []):
        walk(c, depth + 1, out)

sub = []
if target:
    walk(target, 0, sub)
    print("自定义指令子树节点总数:", len(sub))
    print("type 分布:", Counter(x[4] for x in sub))
    tops = [x for x in sub if x[0] == 1]
    print("第1层(大分类)数:", len(tops))
    for t in tops[:15]:
        print("   大分类:", t[1], "| slug=", t[2], "|", t[3])
    kids = [x for x in sub if x[0] == 2]
    print("第2层(子指令)数:", len(kids))
    for k in kids[:15]:
        print("   子指令:", k[1], "| slug=", k[2], "|", k[3], "| parent=", k[5])
else:
    print("未找到自定义指令节点 351278")
