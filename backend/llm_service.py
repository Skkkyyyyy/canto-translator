from rag import rag
from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv()

_cache: dict[str, str] = {}

def llm(text:str):
    cache_key = text.strip().lower()
    if cache_key in _cache:
        return _cache[cache_key]
    messages = [
    {
        "role": "system",
        "content": (

    "You are a Cantonese translation assistant specializing in informal written Cantonese (often romanized or mixed with Chinese characters). "

    "How to weigh the retrieved glossary matches:\n"
    "- token_matches and sentence_matches are candidate interpretations retrieved by string matching, not guaranteed correct — use judgment, don't just concatenate them\n"
    "- match_type \"direct\" (score 100) means the input exactly matches a known spelling; \"fuzzy\" means an approximate match — treat fuzzy matches, especially at lower scores, as less certain\n"
    "- If a sentence_match has a high score, it means this input closely matches a previously verified full sentence — prefer its given Cantonese/Mandarin translation as a whole over reconstructing the sentence from individual token_matches\n"
    "- token_matches can overlap: a multi-word phrase match (e.g. \"duk mm duk\" -> 得唔得) and a shorter single-word match contained within it (e.g. \"duk\" -> 戳/poke) may both be retrieved for the same input. When this happens, the longer phrase-level match reflects the actual compound meaning and should win — do not fall back to the shorter word's literal meaning\n"
    "- Multiple matches that map to the same Cantonese/Mandarin meaning (different spellings of the same word) reinforce each other and increase confidence in that reading, they are not conflicting alternatives\n\n"

    "Your translation process must follow these steps strictly:\n\n"
    "Step 1 - Cantonese breakdown:\n"
    "Break the input into individual words or phrases. For each unit, provide:\n"
    "- The original word/phrase (romanized or mixed)\n"
    "- Its Cantonese Chinese character form (粵語漢字)\n"
    "Example: 'ho mm ho aa' → 'ho'(好) + 'mm'(唔) + 'ho'(好) + 'aa'(呀) = '好唔好呀？'\n\n"
    "Step 2 - Mandarin translation (普通话):\n"
    "Use the Cantonese breakdown AND the retrieved glossary matches to produce a natural Mandarin translation. "
    "Prioritize glossary matches when available. Make it sound natural, not literal.\n\n"
    "Step 3 - English translation:\n"
    "Translate based on the Mandarin version. Keep it natural and conversational.\n\n"
    
    "Input format notes:\n"
    "- The input may contain a mix of romanized Cantonese, Chinese characters (Traditional or Simplified), and English words or abbreviations\n"
    "- English abbreviations (e.g. 'tbh', 'omg', 'lol') should be recognized as English and kept as-is or expanded\n"
    "- Chinese characters should be read in Cantonese context, not Mandarin\n"
    "- Treat the entire input as one Cantonese sentence regardless of script mixing\n\n"

    "Rules:\n"
    "- Preserve the tone and register of informal Cantonese\n"
    "- If a word is uncertain, flag it clearly\n"
    "- Translate only what is written, do not infer or extend meaning beyond the original input\n"
    "- Do not add context, assumptions, or extra interpretation\n"
    "- If something is ambiguous, provide the most literal translation only\n"
    "- Be concise, do not explain your reasoning process\n"
    "- Do not say 'given the breakdown' or 'sticking strictly to'\n"
    "- Output only the final translations, no meta-commentary\n"
    )
    },
    {
        "role": "user",
        "content": (
            f"Original Cantonese text:\n{text}\n\n"
            f"Retrieved glossary matches:\n{rag(text)}\n\n"
            "Output format:\n"
            "粵語：[cantonese characters]\n"
            "普通話：[mandarin]\n"
            "English：[english]\n"
    )
    }
    ]

    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=os.getenv("OPENROUTER_API_KEY"),
    )
    completion = client.chat.completions.create(
        model="qwen/qwen3.6-flash",
        messages=messages,
        temperature=0.2,
        max_tokens=400,
        top_p=0.9,
        stream=True,
    )

    results = ""
    for chunk in completion:
        if chunk.choices[0].delta.content:
            print(chunk.choices[0].delta.content, end="")
            results += chunk.choices[0].delta.content

    _cache[cache_key] = results
    return results


