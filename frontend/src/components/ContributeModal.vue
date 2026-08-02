<template>
    <div v-if="open" class="overlay" @mousedown.self="requestClose">
        <div
            class="modal"
            role="dialog"
            tabindex="-1"
            aria-modal="true"
            aria-labelledby="contribute-title"
            @keydown.esc="requestClose"
        >
            <header class="modal-header">
                <div>
                    <h2 id="contribute-title">{{ t('contribute.title') }}</h2>
                    <p class="modal-sub">
                        {{ t('contribute.subtitle') }}
                    </p>
                </div>
                <button class="icon-btn" :aria-label="t('contribute.close')" @click="requestClose">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
                        <path d="M6 6l12 12M18 6L6 18" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                    </svg>
                </button>
            </header>

            <p v-if="USE_MOCK" class="mock-banner">
                {{ t('contribute.mockBanner') }}
            </p>

            <form v-if="status !== 'success'" class="modal-body" @submit.prevent="submit">
                <div class="kind-tabs" role="tablist">
                    <button
                        v-for="tab in kindTabs"
                        :key="tab.value"
                        type="button"
                        role="tab"
                        class="kind-tab"
                        :class="{ active: form.kind === tab.value }"
                        :aria-selected="form.kind === tab.value"
                        @click="form.kind = tab.value"
                    >{{ tab.label }}</button>
                </div>

                <label class="field">
                    <span class="field-label">
                        {{ form.kind === 'token' ? t('contribute.fields.tokenLabelToken') : t('contribute.fields.tokenLabelSentence') }}
                        <span class="required">*</span>
                    </span>
                    <input
                        ref="firstInput"
                        v-model="form.token"
                        type="text"
                        :placeholder="form.kind === 'token' ? t('contribute.fields.tokenPlaceholderToken') : t('contribute.fields.tokenPlaceholderSentence')"
                        :aria-invalid="!!errors.token"
                    />
                    <span v-if="errors.token" class="error-text">{{ errors.token }}</span>
                </label>

                <div v-if="form.kind === 'token' && duplicates.length" class="duplicate-note">
                    <p class="duplicate-title">{{ t('contribute.duplicates.title') }}</p>
                    <p v-for="hit in duplicates" :key="hit.token" class="duplicate-row">
                        <code>{{ hit.token }}</code> → {{ hit.cantonese }} · {{ hit.english }}
                    </p>
                    <p class="duplicate-hint">
                        {{
                            form.intent === 'correction'
                                ? t('contribute.duplicates.hintCorrection')
                                : t('contribute.duplicates.hintNew')
                        }}
                    </p>
                    <button
                        v-if="form.intent === 'new'"
                        type="button"
                        class="ghost-btn"
                        @click="switchToCorrection"
                    >{{ t('contribute.duplicates.correctThisEntry') }}</button>
                </div>

                <p v-if="form.kind === 'sentence'" class="hint">
                    {{ t('contribute.sentenceHint') }}
                </p>

                <div class="triple">
                    <label class="field">
                        <span class="field-label">{{ t('contribute.fields.cantonese') }}</span>
                        <input v-model="form.cantonese" type="text" :placeholder="placeholders.cantonese" />
                    </label>
                    <label class="field">
                        <span class="field-label">{{ t('contribute.fields.mandarin') }}</span>
                        <input v-model="form.mandarin" type="text" :placeholder="placeholders.mandarin" />
                    </label>
                    <label class="field">
                        <span class="field-label">{{ t('contribute.fields.english') }}</span>
                        <input v-model="form.english" type="text" :placeholder="placeholders.english" />
                    </label>
                </div>
                <span v-if="errors.meaning" class="error-text">{{ errors.meaning }}</span>

                <label v-if="form.kind === 'token'" class="field">
                    <span class="field-label">{{ t('contribute.fields.partOfSpeech') }}</span>
                    <select v-model="form.function">
                        <option value="">{{ t('contribute.fields.pickOne') }}</option>
                        <option v-for="option in functionOptions" :key="option" :value="option">
                            {{ option }}
                        </option>
                    </select>
                </label>

                <label v-if="form.kind === 'token'" class="field">
                    <span class="field-label">{{ t('contribute.fields.exampleSentence') }} <span class="optional">{{ t('contribute.fields.optional') }}</span></span>
                    <input v-model="form.example" type="text" :placeholder="t('contribute.fields.examplePlaceholder')" />
                </label>

                <label class="field">
                    <span class="field-label">
                        {{ form.kind === 'token' ? t('contribute.fields.notesToken') : t('contribute.fields.notesSentence') }}
                        <span class="optional">{{ t('contribute.fields.optional') }}</span>
                    </span>
                    <textarea
                        v-model="form.note"
                        rows="2"
                        :placeholder="form.kind === 'token'
                            ? t('contribute.fields.notesPlaceholderToken')
                            : t('contribute.fields.notesPlaceholderSentence')"
                    ></textarea>
                </label>

                <label class="field">
                    <span class="field-label">{{ t('contribute.fields.contributor') }} <span class="optional">{{ t('contribute.fields.optional') }}</span></span>
                    <input v-model="form.contributor" type="text" :placeholder="t('contribute.fields.contributorPlaceholder')" />
                </label>

                <p v-if="status === 'error'" class="submit-error">
                    {{ t('contribute.errors.submitFailed', { error: submitError }) }}
                </p>

                <footer class="modal-footer">
                    <button type="button" class="ghost-btn" @click="requestClose">{{ t('contribute.actions.cancel') }}</button>
                    <button type="submit" class="primary-btn" :disabled="status === 'submitting'">
                        {{ status === 'submitting' ? t('contribute.actions.submitting') : t('contribute.actions.submit') }}
                    </button>
                </footer>
            </form>

            <div v-else class="success">
                <div class="success-mark" aria-hidden="true">
                    <svg width="26" height="26" viewBox="0 0 24 24" fill="none">
                        <path d="M4 12.5l5.5 5.5L20 7" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"/>
                    </svg>
                </div>
                <h3>{{ t('contribute.success.title') }}</h3>
                <p class="success-text">
                    {{ t('contribute.success.text') }}
                </p>
                <p class="receipt">{{ t('contribute.success.referenceLabel') }} <code>{{ receipt?.id }}</code></p>
                <div class="modal-footer">
                    <button type="button" class="ghost-btn" @click="startAnother">{{ t('contribute.success.another') }}</button>
                    <button type="button" class="primary-btn" @click="close">{{ t('contribute.success.done') }}</button>
                </div>
            </div>
        </div>
    </div>
</template>

<script setup lang="ts">
import { computed, nextTick, reactive, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { searchGlossary, submitContribution } from '../api/contributions'
import { USE_MOCK } from '../api/client'
import type {
    ContributionDraft,
    ContributionKind,
    ContributionReceipt,
    GlossaryHit,
} from '../api/types'

const { t } = useI18n()

const props = defineProps<{
    open: boolean
    /** What the user last translated, used to prefill a sentence correction. */
    sourceText?: string
    sourceOutput?: { cantonese: string; mandarin: string; english: string }
    initialKind?: ContributionKind
}>()

const emit = defineEmits<{ close: [] }>()

// Matches the Function column in backend/data/tokens100.csv.
const functionOptions = [
    'expression', 'phrase', 'question phrase', 'particle', 'negation',
    'verb', 'noun', 'adjective', 'adverb', 'pronoun', 'modal', 'slang', 'profanity',
]

const kindTabs = computed<{ value: ContributionKind; label: string }[]>(() => [
    { value: 'token', label: t('contribute.tabs.token') },
    { value: 'sentence', label: t('contribute.tabs.sentence') },
])

const emptyForm = (): ContributionDraft => ({
    kind: 'token',
    intent: 'new',
    token: '',
    cantonese: '',
    mandarin: '',
    english: '',
    function: '',
    example: '',
    note: '',
    contributor: '',
})

const form = reactive<ContributionDraft>(emptyForm())
const errors = reactive<{ token?: string; meaning?: string }>({})
const status = ref<'form' | 'submitting' | 'success' | 'error'>('form')
const submitError = ref('')
const receipt = ref<ContributionReceipt | null>(null)
const firstInput = ref<HTMLInputElement | null>(null)

const duplicates = ref<GlossaryHit[]>([])

const placeholders = computed(() =>
    form.kind === 'token'
        ? { cantonese: '加油', mandarin: '加油', english: 'keep it up' }
        : { cantonese: '正確嘅粵語', mandarin: '正确的普通话', english: 'what it should say' },
)

const isDirty = computed(() =>
    [form.token, form.cantonese, form.mandarin, form.english, form.note, form.example]
        .some((value) => value.trim() !== ''),
)

function resetForm(kind: ContributionKind) {
    Object.assign(form, emptyForm(), { kind })
    if (kind === 'sentence') {
        form.intent = 'correction'
        form.token = props.sourceText ?? ''
        form.cantonese = props.sourceOutput?.cantonese ?? ''
        form.mandarin = props.sourceOutput?.mandarin ?? ''
        form.english = props.sourceOutput?.english ?? ''
    }
    form.sourceText = props.sourceText
    form.sourceOutput = props.sourceOutput
    duplicates.value = []
    delete errors.token
    delete errors.meaning
    status.value = 'form'
    submitError.value = ''
}

watch(
    () => props.open,
    async (open) => {
        if (!open) return
        resetForm(props.initialKind ?? 'token')
        await nextTick()
        firstInput.value?.focus()
    },
    { immediate: true },
)

// Switching tabs re-prefills, since the two modes mean different things.
watch(() => form.kind, (kind) => resetForm(kind))

let dupTimer: ReturnType<typeof setTimeout> | undefined
watch(
    () => form.token,
    (token) => {
        clearTimeout(dupTimer)
        if (form.kind !== 'token' || !token.trim()) {
            duplicates.value = []
            return
        }
        dupTimer = setTimeout(async () => {
            try {
                duplicates.value = await searchGlossary(token)
            } catch {
                // A failing duplicate check shouldn't block a submission.
                duplicates.value = []
            }
        }, 400)
    },
)

function switchToCorrection() {
    form.intent = 'correction'
    const hit = duplicates.value[0]
    if (!hit) return
    form.cantonese ||= hit.cantonese
    form.mandarin ||= hit.mandarin
    form.english ||= hit.english
    form.function ||= hit.function
}

function validate() {
    delete errors.token
    delete errors.meaning
    if (!form.token.trim()) {
        errors.token = form.kind === 'token'
            ? t('contribute.errors.tokenRequiredToken')
            : t('contribute.errors.tokenRequiredSentence')
    }
    if (!form.cantonese.trim() && !form.mandarin.trim() && !form.english.trim()) {
        errors.meaning = t('contribute.errors.meaningRequired')
    }
    return !errors.token && !errors.meaning
}

async function submit() {
    if (!validate()) return
    status.value = 'submitting'
    try {
        receipt.value = await submitContribution({ ...form })
        status.value = 'success'
    } catch (error) {
        submitError.value = error instanceof Error ? error.message : t('contribute.errors.unknownError')
        status.value = 'error'
    }
}

function startAnother() {
    resetForm(form.kind)
}

function close() {
    emit('close')
}

function requestClose() {
    if (status.value === 'form' && isDirty.value) {
        if (!window.confirm(t('contribute.discardConfirm'))) return
    }
    close()
}
</script>

<style scoped>
.overlay {
    --card-bg: #fff;
    --border: #e5e5e7;
    --text-primary: #111114;
    --text-secondary: #6b6b70;
    --accent: #1f6b45;
    --accent-hover: #185536;
    --pill-bg: #f1f1f3;
    --danger: #b42318;

    position: fixed;
    inset: 0;
    background: rgba(0, 0, 0, 0.45);
    display: flex;
    align-items: flex-start;
    justify-content: center;
    padding: 3rem 1rem;
    overflow-y: auto;
    z-index: 50;
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    color: var(--text-primary);
}

@media (prefers-color-scheme: dark) {
    .overlay {
        --card-bg: #1c1d22;
        --border: #2e303a;
        --text-primary: #f3f4f6;
        --text-secondary: #9ca3af;
        --accent: #2f8a5b;
        --accent-hover: #3aa06b;
        --pill-bg: #26272e;
        --danger: #f87171;
    }
}

.modal {
    background: var(--card-bg);
    border: 1px solid var(--border);
    border-radius: 20px;
    width: min(34rem, 100%);
    padding: 1.5rem;
    box-shadow: 0 20px 40px rgba(0, 0, 0, 0.2);
}

.modal-header {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    gap: 1rem;
}

h2 {
    font-size: 1.25rem;
    font-weight: 700;
    margin: 0;
}

.modal-sub {
    color: var(--text-secondary);
    font-size: 0.9rem;
    margin: 0.35rem 0 0;
}

.icon-btn {
    background: transparent;
    border: none;
    color: var(--text-secondary);
    cursor: pointer;
    padding: 0.25rem;
    border-radius: 8px;
    flex-shrink: 0;
}

.icon-btn:hover {
    background: var(--pill-bg);
    color: var(--text-primary);
}

.mock-banner {
    margin: 1rem 0 0;
    padding: 0.5rem 0.75rem;
    border-radius: 10px;
    background: var(--pill-bg);
    color: var(--text-secondary);
    font-size: 0.8rem;
}

.modal-body {
    display: flex;
    flex-direction: column;
    gap: 1rem;
    margin-top: 1.25rem;
}

.kind-tabs {
    display: flex;
    gap: 0.5rem;
}

.kind-tab {
    padding: 0.45rem 1rem;
    border: 1px solid var(--border);
    border-radius: 999px;
    background: transparent;
    color: var(--text-secondary);
    font-size: 0.9rem;
    font-family: inherit;
    cursor: pointer;
}

.kind-tab.active {
    background: var(--accent);
    border-color: var(--accent);
    color: #fff;
    font-weight: 600;
}

.field {
    display: flex;
    flex-direction: column;
    gap: 0.35rem;
}

.field-label {
    font-size: 0.85rem;
    color: var(--text-secondary);
}

.required {
    color: var(--danger);
}

.optional {
    font-size: 0.75rem;
    opacity: 0.7;
}

input,
select,
textarea {
    width: 100%;
    box-sizing: border-box;
    padding: 0.6rem 0.75rem;
    border: 1px solid var(--border);
    border-radius: 10px;
    background: transparent;
    color: var(--text-primary);
    font-size: 0.95rem;
    font-family: inherit;
    resize: vertical;
}

input:focus,
select:focus,
textarea:focus {
    outline: 2px solid var(--accent);
    outline-offset: -1px;
}

input[aria-invalid='true'] {
    border-color: var(--danger);
}

.triple {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 0.75rem;
}

.error-text {
    color: var(--danger);
    font-size: 0.8rem;
}

.duplicate-note {
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 0.75rem;
    background: var(--pill-bg);
    display: flex;
    flex-direction: column;
    gap: 0.3rem;
    align-items: flex-start;
}

.duplicate-title {
    font-size: 0.85rem;
    font-weight: 600;
}

.duplicate-row {
    font-size: 0.85rem;
}

.duplicate-row code {
    font-family: ui-monospace, Consolas, monospace;
}

.duplicate-hint {
    font-size: 0.8rem;
    color: var(--text-secondary);
}

.hint {
    font-size: 0.8rem;
    color: var(--text-secondary);
}

.ghost-btn {
    padding: 0.45rem 0.9rem;
    border: 1px solid var(--border);
    border-radius: 10px;
    background: transparent;
    color: var(--text-primary);
    font-size: 0.85rem;
    font-family: inherit;
    cursor: pointer;
}

.ghost-btn:hover:not(:disabled) {
    background: var(--pill-bg);
}

.ghost-btn:disabled {
    opacity: 0.45;
    cursor: not-allowed;
}

.primary-btn {
    padding: 0.55rem 1.4rem;
    border: none;
    border-radius: 999px;
    background: var(--accent);
    color: #fff;
    font-size: 0.95rem;
    font-weight: 600;
    font-family: inherit;
    cursor: pointer;
}

.primary-btn:hover:not(:disabled) {
    background: var(--accent-hover);
}

.primary-btn:disabled {
    opacity: 0.5;
    cursor: not-allowed;
}

.submit-error {
    color: var(--danger);
    font-size: 0.85rem;
}

.modal-footer {
    display: flex;
    justify-content: flex-end;
    gap: 0.75rem;
    padding-top: 1rem;
    border-top: 1px solid var(--border);
}

.success {
    display: flex;
    flex-direction: column;
    align-items: center;
    text-align: center;
    gap: 0.5rem;
    padding: 1.5rem 0 0;
}

.success-mark {
    width: 48px;
    height: 48px;
    border-radius: 50%;
    background: var(--accent);
    color: #fff;
    display: flex;
    align-items: center;
    justify-content: center;
}

.success h3 {
    margin: 0.5rem 0 0;
    font-size: 1.1rem;
    color: var(--text-primary);
}

.success-text {
    color: var(--text-secondary);
    font-size: 0.9rem;
}

.receipt {
    font-size: 0.8rem;
    color: var(--text-secondary);
}

.receipt code {
    font-family: ui-monospace, Consolas, monospace;
}

.success .modal-footer {
    width: 100%;
    margin-top: 1rem;
    justify-content: center;
}

@media (max-width: 640px) {
    .triple {
        grid-template-columns: 1fr;
    }
}
</style>
