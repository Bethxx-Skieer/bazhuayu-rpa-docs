# -*- coding: utf-8 -*-
"""
重建自定义指令大分类页、导航、redirects、总览页。
- 大分类页只列子指令，不用占位格式
- 排除用户特意不需要的三篇：LqGka251/q1cyRlx9/zaP6Z9qv
- 子指令内容搬运保持现有 convert.py 逻辑
"""
import json, re
from pathlib import Path

REPO = Path(r"C:/Users/1/Documents/bazhuayu-rpa-docs")
TMP = REPO / "_helplook"
CUSTOM_ID = 351278
EXCLUDE = {"LqGka251", "q1cyRlx9", "zaP6Z9qv"}

# 1. 加载 HelpLook 真实映射
tree = json.loads((TMP / "tree.json").read_text(encoding="utf-8"))["data"]["list"]

def find_node(n, tid):
    for c in n:
        if str(c.get("id")) == str(tid):
            return c
        r = find_node(c.get("child", []), tid)
        if r:
            return r
    return None

custom = find_node(tree, CUSTOM_ID)
hl_bigs = [(c.get("slug"), c.get("name"), c.get("child", []))
           for c in custom.get("child", []) if str(c.get("type")) == "2" and c.get("slug") not in EXCLUDE]
hl_map = {s: n for s, n, _ in hl_bigs}
hl_slugs = set(hl_map.keys())

print(f"HelpLook 自定义指令大分类: {len(hl_slugs)}（已排除 {EXCLUDE}）")

# 2. 删除本地多余的大分类文件（包括 EXCLUDE 和 HelpLook 里没有的）
local_files = sorted(REPO.glob("commands/custom-commands/*.mdx"))
local_slugs = {p.stem for p in local_files}
wrong = local_slugs - hl_slugs
print(f"将删除的本地多余文件: {sorted(wrong)}")
for s in wrong:
    p = REPO / f"commands/custom-commands/{s}.mdx"
    if p.exists():
        p.unlink()
        print(f"  删除: {p.name}")

# 3. 生成/更新大分类页：只列子指令
OVERVIEW_LINK = "https://rpa.bazhuayu.com/community/questions"

def build_index(slug, name, children):
    lines = [f'---\ntitle: "{name}"\n---\n', f"## {name}", ""]
    # 只取直接子指令（type==2），不递归孙节点
    kids = [(c.get("slug"), c.get("name")) for c in children if str(c.get("type")) == "2"]
    if kids:
        lines.append("### 子指令")
        lines.append("")
        for kslug, kname in kids:
            lines.append(f"- [{kname}](./{slug}/{kslug})")
        lines.append("")
    else:
        lines.append("该分类下暂无子指令。")
        lines.append("")
    lines.append("<Info>")
    lines.append(f"  使用指令过程中遇到问题？前往 [八爪鱼RPA 开发者社区问答板块]({OVERVIEW_LINK}) 提问，获取官方与社区帮助。")
    lines.append("</Info>")
    lines.append("")
    return "\n".join(lines)

for slug, name, children in hl_bigs:
    p = REPO / f"commands/custom-commands/{slug}.mdx"
    p.write_text(build_index(slug, name, children), encoding="utf-8")
    print(f"  更新分类页: {slug}.mdx ({name}, 子指令 {len([c for c in children if str(c.get('type'))=='2'])})条")

# 4. 更新 docs.json
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
    raise SystemExit("未找到自定义指令分组")

# 新的 pages：总览 + 大分类（本地已有子指令文件才展开 group，否则 plain string）
new_pages = ["commands/custom-commands"]
for slug, name, children in hl_bigs:
    kids = [(c.get("slug"), c.get("name")) for c in children if str(c.get("type")) == "2"]
    local_kids = [ks for ks, _ in kids if (REPO / f"commands/custom-commands/{slug}/{ks}.mdx").exists()]
    if local_kids:
        pages = [f"commands/custom-commands/{slug}"] + [f"commands/custom-commands/{slug}/{ks}" for ks in local_kids]
        new_pages.append({"group": name, "pages": pages})
    else:
        new_pages.append(f"commands/custom-commands/{slug}")

cc["pages"] = new_pages

# 5. 更新 redirects：保留非自定义，重建 137 条（140-3）
old_redirects = docs.get("redirects", [])
non_custom = [r for r in old_redirects if not r.get("destination", "").startswith("/commands/custom-commands/")]
custom_redirects = [
    {"source": f"/commands/{s}", "destination": f"/commands/custom-commands/{s}"}
    for s in sorted(hl_slugs)
]
docs["redirects"] = non_custom + custom_redirects

(REPO / "docs.json").write_text(json.dumps(docs, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"\ndocs.json 已更新: {len(new_pages)-1} 个分类, redirects {len(non_custom)}+{len(custom_redirects)}")

# 6. 更新总览页
overview = REPO / "commands/custom-commands.mdx"
lines = ["## 指令列表", ""]
for slug, name, _ in hl_bigs:
    lines.append(f"- [{name}](/commands/custom-commands/{slug})")
lines.append("")
if overview.exists():
    txt = overview.read_text(encoding="utf-8")
    m = re.search(r'^## 指令列表\s*$', txt, re.M)
    if m:
        new_txt = txt[: m.start()] + "\n".join(lines)
    else:
        new_txt = txt.rstrip() + "\n\n" + "\n".join(lines)
    overview.write_text(new_txt, encoding="utf-8")
    print(f"总览页已更新: {len(hl_bigs)} 条")

print("\n完成。建议校验：python -m json.tool docs.json + node _mdxcheck.cjs ...")
