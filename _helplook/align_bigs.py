# -*- coding: utf-8 -*-
"""
按 HelpLook API 数据对齐 140 个自定义指令大分类：
- 删除本地 5 个 HelpLook 不存在的错误 slug
- 补 3 个缺失的占位页
- 更新所有 140 个占位页 frontmatter title
- 更新 docs.json 自定义指令分组与 redirects
- 更新 commands/custom-commands.mdx 总览页列表
"""
import json, re
from pathlib import Path

REPO = Path(r"C:/Users/1/Documents/bazhuayu-rpa-docs")
TMP = REPO / "_helplook"
CUSTOM_ID = 351278

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
hl_bigs = [(c.get("slug"), c.get("name")) for c in custom.get("child", []) if str(c.get("type")) == "2"]
hl_map = {s: n for s, n in hl_bigs}
hl_slugs = set(hl_map.keys())

# 2. 本地状态
local_files = sorted(REPO.glob("commands/custom-commands/*.mdx"))
local_slugs = {p.stem for p in local_files}

wrong_slugs = sorted(local_slugs - hl_slugs)
missing_slugs = sorted(hl_slugs - local_slugs)

print(f"HelpLook 大分类: {len(hl_slugs)}")
print(f"本地大分类文件: {len(local_slugs)}")
print(f"错误 slug(将删除): {wrong_slugs}")
print(f"缺失 slug(将新建): {missing_slugs}")

# 3. 删除错误 .mdx
for s in wrong_slugs:
    p = REPO / f"commands/custom-commands/{s}.mdx"
    if p.exists():
        p.unlink()
        print(f"  删除: {p}")

# 4. 新建缺失占位页
TEMPLATE = '---\ntitle: "{title}"\n---\n\n## 指令说明\n\n**描述：** {title}。\n\n<Warning>\n  本页内容正在完善中，参数说明与使用示例稍后补充。\n</Warning>\n\n## 参数说明\n\n<Tabs>\n  <Tab title="常规">\n\n    待补充。\n\n  </Tab>\n  <Tab title="高级">\n\n    待补充。\n\n  </Tab>\n</Tabs>\n\n## 使用示例\n\n待补充。\n\n<Info>\n  使用指令过程中遇到问题？前往 [八爪鱼RPA 开发者社区问答板块](https://rpa.bazhuayu.com/community/questions) 提问，获取官方与社区帮助。\n</Info>\n'
for s in missing_slugs:
    p = REPO / f"commands/custom-commands/{s}.mdx"
    p.write_text(TEMPLATE.format(title=hl_map[s]), encoding="utf-8")
    print(f"  新建: {p} ({hl_map[s]})")

# 5. 更新所有 140 个占位页 title
def fix_title(p, title):
    txt = p.read_text(encoding="utf-8")
    m = re.match(r'^(---\s*\n)(.*?)(\n---\s*\n)', txt, re.S)
    if not m:
        return
    fm = m.group(2)
    new_fm = re.sub(r'^title:\s*".*?"', f'title: "{title}"', fm, flags=re.M)
    if new_fm == fm:
        return  # 无变化
    new_txt = m.group(1) + new_fm + m.group(3) + txt[m.end():]
    p.write_text(new_txt, encoding="utf-8")
    print(f"  更新标题: {p.name} -> {title}")

for s, name in hl_map.items():
    p = REPO / f"commands/custom-commands/{s}.mdx"
    if p.exists():
        fix_title(p, name)

# 6. 更新 docs.json
docs = json.loads((REPO / "docs.json").read_text(encoding="utf-8"))

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

cc = find_cc(docs)
if not cc:
    raise SystemExit("未找到自定义指令分组")

# 记录当前 group 结构（保留子页面）
current_groups = {}
for p in cc["pages"]:
    if isinstance(p, dict) and p.get("group"):
        slug = None
        for pg in p.get("pages", []):
            if isinstance(pg, str) and pg.startswith("commands/custom-commands/") and "/" not in pg.split("/")[-1]:
                slug = pg.split("/")[-1]
                break
        if slug:
            current_groups[slug] = p["pages"]

# 按原顺序重建 pages，缺失 append
final_order = []
for p in cc["pages"]:
    if isinstance(p, dict):
        # 提取 group 的主 slug
        slug = None
        for pg in p.get("pages", []):
            if isinstance(pg, str) and pg.startswith("commands/custom-commands/") and pg.count("/") == 2:
                slug = pg.split("/")[-1]
                break
        if slug in hl_slugs:
            final_order.append(slug)
    elif isinstance(p, str) and p.startswith("commands/custom-commands/"):
        slug = p.split("/")[-1]
        if slug in hl_slugs:
            final_order.append(slug)

# 补缺失
for s in missing_slugs:
    if s not in final_order:
        final_order.append(s)

# 构建新的 pages 列表：有子页面的保持 group，其余 plain string
new_pages = ["commands/custom-commands"]  # 总览页
for s in final_order:
    if s in current_groups:
        # 更新 group 名称（用 HelpLook 真实名），保留现有 pages
        grp = {"group": hl_map[s], "pages": current_groups[s]}
        new_pages.append(grp)
    else:
        new_pages.append(f"commands/custom-commands/{s}")

cc["pages"] = new_pages

# 7. 更新 redirects：保留非自定义指令 redirects，重建 140 条自定义指令 redirects
old_redirects = docs.get("redirects", [])
non_custom = [r for r in old_redirects if not r.get("destination", "").startswith("/commands/custom-commands/")]
custom_redirects = [
    {"source": f"/commands/{s}", "destination": f"/commands/custom-commands/{s}"}
    for s in sorted(hl_slugs)
]
docs["redirects"] = non_custom + custom_redirects

(REPO / "docs.json").write_text(json.dumps(docs, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"\nredirects 已重建: 非自定义 {len(non_custom)} + 自定义 {len(custom_redirects)}")

# 8. 更新 commands/custom-commands.mdx 总览页
overview = REPO / "commands/custom-commands.mdx"
if overview.exists():
    # 按 HelpLook 原始顺序生成列表（custom.get('child') 顺序）
    lines = ["## 指令列表", ""]
    for s, name in hl_bigs:
        lines.append(f"- [{name}](/commands/custom-commands/{s})")
    lines.append("")
    # 替换 "## 指令列表" 到文件末尾
    txt = overview.read_text(encoding="utf-8")
    m = re.search(r'^## 指令列表\s*$', txt, re.M)
    if m:
        new_txt = txt[: m.start()] + "\n".join(lines)
        overview.write_text(new_txt, encoding="utf-8")
        print(f"总览页已更新: {len(hl_bigs)} 条")

print("\n对齐完成。建议运行：git status + _mdxcheck.cjs + git add docs.json commands/custom-commands*.mdx commands/custom-commands/ ...")
