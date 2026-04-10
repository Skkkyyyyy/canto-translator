# CantoLens 🔍

A Cantonese translation tool that converts **romanized Cantonese (Jyutping/informal romanization)** into Traditional Chinese (Cantonese), Mandarin Chinese, and English — powered by a local glossary and LLM.

## Example

| Input | Cantonese | Mandarin | English |
|---|---|---|---|
| mm ho gum la | 唔好咁啦 | 不要這樣啦 | Don't do this |
| can I late drop | 可以唔可以late drop？ | 可以退掉嗎？ | Can I drop it? |

---

## How It Works

CantoLens uses a **two-stage translation pipeline**:

1. **Glossary Lookup** — Before calling the LLM, the input is matched against a local glossary of Cantonese tokens and sentences using:
   - **Direct match** — exact lookup for known tokens/phrases
   - **Fuzzy match** — approximate matching for close variants

2. **LLM Translation** — Matched glossary context is injected into the prompt, then passed to `llama-3.3-70b-versatile` (via Groq) to produce the final translation across all three output languages.

This hybrid approach improves accuracy for Cantonese-specific slang and colloquial expressions that LLMs may not handle well on their own.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Vue.js |
| Backend | FastAPI (Python) |
| LLM | `llama-3.3-70b-versatile` |
| Fuzzy Matching | `thefuzz` |

---

## Getting Started

### Prerequisites

- Python 3.9+
- Node.js 18+
- A Groq API key

### Backend Setup
```bash
cd backend
pip install -r requirements.txt
cp .env.example .env   # add your API key here
uvicorn main:app --reload
```

### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

### Environment Variables

Create a `.env` file in the backend directory:
