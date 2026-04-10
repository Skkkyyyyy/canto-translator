## normalize the user's message before rag
## convert all capital to lower case 
## remove punctuation, or turn - into space
## reduce replicated letters (goooood)
#used in rag.py
import re 
from itertools import groupby 

def normalizer(text: str):
    #lowercase
    text = text.lower()

    #turn hyphen into space 
    text = text.replace("-"," ")

    #remove punctuations
    text = re.sub(r"[^\w\s]", "", text)

    #reduce repeated letters 
    text = re.sub(r"([a-z])\1{2,}", r"\1\1", text)

    # collapse multiple spaces 
    text = re.sub(r"\s+", " ", text).strip()
    ##text.strip() 去掉字符串开头和结尾的空白

    return text


