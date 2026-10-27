# 引经据典 skill

给一句话，从本地经典语料库（圣经和合本 + 论语/孟子/诗经/增广贤文等 4.2 万条）里检索语义贴近的原句，直接引用。

## 用法
消息末尾加字母 `g` 触发，例如 `人走茶凉g`。

```bash
cd scripts
python3 quote.py "你在这里做什么" -n 12
python3 quote.py "信 诺 言 诚" -n 12        # 直搜不贴切时拆成文言关键词
```

## 依赖
```bash
pip install jieba opencc-python-reimplemented
```

## 结构
- `SKILL.md`：触发规则与检索流程
- `scripts/quote.py`：BM25 检索（jieba 分词 + 单字/bigram + 繁简转换），索引支持 `.pkl` 和 `.pkl.gz`
- `scripts/build_index.py`：重建索引
- `data/index.pkl.gz`：预建索引（压缩版 6.9M，脚本自动读取）
- `data/corpus/`：语料（圣经 66 卷 31101 节 + 14 种古书）
- `data/corpus/bible_CUNPS.json.gz`：圣经原始抓取数据（压缩版）

索引已随仓库提供，克隆后可直接用；改了语料再跑 build_index.py 重建（会生成未压缩的 index.pkl）。
