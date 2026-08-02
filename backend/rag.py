"""
检索层：fuzzy 匹配 glossary_master.csv（含 Variants 列）。

本 session 试过用音系归一化(phonkey.py)替代/增强这里的 fuzzy 匹配，
端到端评测(eval/ablation.py)测出来是倒退的：

    自动字级F1   none 0.440   legacy(此文件) 0.640   音系键版本 0.613

原因：音系键召回更高，但撞车时也会给模型一个自信的错答案，
而错误的检索结果比没有检索结果更伤（模型会放弃自己本来对的判断）。
legacy 的 fuzzy(阈值90) 几乎不产生假阳性，代价是只能捞到很有限的变体
（主要是空格差异），查不到时保持沉默——这在此场景下比高召回更重要。

结论：想扩大召回，去补 data/glossary_master.csv 的 Variants 列（人工，
100%精度），不要在这里调低 fuzzy 阈值或换匹配算法——试过，短字符串
（3-5字母，粤语罗马化音节的典型长度）上任何字符串相似度算法的精度
天花板都在 40-50% 左右，因为很多形近的拼写其实是完全不同的词
（nigo=呢個 vs ngo=我），不是同一个词的拼写变体，编辑距离分不出这个
区别。rag_legacy.py 是这份文件更早的冻结副本，两者逻辑相同。
"""
from pathlib import Path
DATA = Path(__file__).parent / "data"

#used in llm_service.py
## normalize user input 
## tokenization V
## sliding window phrase matching V
## direct match 
## fuzzy match
## embedding models + vector DB +  check vector similarity 
from normalizer import normalizer  #from module import function
import nltk
nltk.data.path.append(str(Path(__file__).parent / "nltk_data"))
from nltk.tokenize import word_tokenize
import pandas as pd
from thefuzz import fuzz, process


def rag(text:str):
    #normalize text 
    normalized_text = normalizer(text)
    
    #tokenization
    tokens = word_tokenize(normalized_text)
    
    #sliding window n-grams
    phrases = []
    for n in range(len(tokens),0,-1): #n length: 4 3 2 1
        for start in range(len(tokens) - n + 1): #len(tokens) - n + 1： 找最后无法满足条件的start index
            phrase = " ".join(tokens[start:start+n])
            phrases.append(phrase)

    df_token = pd.read_csv(DATA/'glossary_master.csv')
    df_sentence = pd.read_csv(DATA/'sentences.csv')

    #direct match + fuzzy match, checking the primary Romanized spelling plus any known variants
    matches_token = []
    for _, row in df_token.iterrows():
        spellings = [str(row["Romanized"]).strip().lower()]
        variants = str(row.get("Variants", "")).strip()
        if variants and variants.lower() != "nan":
            spellings += [v.strip().lower() for v in variants.split(",") if v.strip()]

        best = None
        for spelling in spellings:
            for phrase in phrases:
                if spelling == phrase:
                    candidate = (100, phrase, "direct")
                elif fuzz.ratio(spelling, phrase) >= 90:
                    candidate = (fuzz.ratio(spelling, phrase), phrase, "fuzzy")
                else:
                    continue
                if best is None or candidate[0] > best[0]:
                    best = candidate

        if best:
            score, matched_phrase, match_type = best
            matches_token.append({
                "token": row["Romanized"],
                "cantonese": row.get("Cantonese", ""),
                "mandarin": row.get("Mandarin", ""),
                "english": row.get("English", ""),
                "category": row.get("Category", ""),
                "matched_phrase": matched_phrase,
                "match_type": match_type,
                "score": score
            })
    matches_token.sort(key=lambda m: m["score"], reverse=True)

    matches_sentence = []
    for _, row in df_sentence.iterrows():
        sentence = str(row['Sentence']).strip().lower()
        score = fuzz.token_set_ratio(normalized_text, sentence)
        if score >= 60:
            matches_sentence.append({
                "sentence": row["Sentence"],
                "cantonese": row.get("Cantonese",""),
                "mandarin": row.get("Mandarin",""),
                "matched_phrase": normalized_text,
                "match_type": "fuzzy",
                "score": score
            })
    matches_sentence.sort(key=lambda m: m["score"], reverse=True)

    return {
    "token_matches": [
        {
            "token": m["token"],
            "cantonese": m["cantonese"],
            "mandarin": m["mandarin"],
            "english": m["english"],
            "score": m["score"]
        }
        for m in matches_token[:10]
    ],
    "sentence_matches": [
        {
            "sentence": m["sentence"],
            "cantonese": m["cantonese"],
            "mandarin": m["mandarin"],
            "matched_phrase": m["matched_phrase"],
            "match_type": m["match_type"],
            "score": m["score"]
        }
        for m in matches_sentence[:5]
    ]
}



    

        


    

    




