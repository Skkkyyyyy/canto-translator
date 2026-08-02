<template>
    <div class="page">
        <header class="header">
            <div class="brand">
                <span class="logo">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
                        <path d="M4 10v4M8 7v10M12 4v16M16 7v10M20 10v4" stroke="white" stroke-width="2.2" stroke-linecap="round"/>
                    </svg>
                </span>
                <span class="brand-name">{{ t('brand.name') }}</span>
            </div>
            <div class="lang-dropdown">
                <select
                    class="lang-select"
                    :value="locale"
                    @change="setLocale(($event.target as HTMLSelectElement).value as LocaleCode)"
                >
                    <option v-for="loc in SUPPORTED_LOCALES" :key="loc.code" :value="loc.code">
                        {{ loc.label }}
                    </option>
                </select>
                <svg class="lang-caret" width="12" height="12" viewBox="0 0 24 24" fill="none">
                    <path d="M6 9l6 6 6-6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
            </div>
        </header>

        <main class="content">
            <h1>{{ t('chatbox.title') }}</h1>
            <p class="subtitle">{{ t('chatbox.subtitle') }}</p>

            <div class="input-card">
                <textarea
                    v-model="message"
                    :placeholder="t('chatbox.placeholder')"
                    rows="2"
                    maxlength="500"
                ></textarea>

                <div class="input-footer">
                    <span class="char-count">{{ t('chatbox.charCount', { count: message.length }) }}</span>
                    <button class="translate-btn" :disabled="!message.trim() || loading" @click="sendMessage">
                        {{ loading ? t('chatbox.translating') : t('chatbox.translate') }}
                    </button>
                </div>
            </div>

            <section class="results-section">
                <h2>{{ t('chatbox.resultsHeading') }}</h2>
                <div class="results-card">
                    <div class="result-col" v-for="col in columns" :key="col.label">
                        <span class="col-label">{{ col.label }}</span>
                        <p class="col-text">{{ col.text || '—' }}</p>
                        <button class="copy-btn" :disabled="!col.text" @click="copyText(col)">
                            <svg width="15" height="15" viewBox="0 0 24 24" fill="none">
                                <rect x="9" y="9" width="12" height="12" rx="2" stroke="currentColor" stroke-width="1.8"/>
                                <path d="M5 15V5a2 2 0 0 1 2-2h10" stroke="currentColor" stroke-width="1.8"/>
                            </svg>
                            {{ col.copied ? t('chatbox.copied') : t('chatbox.copy') }}
                        </button>
                    </div>
                </div>

                <div class="contribute-row">
                    <span class="contribute-text">
                        <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
                            <path d="M12 20.25c-.184 0-.365-.045-.527-.13C7.94 18.24 3 14.76 3 9.75 3 7.13 5.13 5 7.75 5c1.44 0 2.8.66 3.75 1.77A4.98 4.98 0 0 1 16.25 5C18.87 5 21 7.13 21 9.75c0 5.01-4.94 8.49-8.473 10.37-.162.085-.343.13-.527.13Z" stroke="currentColor" stroke-width="1.6" stroke-linejoin="round"/>
                        </svg>
                        {{ hasResults ? t('chatbox.contributePromptHasResults') : t('chatbox.contributePromptNoResults') }}
                    </span>
                    <div class="contribute-actions">
                        <button class="contribute-btn" @click="openContribute('sentence')">
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
                                <path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4 12.5-12.5Z" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/>
                            </svg>
                            {{ t('chatbox.fixTranslation') }}
                        </button>
                        <button class="contribute-btn" @click="openContribute('token')">
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
                                <path d="M2 6s2-1.5 5-1.5 5 1.5 5 1.5v13s-2-1.5-5-1.5-5 1.5-5 1.5V6Z" stroke="currentColor" stroke-width="1.6" stroke-linejoin="round"/>
                                <path d="M22 6s-2-1.5-5-1.5-5 1.5-5 1.5v13s2-1.5 5-1.5 5 1.5 5 1.5V6Z" stroke="currentColor" stroke-width="1.6" stroke-linejoin="round"/>
                            </svg>
                            {{ t('chatbox.addWord') }}
                        </button>
                    </div>
                </div>
            </section>

            <div class="examples">
                <span class="examples-label">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                        <path d="M12 2l1.7 5.1L19 9l-5.3 1.9L12 16l-1.7-5.1L5 9l5.3-1.9L12 2Z"/>
                        <path d="M19 15l.8 2.3L22 18l-2.2.7L19 21l-.8-2.3L16 18l2.2-.7L19 15Z"/>
                    </svg>
                    {{ t('chatbox.examplesLabel') }}
                </span>
                <button
                    v-for="ex in examples"
                    :key="ex"
                    class="example-chip"
                    @click="message = ex"
                >{{ ex }}</button>
            </div>
        </main>

        <ContributeModal
            :open="contributeOpen"
            :initial-kind="contributeKind"
            :source-text="message"
            :source-output="{ cantonese: columns[0].text, mandarin: columns[1].text, english: columns[2].text }"
            @close="contributeOpen = false"
        />
    </div>
</template>

<script setup lang="ts">
import { computed, ref, reactive, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import ContributeModal from './ContributeModal.vue'
import type { ContributionKind } from '../api/types'
import { SUPPORTED_LOCALES, setLocale } from '../i18n'
import type { LocaleCode } from '../i18n'

const { t, locale } = useI18n()

const message = ref('')
const loading = ref(false)

const contributeOpen = ref(false)
const contributeKind = ref<ContributionKind>('token')

const openContribute = (kind: ContributionKind) => {
    contributeKind.value = kind
    contributeOpen.value = true
}

const examples = ['hoi sem fai lok!', 'mm ho gum la', 'mm goi sai']

const columns = reactive([
    { label: '廣東話', text: '', copied: false },
    { label: '普通话', text: '', copied: false },
    { label: 'English', text: '', copied: false },
])

const hasResults = computed(() => columns.some(col => col.text !== ''))

const setResults = (cantonese: string, mandarin: string, english: string) => {
    columns[0].text = cantonese
    columns[1].text = mandarin
    columns[2].text = english
}

watch(message, (value) => {
    if (!value.trim()) {
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
        setResults(t('chatbox.connectionError'), '', '')
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
    --header-bg: #fff;
    --page-bg: #f6faf7;
    --border: #e5e5e7;
    --text-primary: #111114;
    --text-secondary: #6b6b70;
    --accent: #1f6b45;
    --accent-hover: #185536;
    --pill-bg: #f1f1f3;

    --fs-h1: 1.5rem;
    --fs-lg: 1.125rem;
    --fs-md: 1rem;
    --fs-sm: 0.9375rem;
    --fs-xs: 0.875rem;
    --fs-2xs: 0.9375rem;

    min-height: 100svh;
    display: flex;
    flex-direction: column;
    background: var(--page-bg);
    color: var(--text-primary);
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
}

@media (prefers-color-scheme: dark) {
    .page {
        --card-bg: #1c1d22;
        --header-bg: #1c1d22;
        --page-bg: #10241a;
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
    justify-content: space-between;
    padding: 0.65rem 2rem;
    border-bottom: 1px solid var(--border);
    background: var(--header-bg);
}

.lang-dropdown {
    position: relative;
    display: inline-flex;
    align-items: center;
}

.lang-select {
    appearance: none;
    -webkit-appearance: none;
    padding: 0.4rem 2rem 0.4rem 1rem;
    border: 1px solid var(--border);
    border-radius: 999px;
    background: transparent;
    color: var(--text-primary);
    font-size: var(--fs-2xs);
    font-family: inherit;
    cursor: pointer;
}

.lang-select:hover {
    background: var(--pill-bg);
}

.lang-caret {
    position: absolute;
    right: 0.7rem;
    pointer-events: none;
    color: var(--text-secondary);
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
    font-size: var(--fs-lg);
    font-weight: 700;
}

.content {
    width: 100%;
    max-width: 46rem;
    margin: 0 auto;
    padding: 2.5rem 1.5rem;
    flex: 1;
    display: flex;
    flex-direction: column;
    justify-content: center;
    box-sizing: border-box;
}

h1 {
    font-size: var(--fs-h1);
    font-weight: 700;
    margin: 0;
}

.subtitle {
    color: var(--text-secondary);
    font-size: var(--fs-sm);
    margin: 0.3rem 0 1rem;
}

.input-card {
    background: var(--card-bg);
    border: 1px solid var(--border);
    border-radius: 20px;
    padding: 1.75rem;
}

textarea {
    width: 100%;
    border: none;
    background: transparent;
    resize: vertical;
    padding: 0;
    font-size: var(--fs-md);
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
    margin-top: 1.25rem;
    padding-top: 1rem;
    border-top: 1px solid var(--border);
}

.char-count {
    color: var(--text-secondary);
    font-size: var(--fs-2xs);
}

.translate-btn {
    padding: 0.5rem 1.4rem;
    border: none;
    border-radius: 999px;
    background: var(--accent);
    color: white;
    font-size: var(--fs-xs);
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
    font-size: var(--fs-md);
    font-weight: 700;
    margin: 0 0 0.85rem;
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
    padding: 1.5rem 1.25rem;
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
    font-size: var(--fs-2xs);
    margin-bottom: 0.6rem;
}

.col-text {
    font-weight: 600;
    font-size: var(--fs-md);
    margin: 0 0 1.1rem;
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
    font-size: var(--fs-xs);
    cursor: pointer;
}

.copy-btn:hover:not(:disabled) {
    background: var(--pill-bg);
}

.copy-btn:disabled {
    opacity: 0.4;
    cursor: not-allowed;
}

.contribute-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    flex-wrap: wrap;
    gap: 0.6rem;
    margin-top: 1.25rem;
    background: var(--card-bg);
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 1.1rem 1.25rem;
}

.contribute-text {
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    color: var(--text-primary);
    font-size: var(--fs-sm);
}

.contribute-text svg {
    color: var(--accent);
    flex-shrink: 0;
}

.contribute-actions {
    display: flex;
    gap: 0.6rem;
    flex-wrap: wrap;
}

.contribute-btn {
    display: inline-flex;
    align-items: center;
    gap: 0.4rem;
    padding: 0.4rem 0.95rem;
    border: 1px solid var(--border);
    border-radius: 999px;
    background: var(--card-bg);
    color: var(--text-primary);
    font-size: var(--fs-xs);
    font-family: inherit;
    cursor: pointer;
}

.contribute-btn svg {
    color: var(--accent);
    flex-shrink: 0;
}

.contribute-btn:hover {
    background: var(--pill-bg);
}

.examples {
    display: flex;
    align-items: center;
    flex-wrap: wrap;
    gap: 0.6rem;
    margin-top: 1.25rem;
    background: var(--card-bg);
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 1.1rem 1.25rem;
}

.examples-label {
    display: inline-flex;
    align-items: center;
    gap: 0.4rem;
    color: var(--text-primary);
    font-size: var(--fs-sm);
    margin-right: 0.25rem;
}

.example-chip {
    padding: 0.4rem 1rem;
    border: 1px solid var(--border);
    border-radius: 999px;
    background: var(--card-bg);
    color: var(--accent);
    font-size: var(--fs-xs);
    font-weight: 600;
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
