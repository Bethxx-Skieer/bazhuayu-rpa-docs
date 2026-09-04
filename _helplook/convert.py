# -*- coding: utf-8 -*-
"""
HelpLook 自定义指令 HTML -> Mintlify MDX 转换器 (忠实 1:1 搬运)
用法:
  python _helplook/convert.py one <slug> <bigslug>   # 单篇样例
  python _helplook/convert.py big <slug>             # 某大分类下全部子指令
  python _helplook/convert.py all                    # 全部(逐大分类)
依赖环境变量 HELPLOOK_API_KEY
"""
import os, sys, json, ssl, re, time, urllib.request
from pathlib import Path
from html.parser import HTMLParser

KEY = os.environ.get("HELPLOOK_API_KEY")
REPO = Path(r"C:/Users/1/Documents/bazhuayu-rpa-docs")
CUSTOM = REPO / "commands" / "custom-commands"
TMP = REPO / "_helplook"
TMP.mkdir(exist_ok=True)
ctx = ssl.create_default_context()
COMMUNITY = "https://rpa.bazhuayu.com/community/questions"

# ---------- HTML -> Markdown ----------
class MDXBuilder(HTMLParser):
    def __init__(self, slug):
        super().__init__(convert_charrefs=True)
        self.slug = slug
        self.md = []
        self.imgs = []          # (src, localname)
        self.img_idx = 0
        self._buf = ""
        self._in_heading = False
        self._a_href = None
        self._a_text = ""

    def _flush(self):
        if self._buf:
            self.md.append(self._buf)
            self._buf = ""

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag in ("h1", "h2", "h3", "h4"):
            self._flush()
            self._in_heading = True
            self.md.append("\n" + "#" * int(tag[1]) + " ")
        elif tag == "p":
            self._flush()
            self.md.append("\n")
        elif tag == "br":
            self.md.append("\n")
        elif tag in ("strong", "b"):
            self._buf += "<strong>"
        elif tag in ("em", "i"):
            self._buf += "<em>"
        elif tag == "a":
            self._a_href = a.get("href", "")
        elif tag == "img":
            src = a.get("src", "")
            # 只搬运可下载的线上图片；本地临时路径跳过
            if src and (src.startswith("http://") or src.startswith("https://")):
                self.img_idx += 1
                local = f"{self.slug}-{self.img_idx:02d}.png"
                self.imgs.append((src, local))
                self._flush()
                self.md.append(f"![image](images/{local})\n")
        elif tag == "li":
            self.md.append("\n- ")
        elif tag in ("ul", "ol"):
            self.md.append("\n")

    def handle_endtag(self, tag):
        if tag in ("h1", "h2", "h3", "h4"):
            self.md.append("\n")
            self._in_heading = False
        elif tag == "p":
            self.md.append("\n")
        elif tag in ("strong", "b"):
            self._buf += "</strong>"
        elif tag in ("em", "i"):
            self._buf += "</em>"
        elif tag == "a":
            if self._a_href:
                self._buf += f"[{self._a_text}]({self._a_href})"
            self._a_href = None
            self._a_text = ""
        elif tag in ("ul", "ol"):
            self.md.append("\n")

    def handle_data(self, data):
        if self._a_href is not None:
            self._a_text += data
        if self._in_heading:
            self.md.append(data.replace("\xa0", " "))
        else:
            self._buf += data.replace("\xa0", " ")

    def result(self):
        raw = "".join(self.md)
        raw = raw.replace("\xa0", " ")
        # 清理源站用空 <strong> 做缩进产生的 <strong> </strong>
        raw = re.sub(r"<strong>\s*</strong>", "", raw)
        # 清理多余空行
        raw = re.sub(r"\n{3,}", "\n\n", raw)
        lines = [ln.rstrip() for ln in raw.split("\n")]
        # 去掉因源站 &nbsp; 造成的行首缩进(标题行保留)
        lines = [ln.lstrip() if not ln.startswith("#") else ln for ln in lines]
        return "\n".join(lines).strip() + "\n"

def html_to_mdx(html, slug):
    p = MDXBuilder(slug)
    p.feed(html)
    return p.result(), p.imgs

# ---------- 拉取 ----------
def http_get(url, binary=False, retries=4):
    last = None
    for i in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Chrome/124)"})
            r = urllib.request.urlopen(req, timeout=40, context=ctx)
            return r.read() if binary else json.loads(r.read().decode("utf-8", "ignore"))
        except Exception as e:
            last = e
            time.sleep(1.5 ** i)
    raise last

def fetch_content(slug):
    url = f"https://api.helplook.net/api/content/get-content?token={KEY}&slug={slug}"
    d = http_get(url)
    return d.get("data") or {}

def download(url, path: Path):
    data = http_get(url, binary=True)
    path.write_bytes(data)
    return len(data)

def render_mdx(name, body):
    return f'---\ntitle: "{name}"\n---\n\n{body}\n\n<Info>\n  使用指令过程中遇到问题？前往 [八爪鱼RPA 开发者社区问答板块]({COMMUNITY}) 提问，获取官方与社区帮助。\n</Info>\n'

def build_one(slug, bigslug):
    data = fetch_content(slug)
    name = data.get("name", slug)
    html = (data.get("content") or {}).get("content") or ""
    body, imgs = html_to_mdx(html, slug)
    out_dir = CUSTOM / bigslug
    img_dir = out_dir / "images"
    out_dir.mkdir(parents=True, exist_ok=True)
    img_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / f"{slug}.mdx").write_text(render_mdx(name, body), encoding="utf-8")
    for src, local in imgs:
        try:
            download(src, img_dir / local)
        except Exception as e:
            print(f"    [img FAIL] {local}: {e}")
    return name, len(imgs)

# ---------- tree ----------
def load_tree():
    return json.loads((TMP / "tree.json").read_text(encoding="utf-8"))["data"]["list"]

def find_node(tree, slug):
    for n in tree:
        if n.get("slug") == slug:
            return n
        r = find_node(n.get("child", []), slug)
        if r:
            return r
    return None

def collect_children(slug):
    node = find_node(load_tree(), slug)
    res = []
    if not node:
        return res
    def walk(n):
        for c in n.get("child", []):
            if c.get("type") == "2":
                res.append((c["slug"], c.get("name")))
            walk(c)
    walk(node)
    return res

def build_big(bigslug, delay=0.15, resume=True):
    kids = collect_children(bigslug)
    out_dir = CUSTOM / bigslug
    out_dir.mkdir(parents=True, exist_ok=True)
    done = 0
    for slug, name in kids:
        target = out_dir / f"{slug}.mdx"
        if resume and target.exists():
            done += 1
            continue
        try:
            _, n = build_one(slug, bigslug)
            print(f"  OK {slug} ({name}) imgs={n}")
        except Exception as e:
            print(f"  FAIL {slug}: {e}")
        if delay:
            time.sleep(delay)
    new = len(kids) - done
    print(f"大分类 {bigslug}: 子指令 {len(kids)} 篇, 本次新增 {new}")
    return len(kids)

if __name__ == "__main__":
    if not KEY:
        print("ERROR: 需要 HELPLOOK_API_KEY"); sys.exit(1)
    mode = sys.argv[1] if len(sys.argv) > 1 else ""
    if mode == "one" and len(sys.argv) >= 4:
        name, n = build_one(sys.argv[2], sys.argv[3])
        print(f"=== 生成: {name} 图片={n} ===")
    elif mode == "big" and len(sys.argv) >= 3:
        build_big(sys.argv[2])
    elif mode == "all":
        # 只遍历本地已有的大分类占位页(137个, 已排除用户删除的3个)
        bigs = sorted([p.stem for p in CUSTOM.glob("*.mdx") if p.stem != "custom-commands"])
        print("全量本地大分类数:", len(bigs))
        total = 0
        for i, b in enumerate(bigs, 1):
            print(f"[{i}/{len(bigs)}] === {b} ===")
            try:
                n = build_big(b, delay=0.25, resume=True)
                total += n
            except Exception as e:
                print("big FAIL", b, e)
        print("全部完成, 子指令总数(含已生成):", total)
    else:
        print(__doc__)
