#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""构建引经据典语料库与检索索引。"""
import json, os, re, pickle, sys
from collections import defaultdict

import jieba
import opencc

HERE = os.path.dirname(os.path.abspath(__file__))
CORPUS = os.path.join(HERE, "..", "data", "corpus")
CP = os.path.join(CORPUS, "chinese-poetry")
OUTDIR = "/AstrBot/data/skills/yinjing-judian/data"
os.makedirs(OUTDIR, exist_ok=True)
cc = opencc.OpenCC("t2s")

STOP = set("的 了 着 是 在 和 与 也 吗 呢 吧 啊 这 那 就 都 很 我 你 他 她 它 们 一 个 有 不 之 而 其 以 为 於 于 也 矣 焉 哉 乎 兮 者 所 则 曰 云".split())

quotes = []  # (text, src, ref)

def add(text, src, ref):
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    text = cc.convert(text)
    text = re.sub(r"(.)\1{3,}", r"\1\1", text)  # 去掉 "主 主 主"
    text = text.strip()
    if len(text) < 4:
        return
    quotes.append((text, src, ref))

# ---------- 圣经 ----------
bp = os.path.join(CORPUS, "bible_CUNPS.json")
if os.path.exists(bp):
    d = json.load(open(bp, encoding="utf-8"))
    for bookid, bname, ch, verses in d["books"]:
        for v, t in verses:
            add(t, "圣经", "%s %d:%d" % (bname, ch, v))
    print("圣经 ok", len(quotes), flush=True)
else:
    print("!! 圣经语料缺失", flush=True)

# ---------- 论语 ----------
d = json.load(open(os.path.join(CP, "lunyu", "lunyu.json"), encoding="utf-8"))
for ch in d:
    for i, para in enumerate(ch["paragraphs"], 1):
        for s in re.split(r"(?<=[。！？])", para):
            if s.strip():
                add(s, "论语", "论语·%s 第%d则" % (ch["chapter"], i))

# ---------- 四书 ----------
for fn, book in [("mengzi.json", "孟子"), ("daxue.json", "大学"), ("zhongyong.json", "中庸")]:
    d = json.load(open(os.path.join(CP, "sishuwujing", fn), encoding="utf-8"))
    if isinstance(d, dict):
        d = [d]
    for ch in d:
        for para in ch["paragraphs"]:
            for s in re.split(r"(?<=[。！？])", para):
                if s.strip():
                    add(s, book, "%s·%s" % (book, ch.get("chapter", "")))

# ---------- 诗经 ----------
d = json.load(open(os.path.join(CP, "shijing", "shijing.json"), encoding="utf-8"))
for poem in d:
    for seg in poem["content"]:
        add(seg, "诗经", "诗经·%s·%s·%s" % (poem.get("chapter", ""), poem.get("section", ""), poem["title"]))

# ---------- 蒙学 / 格言 ----------
MENG = {
    "sanzijing-new.json": "三字经", "dizigui.json": "弟子规", "qianziwen.json": "千字文",
    "zengguangxianwen.json": "增广贤文", "zhuzijiaxun.json": "朱子家训",
    "shenglvqimeng.json": "声律启蒙", "youxueqionglin.json": "幼学琼林",
    "wenzimengqiu.json": "文字蒙求", "baijiaxing.json": "百家姓", "qianjiashi.json": "千家诗",
    "tangshisanbaishou.json": "唐诗三百首", "guwenguanzhi.json": "古文观止",
}
for fn, book in MENG.items():
    p = os.path.join(CP, "mengxue", fn)
    if not os.path.exists(p):
        continue
    d = json.load(open(p, encoding="utf-8"))
    items = d if isinstance(d, list) else [d]
    for it in items:
        blocks = it.get("content", []) if isinstance(it, dict) else []
        if isinstance(blocks, list):
            for b in blocks:
                if isinstance(b, dict):
                    for para in b.get("paragraphs", []):
                        if fn in ("sanzijing-new.json", "dizigui.json"):
                            add(para, book, "%s·%s" % (book, b.get("chapter", "")))
                        else:
                            for s in re.split(r"(?<=[。！？])", para):
                                if s.strip():
                                    add(s, book, "%s·%s" % (book, b.get("chapter", "")))
                elif isinstance(b, str):
                    for s in re.split(r"(?<=[。！？])", b):
                        if s.strip():
                            add(s, book, book)

# ---------- 幽梦影 ----------
p = os.path.join(CP, "youmengying", "youmengying.json")
if os.path.exists(p):
    d = json.load(open(p, encoding="utf-8"))
    for it in (d if isinstance(d, list) else [d]):
        for para in it.get("paragraphs", []) if isinstance(it, dict) else []:
            add(para, "幽梦影", "幽梦影")

print("总条目", len(quotes), flush=True)

# ---------- 建索引 ----------
def tokens(s):
    s = re.sub(r"[^\u4e00-\u9fffA-Za-z0-9]", "", s)
    out = [w for w in jieba.lcut(s) if w not in STOP and len(w) >= 2]
    out += [s[i:i + 2] for i in range(len(s) - 1)]
    out += list(s)
    return out

post = defaultdict(list)
dl = []
for i, (t, s, r) in enumerate(quotes):
    tk = tokens(t)
    dl.append(len(tk) or 1)
    tf = defaultdict(int)
    for w in tk:
        tf[w] += 1
    for w, c in tf.items():
        post[w].append((i, c))

N = len(quotes)
avgdl = sum(dl) / N
idf = {w: __import__("math").log(1 + (N - len(v) + 0.5) / (len(v) + 0.5)) for w, v in post.items()}

pickle.dump({"quotes": quotes, "post": dict(post), "dl": dl, "avgdl": avgdl, "idf": idf},
            open(os.path.join(OUTDIR, "index.pkl"), "wb"), protocol=4)
print("索引完成 词条", len(post), "->", OUTDIR, flush=True)
