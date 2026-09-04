# -*- coding: utf-8 -*-
"""
HelpLook 自定义指令子页面抓取器
用法:
  python _helplook/scraper.py explore <slug>            # 抓取单篇原始 JSON 到 _helplook/explore_<slug>.json
  python _helplook/scraper.py tree                      # 抓取整站内容树到 _helplook/tree.json
  python _helplook/scraper.py scrape <slug> [--parent]  # 抓取某大分类(slug)下所有子指令, 生成子页面+图片

API KEY: 通过环境变量 HELPLOOK_API_KEY 传入, 或通过第一个位置参数传入。
"""
import os
import sys
import json
import ssl
import shutil
import urllib.request
import urllib.parse
from pathlib import Path
from html.parser import HTMLParser
import re

API_BASE = "https://api.helplook.net/api"
REPO = Path(r"C:/Users/1/Documents/bazhuayu-rpa-docs")
CUSTOM_DIR = REPO / "commands" / "custom-commands"
TMP = REPO / "_helplook"
TMP.mkdir(exist_ok=True)

SSL_CTX = ssl.create_default_context()

API_KEY = os.environ.get("HELPLOOK_API_KEY") or (sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith(("explore", "tree", "scrape")) else "")


def fetch_json(path, params=None, use_token=False):
    url = API_BASE + path
    if params:
        url += "?" + urllib.parse.urlencode(params)
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/124.0"}
    if use_token:
        headers["x-api-key"] = API_KEY
    else:
        # get-content 用 token 参数, 列表用 x-api-key header
        headers["x-api-key"] = API_KEY
    req = urllib.request.Request(url, headers=headers)
    resp = urllib.request.urlopen(req, timeout=30, context=SSL_CTX)
    return json.loads(resp.read().decode("utf-8", errors="ignore"))


def get_content(slug):
    # 同时尝试 token 参数与 x-api-key 两种方式
    for use_tok in (False, True):
        try:
            data = fetch_json("/content/get-content", {"slug": slug}, use_token=use_tok)
            if data.get("code") == 200 and data.get("data"):
                return data["data"]
        except Exception as e:
            print("  get-content err:", e)
    return None


def cmd_explore(slug):
    d = get_content(slug)
    out = TMP / f"explore_{slug}.json"
    out.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")
    print("saved", out)
    if d:
        print("keys:", list(d.keys()))
        print("name:", d.get("name"))
        c = d.get("content") or {}
        if isinstance(c, dict):
            print("content keys:", list(c.keys()))


def cmd_tree():
    data = fetch_json("/content", use_token=True)
    out = TMP / "tree.json"
    out.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print("saved", out, "code=", data.get("code"))


if __name__ == "__main__":
    if not API_KEY:
        print("ERROR: 需要 API KEY。设置环境变量 HELPLOOK_API_KEY 或作为首个参数传入。")
        sys.exit(1)
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "explore" and len(sys.argv) > 2:
        cmd_explore(sys.argv[2])
    elif cmd == "tree":
        cmd_tree()
    elif cmd == "scrape" and len(sys.argv) > 2:
        print("scrape 逻辑待确认真实数据后实现")
    else:
        print(__doc__)
