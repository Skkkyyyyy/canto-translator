"""
端到端翻译质量评测。两组对照，按 category 分层。

原本试过第三组「音系键」检索（phonkey.py 替代/增强 fuzzy 匹配），实测更差
(0.613 vs 0.640，n=37)，已回退——见 rag.py 顶部注释。现在只保留两组：

  none    不给检索结果        -> 回答「LLM 自己到底行不行」
  legacy  fuzzy 匹配 master   -> rag.py（唯一在用的检索实现）

那一轮花钱跑出来的 new_output 结果备份在 eval_results_with_phonkey_arm.csv.bak
（37 行都有输出）——下次 run/save 会把 eval_results.csv 里的 new_* 列丢弃，
需要那份数据请去 .bak 文件里找，不要指望它还在主文件里。

两种打分
--------
  人工 y/n   准确率。慢，但是唯一可信的判断。填 eval_results.csv 的 *_correct 列。
  自动 charF 字级 F1。免费、可以随时跑，但测不出语序——只看趋势，别当结论。

用法
----
  python eval/ablation.py run                    # 干跑：算要花多少次调用，不联网
  python eval/ablation.py run --go               # 真跑，只补空缺的格子
  python eval/ablation.py run --go --arms legacy # 只跑某一组
  python eval/ablation.py run --go --limit 5     # 先跑 5 题试水
  python eval/ablation.py score               # 出报告（人工 + 自动）
"""
import argparse
import csv
import os
import sys
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

TEST_SET = os.path.join(HERE, "test_set.csv")
RESULTS = os.path.join(HERE, "eval_results.csv")
ARMS = ["none", "legacy"]
FIELDS = ["category", "query", "ref_cantonese", "ref_mandarin", "ref_english"] + \
         [f"{a}_{s}" for a in ARMS for s in ("output", "correct")]


# ---------------------------------------------------------------- 三组检索
# 之前试过第三组「音系键」检索(phonkey.py)，端到端评测比这里的 fuzzy 匹配差
# (0.613 vs 0.640，n=37) —— 撞车时会给模型一个自信的错答案，比不给结果更伤。
# 已回退，phonkey.py 还在但没接线。只留 none/legacy 两组，避免这个文件
# 陪着一起复杂化。
LEGACY_PREAMBLE = (
    "How to weigh the retrieved glossary matches:\n"
    "- token_matches and sentence_matches are candidate interpretations retrieved by string matching, not guaranteed correct — use judgment, don't just concatenate them\n"
    "- match_type \"direct\" (score 100) means the input exactly matches a known spelling; \"fuzzy\" means an approximate match — treat fuzzy matches, especially at lower scores, as less certain\n"
    "- If a sentence_match has a high score, it means this input closely matches a previously verified full sentence — prefer its given Cantonese/Mandarin translation as a whole over reconstructing the sentence from individual token_matches\n"
    "- token_matches can overlap: a multi-word phrase match (e.g. \"duk mm duk\" -> 得唔得) and a shorter single-word match contained within it (e.g. \"duk\" -> 戳/poke) may both be retrieved for the same input. When this happens, the longer phrase-level match reflects the actual compound meaning and should win — do not fall back to the shorter word's literal meaning\n"
    "- Multiple matches that map to the same Cantonese/Mandarin meaning (different spellings of the same word) reinforce each other and increase confidence in that reading, they are not conflicting alternatives\n"
)


def build_context(arm: str, text: str) -> str:
    if arm == "none":
        return ""
    if arm == "legacy":
        from rag import rag
        return f"{LEGACY_PREAMBLE}\nRetrieved glossary matches:\n{rag(text)}"
    raise ValueError(arm)


# ---------------------------------------------------------------- 自动打分
def char_f1(pred: str, ref: str) -> float:
    """字级 F1。测不出语序——两句用字相同顺序全乱也是满分，只用来看趋势。"""
    p = Counter(c for c in pred if c.strip())
    r = Counter(c for c in ref if c.strip())
    if not p or not r:
        return 0.0
    hit = sum((p & r).values())
    prec, rec = hit / sum(p.values()), hit / sum(r.values())
    return 0.0 if prec + rec == 0 else 2 * prec * rec / (prec + rec)


def parse_output(raw: str):
    """从 LLM 输出里抠出三行（prompt 要求 粵語：/ 普通話：/ English：）。"""
    import re
    pats = {
        "cantonese": r"(?:粵語|粤语)\s*[:：]\s*(.+)",
        "mandarin": r"(?:普通話|普通话)\s*[:：]\s*(.+)",
        "english": r"English\s*[:：]\s*(.+)",
    }
    return {k: (m.group(1).strip() if (m := __import__("re").search(p, raw or "")) else "")
            for k, p in pats.items()}


# ---------------------------------------------------------------- IO
def load_results():
    if not os.path.exists(RESULTS):
        return seed_from_test_set()
    return list(csv.DictReader(open(RESULTS, encoding="utf-8-sig")))


def seed_from_test_set():
    rows = []
    for c in csv.DictReader(open(TEST_SET, encoding="utf-8-sig")):
        if not (c.get("Sentence") or "").strip():
            continue
        r = {f: "" for f in FIELDS}
        r.update(category=c.get("category", ""), query=c["Sentence"].strip(),
                 ref_cantonese=c.get("Cantonese", ""), ref_mandarin=c.get("Mandarin", ""),
                 ref_english=c.get("English", ""))
        rows.append(r)
    return rows


def save(rows):
    # extrasaction="ignore": 旧结果文件可能带着已弃用的 new_output/new_correct
    # 列（上一轮试验留下的），忽略它们而不是报错，但也不主动删——保留原始数据。
    with open(RESULTS, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


# ---------------------------------------------------------------- run
def cmd_run(args):
    rows = load_results()
    arms = [a.strip() for a in args.arms.split(",") if a.strip()]
    keep = lambda r: not args.category or r["category"] in args.category.split(",")
    # --redo 覆盖已有输出。改了 prompt 之后必须用它，旧输出是另一个 prompt 跑的，不可比。
    todo = [(i, a) for i, r in enumerate(rows) if keep(r) for a in arms
            if args.redo or not (r.get(f"{a}_output") or "").strip()]
    if args.limit:
        todo = todo[:args.limit]

    sel = [r for r in rows if keep(r)]
    have = {a: sum(1 for r in sel if (r.get(f"{a}_output") or "").strip()) for a in arms}
    print(f"{len(sel)} 题 × {len(arms)} 组" + (f"  (category={args.category})" if args.category else ""))
    print(f"已有输出: {have}")
    print(f"需要调用: {len(todo)} 次")

    if not args.go:
        print("\n干跑，没有联网。确认后加 --go 真跑。")
        if todo:
            i, a = next(((i, a) for i, a in todo if a != "none"), todo[0])
            print(f"\n预览 [{a}] {rows[i]['query']}")
            ctx = build_context(a, rows[i]["query"])
            print("  " + str(ctx).replace("\n", "\n  ")[:600])
        return

    from llm_service import llm
    for n, (i, a) in enumerate(todo, 1):
        q = rows[i]["query"]
        print(f"[{n}/{len(todo)}] {a:6} {q[:46]}")
        try:
            rows[i][f"{a}_output"] = llm(q, context=build_context(a, q), verbose=False)
        except Exception as e:
            print(f"  失败：{e}")
            rows[i][f"{a}_output"] = f"ERROR: {e}"
        save(rows)                      # 每题写一次，中断不丢进度
    print(f"\n写入 {RESULTS}")
    print("人工判分：打开它，对照 ref_* 列，把 *_correct 填 y/n，然后 score")


# ---------------------------------------------------------------- score
def cmd_score(args):
    rows = load_results()
    if args.category:
        rows = [r for r in rows if r["category"] in args.category.split(",")]
    cats = sorted({r["category"] or "uncategorized" for r in rows})

    # --- 人工 y/n
    manual = defaultdict(lambda: defaultdict(lambda: [0, 0]))
    for r in rows:
        c = r["category"] or "uncategorized"
        for a in ARMS:
            v = (r.get(f"{a}_correct") or "").strip().lower()
            if v in ("y", "n"):
                manual[c][a][1] += 1
                manual[c][a][0] += v == "y"

    annotated = sum(manual[c][a][1] for c in cats for a in ARMS)
    print("=" * 68)
    print("人工判分（唯一可信的口径）")
    print("=" * 68)
    if not annotated:
        print("  还没有标注。把 eval_results.csv 的 *_correct 列填 y/n 再跑。")
    else:
        print(f"{'category':14}" + "".join(f"{a:>14}" for a in ARMS))
        for c in cats + ["__总计__"]:
            cells = []
            for a in ARMS:
                if c == "__总计__":
                    ok = sum(manual[x][a][0] for x in cats); tot = sum(manual[x][a][1] for x in cats)
                else:
                    ok, tot = manual[c][a]
                cells.append(f"{ok}/{tot}={ok/tot:.0%}" if tot else "—")
            print(f"{c:14}" + "".join(f"{x:>14}" for x in cells))

    # --- 自动 charF
    print("\n" + "=" * 68)
    print("自动字级 F1（免费但测不出语序，只看趋势）")
    print("=" * 68)
    auto = defaultdict(lambda: defaultdict(list))
    for r in rows:
        c = r["category"] or "uncategorized"
        for a in ARMS:
            out = (r.get(f"{a}_output") or "").strip()
            ref = (r.get("ref_cantonese") or "").strip()
            if out and ref and not out.startswith("ERROR:"):
                auto[c][a].append(char_f1(parse_output(out)["cantonese"], ref))
    print(f"{'category':14}" + "".join(f"{a:>14}" for a in ARMS))
    for c in cats + ["__总计__"]:
        cells = []
        for a in ARMS:
            xs = [v for x in cats for v in auto[x][a]] if c == "__总计__" else auto[c][a]
            cells.append(f"{sum(xs)/len(xs):.3f}(n={len(xs)})" if xs else "—")
        print(f"{c:14}" + "".join(f"{x:>14}" for x in cells))

    tot = {a: [v for c in cats for v in auto[c][a]] for a in ARMS}
    if tot["none"] and tot["legacy"]:
        d = sum(tot["legacy"]) / len(tot["legacy"]) - sum(tot["none"]) / len(tot["none"])
        print(f"\n检索的净贡献 (legacy − none): {d:+.3f}")
        if d < 0.02:
            print("  → 检索基本没帮上忙。先别扩词表，去看 prompt 和模型选择。")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run"); r.set_defaults(fn=cmd_run)
    r.add_argument("--go", action="store_true", help="真的调 LLM（会花钱）")
    r.add_argument("--arms", default=",".join(ARMS))
    r.add_argument("--limit", type=int)
    r.add_argument("--category", help="只跑某些 category，逗号分隔")
    r.add_argument("--redo", action="store_true", help="覆盖已有输出（改了 prompt 后必须用）")
    s = sub.add_parser("score"); s.set_defaults(fn=cmd_score)
    s.add_argument("--category", help="只统计某些 category，逗号分隔")
    a = ap.parse_args()
    a.fn(a)
