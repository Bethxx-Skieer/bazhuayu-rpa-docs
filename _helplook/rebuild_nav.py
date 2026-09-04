# -*- coding: utf-8 -*-
"""
以文件系统为准重建 自定义指令 导航 / 大分类页 / 总览页。
- 扫描 commands/custom-commands/<bigslug>/ 下真实存在的 *.mdx 作为子指令
- 完整保留 docs.json 现有 redirects（含 732 条子指令级跳转），仅补/覆盖 137 条大分类级
- 不依赖 tree.json 的嵌套结构，避免漏列多级子指令
"""
import json, re
from pathlib import Path

REPO = Path(r"C:/Users/1/Documents/bazhuayu-rpa-docs")
CUSTOM = REPO / "commands" / "custom-commands"
TMP = REPO / "_helplook"
COMMUNITY = "https://rpa.bazhuayu.com/community/questions"
EXCLUDE = {"LqGka251", "q1cyRlx9", "zaP6Z9qv"}

# 取大分类显示名（来自 tree.json，slug 唯一）
tree = json.loads((TMP / "tree.json").read_text(encoding="utf-8"))["data"]["list"]
hl_map = {}

def collect_bigs(n):
    for c in n:
        if str(c.get("type")) == "2" and c.get("slug") not in EXCLUDE:
            hl_map[c.get("slug")] = c.get("name")
        collect_bigs(c.get("child", []))

collect_bigs(tree)
print("HelpLook 大分类(去排除):", len(hl_map))

def get_title(p: Path):
    try:
        txt = p.read_text(encoding="utf-8")
        m = re.search(r'^title:\s*"(.*?)"', txt, re.M)
        if m:
            return m.group(1)
    except Exception:
        pass
    return p.stem

# 1) 重建大分类页 + 收集导航
big_pages = []
for bigdir in sorted(p for p in CUSTOM.iterdir() if p.is_dir()):
    bslug = bigdir.name
    if bslug not in hl_map:
        print("  跳过不在 tree 的大分类目录:", bslug)
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
    print(f"  大分类页 {bslug} ({bname}): {len(subs)} 子指令")

# 2) 更新 docs.json 导航
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

# 3) 保留全部现有 redirects，仅补/覆盖 137 条大分类级
existing = {r.get("source"): r for r in docs.get("redirects", []) if r.get("source")}
before = len(existing)
for s in sorted(hl_map):
    existing[f"/commands/{s}"] = {"source": f"/commands/{s}", "destination": f"/commands/custom-commands/{s}"}
docs["redirects"] = list(existing.values())
print(f"redirects: 原 {before} -> 现 {len(docs['redirects'])} (应含 732 子指令级)")

(REPO / "docs.json").write_text(json.dumps(docs, ensure_ascii=False, indent=2), encoding="utf-8")

# 4) 更新总览页
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

# 校验
sub_total = sum(len(s) for _, _, s in big_pages)
print(f"\n完成: 大分类 {len(big_pages)} 个, 子指令页 {sub_total} 篇")
