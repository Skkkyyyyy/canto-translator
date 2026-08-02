from rag import rag
from openai import OpenAI, APITimeoutError, APIConnectionError
from dotenv import load_dotenv
import os
import httpx
import time

from db import log_translation

load_dotenv()

_cache: dict[str, str] = {}

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
    timeout=httpx.Timeout(30.0, connect=10.0),
)

def _safe_log(**kwargs):
    """DB logging must never break a translation request."""
    try:
        log_translation(**kwargs)
    except Exception as e:
        print(f"[log_translation failed: {e}]")

def llm(text: str, use_rag: bool = True, context=None, verbose: bool = True, model: str = "moonshotai/kimi-k3", max_tokens: int = 1500):
    """context 不为 None 时直接用它当检索结果，绕过 rag()。

    只给 eval_translation.py 做多组对照用（旧检索 / 新检索 / 不检索），
    正常调用不要传，走 use_rag 就行。

    model/max_tokens 用于模型对比测试（比如 scratch_compare_models.py），
    正常调用不要传，走默认值就行。
    """
    overall_start = time.monotonic()

    tag = "custom" if context is not None else str(use_rag)
    cache_key = f"{model}:{tag}:{hash(str(context))}:{text.strip().lower()}"
    if cache_key in _cache:
        cached = _cache[cache_key]
        _safe_log(
            input_text=text,
            use_rag=use_rag,
            result=cached,
            model=model,
            cache_hit=True,
        )
        return cached

    if context is not None:
        retrieved = context
    else:
        retrieved = rag(text) if use_rag else {"token_matches": [], "sentence_matches": []}

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
    "- Be concise\n"
    "- Do not say 'given the breakdown' or 'sticking strictly to'\n"
    "- After the REASONING section, output only the final translations, no meta-commentary\n\n"

    "Output format — two sections, in this exact order:\n\n"
    "REASONING:\n"
    "[Walk through Step 1-3 here: syllable-by-syllable breakdown, including any phonological "
    "associations you considered for ambiguous romanization, and why you picked the glossary "
    "matches you did over alternatives. This section is the only place meta-commentary is allowed.]\n"
    "---\n"
    "粵語：[cantonese characters]\n"
    "普通話：[mandarin]\n"
    "English：[english]\n"
    )
    },
    {
        "role": "user",
        "content": (
            f"Original Cantonese text:\n{text}\n\n"
            f"Retrieved glossary matches:\n{retrieved}\n\n"
            "Remember: REASONING section first, then '---', then only the three final translation lines.\n"
    )
    }
    ]

    HARD_DEADLINE_SECONDS = 45

    results = ""
    for attempt in range(2):
        try:
            start = time.monotonic()
            completion = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=0.2,
                max_tokens=max_tokens,
                top_p=0.9,
                stream=True,
                extra_body={"provider": {"sort": "latency"}},
            )
            for chunk in completion:
                if time.monotonic() - start > HARD_DEADLINE_SECONDS:
                    raise TimeoutError(f"stream exceeded {HARD_DEADLINE_SECONDS}s wall-clock deadline")
                delta = chunk.choices[0].delta
                native_reasoning = getattr(delta, "reasoning", None)
                if native_reasoning and verbose:
                    print(native_reasoning, end="")
                if delta.content:
                    results += delta.content
            break
        except (APITimeoutError, APIConnectionError, httpx.TimeoutException, TimeoutError) as e:
            print(f"\n[timeout on attempt {attempt + 1}, retrying]" if attempt == 0 else f"\n[timeout, giving up: {e}]")
            results = ""
            if attempt == 1:
                _safe_log(
                    input_text=text,
                    use_rag=use_rag,
                    retrieved_context=str(retrieved),
                    model=model,
                    latency_ms=int((time.monotonic() - overall_start) * 1000),
                    error=str(e),
                )
                raise

    if "---" in results:
        reasoning, _, final = results.rpartition("---")
        reasoning = reasoning.removeprefix("REASONING:").strip()
        final = final.strip()
    else:
        # some models (e.g. kimi-k3) occasionally skip the "---" separator —
        # fall back to splitting at the last "粵語：" line so raw reasoning
        # never leaks into the cached/returned value.
        cutoff = results.rfind("粵語")
        if cutoff != -1:
            reasoning = results[:cutoff].removeprefix("REASONING:").strip()
            final = results[cutoff:].strip()
        else:
            reasoning = ""
            final = results.strip()

    if verbose and reasoning:
        print("REASONING:\n" + reasoning + "\n")

    _cache[cache_key] = final

    _safe_log(
        input_text=text,
        use_rag=use_rag,
        retrieved_context=str(retrieved),
        reasoning=reasoning,
        result=final,
        model=model,
        latency_ms=int((time.monotonic() - overall_start) * 1000),
    )

    return final


