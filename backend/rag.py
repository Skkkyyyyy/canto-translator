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

    df_token = pd.read_csv('data/tokens100.csv')
    df_sentence = pd.read_csv('data/sentences.csv')

    #direct match + fuzzy match 
    matches_token = []
    for _, row in df_token.iterrows():
        token = str(row["token"]).strip()

        for phrase in phrases:
            if token == phrase:
                matches_token.append({
                    "token": row["token"],
                    "cantonese": row.get("Cantonese", ""),
                    "mandarin": row.get("Mandarin", ""),
                    "english": row.get("English", ""),
                    "function": row.get("Function", ""),
                    "matched_phrase": phrase,
                    "match_type": "direct",
                    "score": 100
                })
            else:
                score = fuzz.ratio(token, phrase)
                if score >= 90:
                    matches_token.append({
                        "token": row["token"],
                        "cantonese": row.get("Cantonese", ""),
                        "mandarin": row.get("Mandarin", ""),
                        "english": row.get("English", ""),
                        "function": row.get("Function", ""),
                        "matched_phrase": phrase,
                        "match_type": "fuzzy",
                        "score": score
                    })
    print(matches_token[:5])

    matches_sentence = []
    for _,row in df_sentence.iterrows():
        sentence = str(row['Sentence'])
        score = fuzz.ratio(sentence, phrase)
        if score >= 50:
            matches_sentence.append({
                "sentence": row["Sentence"],
                "cantonese": row.get("Cantonese",""),
                "mandarin": row.get("Mandarin",""),
                "matched_phrase": phrase,
                "match_type": "fuzzy",
                "score": score
            })
    print(matches_sentence)

    return {
    "token_matches": [
        {
            "token": m["token"],
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



    

        


    

    




