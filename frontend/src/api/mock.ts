// Fake backend for the contribution flow, so the frontend can run and be
// verified before the real endpoints exist. Flip VITE_USE_MOCK to false (or
// drop it) once the backend session ships /contributions.

import type {
    ContributionDraft,
    ContributionReceipt,
    GlossaryHit,
} from './types'

const STORAGE_KEY = 'cantolens.mock.contributions'

/** A slice of backend/data/tokens100.csv, enough for the duplicate check to hit. */
const GLOSSARY: GlossaryHit[] = [
    { token: 'gayau', cantonese: '加油', mandarin: '加油', english: 'keep it up', function: 'expression' },
    { token: 'garyau', cantonese: '加油', mandarin: '加油', english: 'keep it up', function: 'expression' },
    { token: 'mm', cantonese: '唔', mandarin: '不', english: 'not', function: 'negation' },
    { token: 'can mm can', cantonese: '得唔得', mandarin: '可不可以', english: 'can or not / is it okay', function: 'question phrase' },
    { token: 'duk', cantonese: '得', mandarin: '可以', english: 'can', function: 'verb' },
    { token: 'ho', cantonese: '好', mandarin: '好', english: 'can / okay', function: 'modal' },
    { token: 'jeng', cantonese: '正', mandarin: '很棒', english: 'great / nice', function: 'adjective' },
    { token: 'siu sei', cantonese: '笑死', mandarin: '笑死', english: 'so funny', function: 'expression' },
    { token: 'ho chi', cantonese: '好似', mandarin: '好像', english: 'seem / look like', function: 'verb' },
    { token: 'la', cantonese: '啦', mandarin: '啦', english: '(final particle)', function: 'particle' },
    { token: 'lor', cantonese: '囉', mandarin: '囉', english: '(obvious tone particle)', function: 'particle' },
    { token: 'dou', cantonese: '都', mandarin: '都', english: 'also', function: 'adverb' },
    { token: 'hea', cantonese: 'hea', mandarin: '混日子', english: 'laze around', function: 'verb' },
    { token: 'leng jai', cantonese: '靚仔', mandarin: '帥哥', english: 'handsome guy', function: 'noun' },
    { token: 'leng nui', cantonese: '靚女', mandarin: '美女', english: 'pretty girl', function: 'noun' },
]

const delay = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms))

function readStore(): (ContributionDraft & ContributionReceipt)[] {
    try {
        return JSON.parse(localStorage.getItem(STORAGE_KEY) ?? '[]')
    } catch {
        return []
    }
}

function writeStore(rows: (ContributionDraft & ContributionReceipt)[]) {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(rows))
}

export async function mockSearchGlossary(query: string): Promise<GlossaryHit[]> {
    await delay(180)
    const needle = query.trim().toLowerCase()
    if (!needle) return []
    return GLOSSARY.filter((row) => row.token === needle || row.token.startsWith(`${needle} `)).slice(0, 3)
}

export async function mockSubmitContribution(draft: ContributionDraft): Promise<ContributionReceipt> {
    await delay(600)
    const receipt: ContributionReceipt = {
        id: `mock-${Date.now().toString(36)}`,
        status: 'pending',
        createdAt: new Date().toISOString(),
    }
    writeStore([...readStore(), { ...draft, ...receipt }])
    return receipt
}
