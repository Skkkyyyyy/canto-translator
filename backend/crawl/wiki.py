import re
import wikipediaapi
import pandas as pd

CJK = re.compile(r'[一-鿿]')
ENTRY_RE = re.compile(r'^\d+\.\s+(.*)$')
PAIR_RE = re.compile(r"([A-Za-z][A-Za-z0-9 .'-]*?)\s*\(\s*([^()]*[一-鿿][^()]*?)\s*\)")


def strip_tone(romanized: str) -> str:
    romanized = re.sub(r'\d', '', romanized)
    return re.sub(r'\s+', ' ', romanized).strip().lower()


def parse_entries(text: str, source: str):
    category = ""
    rows = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        m = ENTRY_RE.match(line)
        if not m:
            # a short, Chinese-free line between entries is treated as the section header
            if not CJK.search(line) and len(line) < 60 and "=" not in line:
                category = line
            continue

        body = m.group(1)
        term_part, _, gloss = body.partition(" - ")
        gloss = gloss.strip().rstrip(".")

        pairs = PAIR_RE.findall(term_part)
        if not pairs:
            continue

        romanized_list = [strip_tone(r) for r, _ in pairs]
        cantonese_list = [c.strip() for _, c in pairs]
        primary_romanized, primary_cantonese = romanized_list[0], cantonese_list[0]
        # later pairs are spelling *variants* only if they share the same Cantonese word;
        # different Cantonese words in one entry (e.g. male/female forms) are separate items
        variants = sorted(set(
            r for r, c in zip(romanized_list[1:], cantonese_list[1:]) if c == primary_cantonese
        ))

        rows.append({
            "Type": "phrase" if " " in primary_romanized else "token",
            "Category": category,
            "Romanized": primary_romanized,
            "Variants": ",".join(variants),
            "Cantonese": primary_cantonese,
            "Mandarin": "",
            "English": gloss,
            "Source": source,
        })
        for r, c in list(zip(romanized_list, cantonese_list))[1:]:
            if c != primary_cantonese:
                rows.append({
                    "Type": "phrase" if " " in r else "token",
                    "Category": category,
                    "Romanized": r,
                    "Variants": "",
                    "Cantonese": c,
                    "Mandarin": "",
                    "English": gloss,
                    "Source": source,
                })

    df = pd.DataFrame(rows)
    return df.drop_duplicates(subset=["Cantonese"], keep="first")


def fetch_page(title: str) -> str:
    wiki = wikipediaapi.Wikipedia(
        user_agent='canto(sally1152005@gmail.com)',
        language='en',
        extract_format=wikipediaapi.ExtractFormat.WIKI
    )
    page = wiki.page(title)
    if not page.exists():
        raise ValueError(f"Wikipedia page not found: {title}")
    return page.text


if __name__ == "__main__":
    title = "Hong Kong slang"  # redirects to the "Hong Kong slanguage" article
    text = fetch_page(title)
    entries = parse_entries(text, source="wikipedia:Hong_Kong_slanguage")
    out_path = "crawl/wiki_hongkong_slanguage.csv"
    entries.to_csv(out_path, index=False)
    print(f"Parsed {len(entries)} glossary entries from '{title}' -> {out_path}")
    print(entries["Category"].value_counts().to_string())
