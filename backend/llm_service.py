from rag import rag
from openai import OpenAI
from dotenv import load_dotenv 
import os 
from groq import Groq

load_dotenv()
api_key = os.getenv("GROQ_API_KEY")

def llm(text:str):
    messages = [
    {
        "role": "system",
        "content": (

    "You are a Cantonese translation assistant specializing in informal written Cantonese (often romanized or mixed with Chinese characters). "
    
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

    client = Groq()
    completion = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=messages,
        temperature=1,
        max_completion_tokens=1024,
        top_p=1,
        stream=True,
        stop=None
    )

    results = ""
    for chunk in completion:
        if chunk.choices[0].delta.content:
            print(chunk.choices[0].delta.content, end="")
            results += chunk.choices[0].delta.content
    return results 


