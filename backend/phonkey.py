"""
罗马化粤语 -> 音系键 (phonetic key)

目的：把同一个粤语音节的多种民间拼法收敛到同一个 key，
     让查表在「没见过的拼法」上也能命中。

重要前提：key 不需要是「正确的粤拼」，只需要**两边一致**。
        输入和词表都过同一个函数，撞到同一个 key 就算命中。
        所以 syu -> sju 这种「不像粤拼」的结果是可以接受的。

规则顺序 = 执行顺序，单趟不迭代。顺序错了会出错，见 test_ordering()。
每条规则后面标了它在 tokens100.csv 里的实测出现次数（evidence）。
"""
import re

# ---------------------------------------------------------------- 层 1 韵腹
# 必须跑在「删 r」前面：yurk 先删 r 会变成 yuk(郁)，是另一个字
NUCLEUS = [
    ("1.1", r"eoi",        "ui",  "eoi->ui   佢 keoi/kui",              0),
    ("1.2", r"ur",         "oe",  "ur->oe    約 yurk / 趕 chur",         3),
    ("1.3", r"eu",         "oe",  "eu->oe    耶鲁拼音残留",              0),  # 语料内 0 次，保留待观察
    ("1.4", r"aa",         "a",   "aa->a     返 faan/fan 长短音不分",     2),
    ("1.5", r"u([mn])",    r"a\1", "um->am    咁 gum / 心 sum，英语 u 读 /ʌ/", 3),
    ("1.6", r"ou",         "o",   "ou->o     好 hou/ho",                 8),
    ("1.7", r"eng",        "ang", "[拼音] eng->ang  可能 horneng",        2),
    ("1.8", r"ao",         "ou",  "[拼音] ao->ou",                       0),
    ("1.9", r"oo",         "u",   "[政府] oo=/u/  出門 chut moon",        1),
]

# ---------------------------------------------------------------- 层 2 韵尾
CODA = [
    ("2.1", r"ck$|c$",     "k",   "词尾 c/ck -> k   得 duc/duk",          2),
    ("2.2", r"([aeiou])r", r"\1", "元音后 r 删除    返 farn / 可 hor",    13),  # 语料内最强信号
    # h 不只在词尾要删：连写时它会跑到词中间。meh si -> mesi 而 mehsi -> mehsi，
    # 两个 key 对不上就破坏了「空格无关」。所以辅音前的 h 也要删。
    ("2.3", r"([aeiou])h(?=[bcdfgjklmnpqrstvwxz]|$)", r"\1",
     "元音后、辅音前或词尾的 h 删除   嘅 geh / 咩事 mehsi", 5),
]

# ---------------------------------------------------------------- 层 3 声母
# 全局替换（不限词首）：民间拼写不标音节边界，gayau 和 ga yau 必须收敛到同一 key
# 3.1 必须早于 3.2，否则 yurk -> jurk -> zurk 声母就错了
ONSET = [
    ("3.0", r"ts",         "z",   "[政府拼音] ts->z  多謝 dor tse / 仔 tsai", 2),
    ("3.1", r"zh",         "z",   "[拼音] zh->z    仲要 zhongyiu",        1),
    ("3.2", r"j",          "z",   "j->z      民间 j 读 /ts/  正 jeng",     9),
    ("3.3", r"y",          "j",   "y->j      粤拼里 /j/ 写作 j  約 yurk",  4),
    ("3.4", r"ch",         "c",   "ch->c     出 chut",                    5),
    ("3.5", r"sh",         "s",   "sh->s     食 shik",                    0),
]

# ------------------------------------------------- Tier 2：高风险，默认关闭
# 能提召回，但碰撞率涨得快。只在 Tier 1 完全没命中时对该位置启用。
TIER2 = [
    ("T2.1", r"^n",        "l",   "n->l  懒音  你 nei/lei",               0),
    ("T2.2", r"ng$",       "n",   "词尾 ng->n  懒音",                     0),
    ("T2.3", r"^ng",       "",    "词首 ng 删除  我 ngo/o",               1),
    ("T2.4", r"gw",        "g",   "gw->g",                                0),
]

RULES = NUCLEUS + CODA + ONSET


def _apply(piece: str, rules) -> str:
    for _id, pat, repl, _desc, _ev in rules:
        piece = re.sub(pat, repl, piece)
    return piece


def phon_key(text: str, tier2: bool = False) -> str:
    """罗马化串 -> 音系键。空格被吃掉（音节边界在民间拼写里完全随意）。"""
    text = text.lower().strip()
    text = re.sub(r"[^\w\s]", " ", text)
    pieces = [p for p in text.split() if p]

    out = []
    for p in pieces:
        p = _apply(p, RULES)
        if tier2:
            p = _apply(p, TIER2)
        out.append(p)
    return "".join(out)          # 无分隔符拼接 -> gayau == ga yau


def jyutping_key(text: str) -> str:
    """粤拼 -> 同一个 key 空间。导入 Rime-Cantonese / words.hk 时用这个，不要用 phon_key。

    为什么要分开两个函数：
      phon_key 假设输入是**民间即兴拼写**，那里 j 读 /ts/（jeng=正），所以有 j->z。
      粤拼里 j 是 /j/ 滑音（jiu=要），套 j->z 会把声母改错。

      要 jiu3   phon_key -> ziu   ❌ 和用户写的 yiu(->jiu) 对不上
                jyutping_key -> jiu ✅

    另外粤拼带声调数字，必须先去掉。不能在 phon_key 里去，
    因为民间拼写的数字是有意义的（on9 的 9 = 鳩，b4 = before）。
    """
    text = re.sub(r"[1-6]", "", text.lower().strip())
    pieces = [p for p in re.sub(r"[^\w\s]", " ", text).split() if p]
    # 跳过 3.2/3.3（j/y 的互换），其余规则与 phon_key 完全相同
    rules = [r for r in RULES if r[0] not in ("3.2", "3.3")]
    return "".join(_apply(p, rules) for p in pieces)


def trace(text: str, tier2: bool = False):
    """逐规则追踪，调试规则顺序用。"""
    steps = []
    pieces = re.sub(r"[^\w\s]", " ", text.lower().strip()).split()
    for p in pieces:
        cur = p
        for _id, pat, repl, desc, _ev in (RULES + TIER2 if tier2 else RULES):
            new = re.sub(pat, repl, cur)
            if new != cur:
                steps.append((p, _id, desc, cur, new))
                cur = new
    return steps, phon_key(text, tier2)


def test_ordering():
    """顺序敏感的三个已知冲突，改规则顺序后必须仍然通过。"""
    cases = [
        ("yurk", "joek", "1.2 必须早于 2.2，否则 yurk->yuk(郁)"),
        ("jeng", "zang", "3.2 必须早于 3.3，否则 jeng 声母错"),  # eng->ang 后 zang
        ("gayau", "gajau", "空格无关：gayau == ga yau，且等于粤拼 gaa1jau2"),
        ("ga yau", "gajau", "同上"),
        ("garyau", "gajau", "2.2 删 r 后与 gayau 收敛"),
        ("duc", "duk", "2.1 词尾 c->k"),
        ("duk", "duk", ""),
        ("farn", "fan", "2.2 删 r"),
        ("faan", "fan", "1.4 aa->a"),
        ("geh", "ge", "2.3 词尾 h 删"),
        ("gum", "gam", "1.5 um->am"),
        ("horneng", "honang", "1.7 拼音 eng->ang + 2.2 删 r"),
        ("hor neng", "honang", "空格无关"),
    ]
    bad = []
    for src, want, why in cases:
        got = phon_key(src)
        if got != want:
            bad.append((src, want, got, why))
    return bad


if __name__ == "__main__":
    bad = test_ordering()
    if bad:
        print("顺序测试失败：")
        for src, want, got, why in bad:
            print(f"  {src:10} 期望 {want:10} 实得 {got:10}  {why}")
    else:
        print("顺序测试全部通过")
