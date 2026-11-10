import json
import os
import shutil
from pathlib import Path

REPO = Path("C:/Users/1/Documents/bazhuayu-rpa-docs")

# 1. Copy assets (if not already copied)
src_assets = REPO / "guides" / "assets"
dst_assets = REPO / "commands" / "images"
dst_assets.mkdir(parents=True, exist_ok=True)

copied = 0
for f in sorted(src_assets.glob("custom-instructions-*.png")):
    if not (dst_assets / f.name).exists():
        shutil.copy2(f, dst_assets / f.name)
        copied += 1
print(f"copied {copied} new images to commands/images/")

# 2. Update commands/custom-commands.mdx if not already updated
src_mdx = REPO / "guides" / "custom-instructions.mdx"
dst_mdx = REPO / "commands" / "custom-commands.mdx"
if src_mdx.exists():
    txt = src_mdx.read_text(encoding="utf-8")
    txt = txt.replace('src="assets/', 'src="images/')
    txt = txt.replace('](assets/', '](images/')
    dst_mdx.write_text(txt, encoding="utf-8")
    print(f"rewrote {dst_mdx}")
else:
    print(f"{src_mdx} already removed; keeping current {dst_mdx}")

# 3. Modify docs.json: ensure exactly one 自定义指令 group under 指令概述, none elsewhere
json_path = REPO / "docs.json"
data = json.loads(json_path.read_text(encoding="utf-8"))

# locate tabs
special_tab = None
overview_tab = None
special_group = None
overview_group = None

for tab in data["navigation"]["tabs"]:
    if tab["tab"] == "专题文档":
        special_tab = tab
    if tab["tab"] == "指令概述":
        overview_tab = tab

special_group = special_tab["groups"][0] if special_tab else None
overview_group = overview_tab["groups"][0] if overview_tab else None

# extract the 自定义指令 group from 专题文档 (canonical source with human-readable names)
custom_group = None
special_idx = None
for i, p in enumerate(list(special_group.get("pages", []))):
    if isinstance(p, dict) and p.get("group") == "自定义指令":
        custom_group = p
        special_idx = i
        break

if custom_group is None:
    raise RuntimeError("自定义指令 group not found under 专题文档")
print(f"found 自定义指令 in 专题文档 pages[{special_idx}] with {len(custom_group.get('pages', []))} entries")

# remove from 专题文档
special_group["pages"].pop(special_idx)
print("removed 自定义指令 from 专题文档")

# remove any existing 自定义指令 groups from 指令概述
removed = 0
for p in list(overview_group.get("pages", [])):
    if isinstance(p, dict) and p.get("group") == "自定义指令":
        overview_group["pages"].remove(p)
        removed += 1
print(f"removed {removed} duplicate 自定义指令 group(s) from 指令概述")

# append canonical group to 指令概述
overview_group["pages"].append(custom_group)
print(f"appended 自定义指令 to 指令概述 (now {len(overview_group['pages'])} items)")

# 4. Add redirect for old guides/custom-instructions page
if "redirects" not in data:
    data["redirects"] = []
redirects = data["redirects"]
new_redirect = {"source": "/guides/custom-instructions", "destination": "/commands/custom-commands"}
if not any(r.get("source") == new_redirect["source"] for r in redirects):
    redirects.append(new_redirect)
    print("added redirect /guides/custom-instructions -> /commands/custom-commands")
else:
    print("redirect already exists")

json_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
print("wrote docs.json")

# 5. Remove old guide file and its assets
if src_mdx.exists():
    src_mdx.unlink()
    print(f"deleted old {src_mdx}")
removed_assets = 0
for f in sorted(src_assets.glob("custom-instructions-*.png")):
    f.unlink()
    removed_assets += 1
print(f"deleted {removed_assets} old assets from guides/assets/")

# Summary
print("\n=== summary ===")
print(f"images copied: {copied}")
print(f"custom-commands.mdx updated: yes")
print(f"nav group moved: 专题文档 -> 指令概述")
print(f"duplicates removed from 指令概述: {removed}")
print(f"redirect added: /guides/custom-instructions -> /commands/custom-commands")
print(f"old guide removed: yes ({removed_assets} assets)")
