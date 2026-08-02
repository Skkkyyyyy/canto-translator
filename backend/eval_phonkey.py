"""
规则收敛的评测。三个指标，都从现有数据自动推出，不需要额外标注。

A. 同字异拼收敛率 —— 词表里指向同一个漢字的多行，是不是收敛到同一个 key？
   ground truth 白送：CSV 的 Cantonese 列就是答案。
B. 句子覆盖率 —— sentences.csv 的 token 有多少能查到？现状 vs 音系键。
C. 碰撞率 —— 一个 key 平均对多少个不同的漢字？（召回的代价）
"""
import csv, sys
from collections import defaultdict
from difflib import SequenceMatcher
from phonkey import phon_key

from pathlib import Path

DATA = Path(__file__).parent / "data"
GLOSS = DATA / "glossary_master.csv"
SENTS = DATA / "sentences.csv"
FUZZ_THRESHOLD = 90          # 旧 rag.py 的阈值


def fuzz(a, b):
    return round(100 * SequenceMatcher(None, a, b).ratio())


def load_gloss():
    """返回 [(拼写, 漢字)]。master 的 Romanized 是主拼写，Variants 是逗号分隔的异拼。"""
    out = []
    for r in csv.DictReader(open(GLOSS, encoding="utf-8-sig")):
        c = (r.get("Cantonese") or "").strip()
        for col in ("Romanized", "Variants"):
            raw = (r.get(col) or "").strip()
            if not raw or raw.lower() == "nan":
                continue
            for t in (raw.split(",") if col == "Variants" else [raw]):
                t = t.strip().lower()
                if t:
                    out.append((t, c))
    return out


# ------------------------------------------------- A. 同字异拼收敛率
def eval_convergence(gloss):
    by_char = defaultdict(set)
    for tok, canto in gloss:
        if canto:
            by_char[canto].add(tok)
    groups = {c: ts for c, ts in by_char.items() if len(ts) > 1}

    old_ok = new_ok = 0
    detail = []
    for canto, toks in sorted(groups.items()):
        ts = sorted(toks)
        keys = {phon_key(t) for t in ts}
        new = len(keys) == 1
        # 现状：任意两个变体的 fuzz 是否都过阈值
        old = all(fuzz(a, b) >= FUZZ_THRESHOLD for i, a in enumerate(ts) for b in ts[i + 1:])
        old_ok += old
        new_ok += new
        detail.append((canto, ts, old, new, sorted(keys)))
    return groups, old_ok, new_ok, detail


# ------------------------------------------------- B. 句子 token 覆盖率
def eval_coverage(gloss):
    sents = list(csv.DictReader(open(SENTS, encoding="utf-8-sig")))
    gloss_toks = [t for t, _ in gloss]
    key_index = defaultdict(list)
    for t, c in gloss:
        key_index[phon_key(t)].append((t, c))

    tot = old_hit = new_hit = 0
    only_new = []
    for row in sents:
        s = (row["Sentence"] or "").strip().lower()
        if not s:
            continue
        for w in s.split():
            w = "".join(ch for ch in w if ch.isalnum())
            if not w:
                continue
            tot += 1
            o = any(fuzz(g, w) >= FUZZ_THRESHOLD for g in gloss_toks)
            n = phon_key(w) in key_index
            old_hit += o
            new_hit += n
            if n and not o:
                only_new.append((w, key_index[phon_key(w)][0]))
    return tot, old_hit, new_hit, only_new


# ------------------------------------------------- C. 碰撞率
def eval_collision(gloss):
    key_chars = defaultdict(set)
    for t, c in gloss:
        if c:
            key_chars[phon_key(t)].add(c)
    multi = {k: v for k, v in key_chars.items() if len(v) > 1}
    avg = sum(len(v) for v in key_chars.values()) / max(len(key_chars), 1)
    return key_chars, multi, avg


if __name__ == "__main__":
    gloss = load_gloss()
    print(f"词表 {len(gloss)} 行\n")

    groups, old_ok, new_ok, detail = eval_convergence(gloss)
    print("=" * 64)
    print(f"A. 同字异拼收敛率   ({len(groups)} 组同字多拼)")
    print("=" * 64)
    for canto, ts, old, new, keys in detail:
        mark = lambda b: "✓" if b else "✗"
        print(f"  {canto:6} {str(ts):46} 现状{mark(old)}  音系键{mark(new)} {keys if not new else ''}")
    print(f"\n  现状  {old_ok}/{len(groups)} = {100*old_ok/len(groups):.0f}%")
    print(f"  音系键 {new_ok}/{len(groups)} = {100*new_ok/len(groups):.0f}%")

    tot, old_hit, new_hit, only_new = eval_coverage(gloss)
    print("\n" + "=" * 64)
    print(f"B. sentences.csv token 覆盖率  (共 {tot} 个 token)")
    print("=" * 64)
    print(f"  现状   {old_hit:3}/{tot} = {100*old_hit/tot:.0f}%")
    print(f"  音系键 {new_hit:3}/{tot} = {100*new_hit/tot:.0f}%")
    print(f"\n  新命中的（现状漏掉）：")
    seen = set()
    for w, (t, c) in only_new:
        if w in seen:
            continue
        seen.add(w)
        print(f"    {w:12} -> 词表[{t}] {c}")

    key_chars, multi, avg = eval_collision(gloss)
    print("\n" + "=" * 64)
    print(f"C. 碰撞率")
    print("=" * 64)
    print(f"  {len(key_chars)} 个不同 key，平均 {avg:.2f} 个漢字/key")
    print(f"  发生碰撞的 key: {len(multi)}")
    for k, v in sorted(multi.items()):
        print(f"    {k:12} -> {sorted(v)}")
