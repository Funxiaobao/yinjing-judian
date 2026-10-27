#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""引经据典：给一句话，找经典著作里最接近的原句。

用法:
  python3 quote.py "我想说的话"           # 默认 5 条
  python3 quote.py "..." -n 8 --book 圣经  # 限定来源（支持 圣经/论语/孟子/诗经/增广贤文…）
  python3 quote.py "..." --json           # 机器可读
查不到就输出 NOT_FOUND，绝不编造。
"""
import argparse, gzip, json, math, os, pickle, re, sys
from collections import defaultdict

import jieba

HERE = os.path.dirname(os.path.abspath(__file__))
IDX = os.path.join(HERE, "..", "data", "index.pkl")
IDX_GZ = IDX + ".gz"

STOP = set("的 了 着 是 在 和 与 也 吗 呢 吧 啊 这 那 就 都 很 我 你 他 她 它 们 一 个 有 不 之 而 其 以 为 於 于 也 矣 焉 哉 乎 兮 者 所 则 曰 云".split())
K1, B = 1.5, 0.75


def tokens(s):
    s = re.sub(r"[^\u4e00-\u9fffA-Za-z0-9]", "", s)
    out = [w for w in jieba.lcut(s) if w not in STOP and len(w) >= 2]
    out += [s[i:i + 2] for i in range(len(s) - 1)]
    out += list(s)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("query")
    ap.add_argument("-n", type=int, default=12)
    ap.add_argument("--book", default="")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--min", type=float, default=1.0, help="最低分阈值")
    a = ap.parse_args()

    if os.path.exists(IDX):
        fh = open(IDX, "rb")
    elif os.path.exists(IDX_GZ):
        fh = gzip.open(IDX_GZ, "rb")
    else:
        print("索引不存在，请先运行 build_index.py", file=sys.stderr)
        sys.exit(2)
    with fh:
        d = pickle.load(fh)
    quotes, post, dl, avgdl, idf = d["quotes"], d["post"], d["dl"], d["avgdl"], d["idf"]

    q = tokens(a.query)
    if not q:
        print("NOT_FOUND")
        return
    qterms = list(dict.fromkeys(q))
    scores = defaultdict(float)
    hitcnt = defaultdict(int)
    for w in qterms:
        pl = post.get(w)
        if not pl:
            continue
        w_idf = idf[w]
        for i, tf in pl:
            norm = tf * (K1 + 1) / (tf + K1 * (1 - B + B * dl[i] / avgdl))
            scores[i] += w_idf * norm
            hitcnt[i] += 1
    # 覆盖率优先：查询词命中越少越不可信，扣得狠
    res = [(s * (hitcnt[i] / len(qterms)) ** 2.0, i, hitcnt[i] / len(qterms))
           for i, s in scores.items()]
    res = [r for r in res if r[2] >= 0.2]
    res.sort(reverse=True)

    picked, per_src = [], defaultdict(int)
    for sc, i, cov in res:
        t, src, ref = quotes[i]
        if a.book and a.book not in src:
            continue
        if sc < a.min:
            break
        if per_src[src] >= max(2, a.n // 2):
            continue
        if any(t in p[0] or p[0] in t for p in picked):
            continue
        picked.append((t, src, ref, sc))
        per_src[src] += 1
        if len(picked) >= a.n:
            break

    if not picked:
        print("NOT_FOUND")
        return
    if a.json:
        print(json.dumps([{"text": t, "source": s, "ref": r, "score": round(sc, 2)}
                          for t, s, r, sc in picked], ensure_ascii=False, indent=1))
        return
    for t, s, r, sc in picked:
        print("「%s」\n  ——%s（%.1f）" % (t, r, sc))


if __name__ == "__main__":
    main()
