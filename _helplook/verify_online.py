# -*- coding: utf-8 -*-
import urllib.request, ssl, time
ctx = ssl.create_default_context()
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"}
base = "https://rpa.bazhuayu.com/helpcenter/"

def check(u):
    try:
        req = urllib.request.Request(base + u, headers=UA)
        r = urllib.request.urlopen(req, timeout=30, context=ctx)
        return r.status
    except urllib.error.HTTPError as e:
        return e.code
    except Exception as e:
        return "ERR"

tests = {
    "Xtu3Dyv8 文件扩展功能 (group)": "commands/custom-commands/Xtu3Dyv8",
    "i2Vbj6Mp 验证码 (group)": "commands/custom-commands/i2Vbj6Mp",
    "VELzT4An 文本扩展功能": "commands/custom-commands/VELzT4An",
    "新增 LqGka251": "commands/custom-commands/LqGka251",
    "新增 q1cyRlx9": "commands/custom-commands/q1cyRlx9",
    "新增 zaP6Z9qv": "commands/custom-commands/zaP6Z9qv",
    "删除的旧 3UkAyWdw (应404)": "commands/custom-commands/3UkAyWdw",
    "删除的旧 xvQDnY8i (应404)": "commands/custom-commands/xvQDnY8i",
    "旧 slug redirect /commands/3UkAyWdw (应404或308)": "commands/3UkAyWdw",
    "子指令 sUuGTZYW": "commands/custom-commands/geamt8fB/sUuGTZYW",
    "子指令 dS9s1k7L": "commands/custom-commands/Xtu3Dyv8/dS9s1k7L",
}

for i in range(4):
    time.sleep(15)
    results = {k: check(v) for k, v in tests.items()}
    print(f"--- check {i+1} ---")
    for k, v in results.items():
        print(v, k)
    ok_200 = [k for k, v in results.items() if v == 200]
    ok_404 = [k for k, v in results.items() if v == 404]
    print("预期200:", len(ok_200), "预期404:", len(ok_404))
    if len(ok_200) >= 7:
        print("部署完成")
        break
