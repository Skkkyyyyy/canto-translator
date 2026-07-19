<template>
    <div class="page">
        <header class="header">
            <div class="brand">
                <span class="logo">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
                        <path d="M4 10v4M8 7v10M12 4v16M16 7v10M20 10v4" stroke="white" stroke-width="2.2" stroke-linecap="round"/>
                    </svg>
                </span>
                <span class="brand-name">CantoLens</span>
            </div>
        </header>

        <main class="content">
            <h1>Cantonese Translator</h1>
            <p class="subtitle">Cantonese, Mandarin and English—side by side.</p>

            <div class="input-card">
                <span class="lang-pill">Cantonese (romanized)</span>

                <textarea
                    v-model="message"
                    placeholder="Type Cantonese in English letters, e.g. mm ho gum la..."
                    rows="3"
                    maxlength="500"
                ></textarea>

                <div class="input-footer">
                    <span class="char-count">{{ message.length }} / 500</span>
                    <button class="translate-btn" :disabled="!message.trim() || loading" @click="sendMessage">
                        {{ loading ? 'Translating...' : 'Translate' }}
                    </button>
                </div>
            </div>

            <section class="results-section">
                <h2>Translation results</h2>
                <div class="results-card">
                    <div class="result-col" v-for="col in columns" :key="col.label">
                        <span class="col-label">{{ col.label }}</span>
                        <p class="col-text">{{ col.text || '—' }}</p>
                        <button class="copy-btn" :disabled="!col.text" @click="copyText(col)">
                            <svg width="15" height="15" viewBox="0 0 24 24" fill="none">
                                <rect x="9" y="9" width="12" height="12" rx="2" stroke="currentColor" stroke-width="1.8"/>
                                <path d="M5 15V5a2 2 0 0 1 2-2h10" stroke="currentColor" stroke-width="1.8"/>
                            </svg>
                            {{ col.copied ? 'Copied' : 'Copy' }}
                        </button>
                    </div>
                </div>
            </section>

            <div class="examples">
                <span class="examples-label">Try an example:</span>
                <button
                    v-for="ex in examples"
                    :key="ex"
                    class="example-chip"
                    @click="message = ex"
                >{{ ex }}</button>
            </div>
        </main>
    </div>
</template>

<script setup lang="ts">
import { ref, reactive, watch } from 'vue'

const message = ref('')
const loading = ref(false)

const examples = ['mm ho gum la', 'we yurk ma', 'now lok che']

const columns = reactive([
    { label: '廣東話', text: '', copied: false },
    { label: '普通话', text: '', copied: false },
    { label: 'English', text: '', copied: false },
])

const setResults = (cantonese: string, mandarin: string, english: string) => {
    columns[0].text = cantonese
    columns[1].text = mandarin
    columns[2].text = english
}

watch(message, (newVal) => {
    if (!newVal.trim()) {
        setResults('', '', '')
    }
})

const sendMessage = async () => {
    if (!message.value.trim() || loading.value) return
    loading.value = true
    try {
        const response = await fetch('http://127.0.0.1:8000/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                text: message.value
            })
        })
        const data = await response.json()
        const responseText = data.response

        const cantoPart = responseText.split('普通話：')[0]
        const mandarinAndEnglishPart = responseText.split('普通話：')[1]

        const mandarinPart = mandarinAndEnglishPart.split('English：')[0]
        const englishPart = mandarinAndEnglishPart.split('English：')[1]

        setResults(
            cantoPart.replace('粵語：', '').trim(),
            mandarinPart.trim(),
            englishPart.trim()
        )
    } catch (error) {
        console.error(error)
        setResults('Failed to connect to backend', '', '')
    } finally {
        loading.value = false
    }
}

const copyText = async (col: { text: string; copied: boolean }) => {
    if (!col.text) return
    try {
        await navigator.clipboard.writeText(col.text)
    } catch {
        const textarea = document.createElement('textarea')
        textarea.value = col.text
        textarea.style.position = 'fixed'
        textarea.style.opacity = '0'
        document.body.appendChild(textarea)
        textarea.select()
        document.execCommand('copy')
        document.body.removeChild(textarea)
    }
    col.copied = true
    setTimeout(() => (col.copied = false), 1500)
}
</script>

<style scoped>
.page {
    --card-bg: #fff;
    --page-bg: #f7f7f8;
    --border: #e5e5e7;
    --text-primary: #111114;
    --text-secondary: #6b6b70;
    --accent: #1f6b45;
    --accent-hover: #185536;
    --pill-bg: #f1f1f3;

    min-height: 100svh;
    background: var(--page-bg);
    color: var(--text-primary);
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
}

@media (prefers-color-scheme: dark) {
    .page {
        --card-bg: #1c1d22;
        --page-bg: #131417;
        --border: #2e303a;
        --text-primary: #f3f4f6;
        --text-secondary: #9ca3af;
        --accent: #2f8a5b;
        --accent-hover: #3aa06b;
        --pill-bg: #26272e;
    }
}

.header {
    display: flex;
    align-items: center;
    padding: 1rem 2rem;
    border-bottom: 1px solid var(--border);
    background: var(--card-bg);
}

.brand {
    display: flex;
    align-items: center;
    gap: 0.6rem;
}

.logo {
    width: 30px;
    height: 30px;
    border-radius: 50%;
    background: var(--accent);
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
}

.brand-name {
    font-size: 1.15rem;
    font-weight: 700;
}

.content {
    max-width: 46rem;
    margin: 0 auto;
    padding: 2.5rem 1.5rem 4rem;
}

h1 {
    font-size: 2rem;
    font-weight: 700;
    margin: 0;
}

.subtitle {
    color: var(--text-secondary);
    margin: 0.5rem 0 2rem;
}

.input-card {
    background: var(--card-bg);
    border: 1px solid var(--border);
    border-radius: 20px;
    padding: 1.5rem;
}

.lang-pill {
    display: inline-block;
    background: var(--pill-bg);
    color: var(--text-primary);
    font-weight: 600;
    font-size: 0.9rem;
    padding: 0.45rem 1rem;
    border-radius: 999px;
    margin-bottom: 1rem;
}

textarea {
    width: 100%;
    border: none;
    background: transparent;
    resize: vertical;
    padding: 0;
    font-size: 1.15rem;
    font-family: inherit;
    color: var(--text-primary);
    box-sizing: border-box;
    outline: none;
}

textarea::placeholder {
    color: var(--text-secondary);
}

.input-footer {
    display: flex;
    justify-content: flex-end;
    align-items: center;
    gap: 1rem;
    margin-top: 1rem;
    padding-top: 1rem;
    border-top: 1px solid var(--border);
}

.char-count {
    color: var(--text-secondary);
    font-size: 0.9rem;
}

.translate-btn {
    padding: 0.6rem 1.6rem;
    border: none;
    border-radius: 999px;
    background: var(--accent);
    color: white;
    font-size: 1rem;
    font-weight: 600;
    cursor: pointer;
}

.translate-btn:hover:not(:disabled) {
    background: var(--accent-hover);
}

.translate-btn:disabled {
    opacity: 0.5;
    cursor: not-allowed;
}

.results-section {
    margin-top: 2rem;
}

.results-section h2 {
    font-size: 1.1rem;
    font-weight: 700;
    margin: 0 0 0.75rem;
}

.results-card {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    background: var(--card-bg);
    border: 1px solid var(--border);
    border-radius: 20px;
    overflow: hidden;
}

.result-col {
    padding: 1.25rem;
    border-left: 1px solid var(--border);
    display: flex;
    flex-direction: column;
    align-items: flex-start;
}

.result-col:first-child {
    border-left: none;
}

.col-label {
    color: var(--text-secondary);
    font-size: 0.85rem;
    margin-bottom: 0.5rem;
}

.col-text {
    font-weight: 600;
    font-size: 1.05rem;
    margin: 0 0 1rem;
    word-break: break-word;
}

.copy-btn {
    margin-top: auto;
    display: inline-flex;
    align-items: center;
    gap: 0.35rem;
    padding: 0.4rem 0.75rem;
    border: 1px solid var(--border);
    border-radius: 10px;
    background: transparent;
    color: var(--text-primary);
    font-size: 0.85rem;
    cursor: pointer;
}

.copy-btn:hover:not(:disabled) {
    background: var(--pill-bg);
}

.copy-btn:disabled {
    opacity: 0.4;
    cursor: not-allowed;
}

.examples {
    display: flex;
    align-items: center;
    flex-wrap: wrap;
    gap: 0.6rem;
    margin-top: 2rem;
}

.examples-label {
    color: var(--text-secondary);
    font-size: 0.9rem;
    margin-right: 0.25rem;
}

.example-chip {
    padding: 0.45rem 1rem;
    border: 1px solid var(--border);
    border-radius: 999px;
    background: var(--card-bg);
    color: var(--text-primary);
    font-size: 0.9rem;
    cursor: pointer;
}

.example-chip:hover {
    background: var(--pill-bg);
}

@media (max-width: 640px) {
    .results-card {
        grid-template-columns: 1fr;
    }
    .result-col {
        border-left: none;
        border-top: 1px solid var(--border);
    }
    .result-col:first-child {
        border-top: none;
    }
}
</style>
