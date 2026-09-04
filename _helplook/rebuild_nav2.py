# -*- coding: utf-8 -*-
"""
修正版：仅更新 自定义指令 导航(pages) + 大分类页 + 总览页。
- 大分类名只取 custom 节点的【直接子节点】(type==2)，不递归收集子指令
- 【完全不动】 docs.json 现有 redirects（HEAD 已含 330+137+732=1199 条正确跳转）
"""
import json, re
from pathlib import Path

REPO = Path(r"C:/Users/1/Documents/bazhuayu-rpa-docs")
CUSTOM = REPO / "commands" / "custom-commands"
TMP = REPO / "_helplook"
COMMUNITY = "https://rpa.bazhuayu.com/community/questions"
EXCLUDE = {"LqGka251", "q1cyRlx9", "zaP6Z9qv"}

tree = json.loads((TMP / "tree.json").read_text(encoding="utf-8"))["data"]["list"]

def find(n, tid):
    for c in n:
        if str(c.get("id")) == str(tid):
            return c
        r = find(c.get("child", []), tid)
        if r:
            return r
    return None

custom = find(tree, 351278)
# 仅直接子节点 = 大分类
hl_map = {c.get("slug"): c.get("name") for c in custom.get("child", [])
          if str(c.get("type")) == "2" and c.get("slug") not in EXCLUDE}
print("大分类(直接子节点):", len(hl_map))

def get_title(p: Path):
    try:
        m = re.search(r'^title:\s*"(.*?)"', p.read_text(encoding="utf-8"), re.M)
        if m:
            return m.group(1)
    except Exception:
        pass
    return p.stem

# 1) 重建大分类页（以文件系统真实子指令为准）
big_pages = []
for bigdir in sorted(p for p in CUSTOM.iterdir() if p.is_dir()):
    bslug = bigdir.name
    if bslug not in hl_map:
        print("  跳过非大分类目录:", bslug)
        continue
    bname = hl_map[bslug]
    subs = sorted(bigdir.glob("*.mdx"))
    lines = [f'---\ntitle: "{bname}"\n---\n', f"## {bname}", "", "### 子指令", ""]
    for sp in subs:
        lines.append(f"- [{get_title(sp)}](./{bslug}/{sp.stem})")
    lines += ["", "<Info>",
              f"  使用指令过程中遇到问题？前往 [八爪鱼RPA 开发者社区问答板块]({COMMUNITY}) 提问，获取官方与社区帮助。",
              "</Info>", ""]
    (CUSTOM / f"{bslug}.mdx").write_text("\n".join(lines), encoding="utf-8")
    big_pages.append((bslug, bname, subs))

# 2) 只更新 docs.json 的自定义指令分组 pages，redirects 保持不变
docs = json.loads((REPO / "docs.json").read_text(encoding="utf-8"))

def find_cc(o):
    if isinstance(o, dict):
        if o.get("group") == "自定义指令" and isinstance(o.get("pages"), list):
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

cc = find_cc(docs)
if not cc:
    raise SystemExit("未找到 自定义指令 分组")
new_pages = ["commands/custom-commands"]
for bslug, bname, subs in big_pages:
    pages = [f"commands/custom-commands/{bslug}"] + [f"commands/custom-commands/{bslug}/{sp.stem}" for sp in subs]
    new_pages.append({"group": bname, "pages": pages})
cc["pages"] = new_pages
(REPO / "docs.json").write_text(json.dumps(docs, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"docs.json 导航已更新: {len(big_pages)} 大分类, 子指令页 {sum(len(s) for _,_,s in big_pages)} 篇")

# 3) 重建总览页
overview = CUSTOM / "custom-commands.mdx"
lines = ["## 指令列表", ""]
for bslug, bname, _ in big_pages:
    lines.append(f"- [{bname}](/commands/custom-commands/{bslug})")
lines.append("")
if overview.exists():
    txt = overview.read_text(encoding="utf-8")
    m = re.search(r"^## 指令列表\s*$", txt, re.M)
    new_txt = (txt[: m.start()] + "\n".join(lines)) if m else (txt.rstrip() + "\n\n" + "\n".join(lines))
    overview.write_text(new_txt, encoding="utf-8")
    print(f"总览页已更新: {len(big_pages)} 条")

# 校验 redirects 未被改动
print("redirects 仍保持:", len(docs.get("redirects", [])), "条 (应=1199)")
