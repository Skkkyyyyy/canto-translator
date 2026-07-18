#used in llm_service.py
## normalize user input 
## tokenization V
## sliding window phrase matching V
## direct match 
## fuzzy match
## embedding models + vector DB +  check vector similarity 
from normalizer import normalizer  #from module import function 
import nltk
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

    df_token = pd.read_csv('data/glossary_master.csv')
    df_sentence = pd.read_csv('data/sentences.csv')

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
    print(matches_token[:5])

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
    print(matches_sentence)

    return {
    "token_matches": [
        {
            "token": m["token"],
            "cantonese": m["cantonese"],
            "mandarin": m["mandarin"],
            "english": m["english"],
            "score": m["score"]
        }
        for m in matches_token[:5]
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



    

        


    

    




