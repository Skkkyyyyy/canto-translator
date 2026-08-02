// Shared shapes for the contribution flow.
// The backend session owns the real implementation; these types are the contract.

/** A word/phrase entry vs. a correction of a whole sentence. */
export type ContributionKind = 'token' | 'sentence'

/** Brand new entry, or a fix to something already in the glossary. */
export type ContributionIntent = 'new' | 'correction'

export interface ContributionDraft {
    kind: ContributionKind
    intent: ContributionIntent
    /** Romanized spelling for a token, or the full romanized sentence. */
    token: string
    cantonese: string
    mandarin: string
    english: string
    /** Part of speech — token entries only, matches the Function column. */
    function: string
    example: string
    note: string
    /** Optional, so we can credit the contributor. */
    contributor: string
    /** What the user typed into the translator when they hit this. */
    sourceText?: string
    /** What we gave back, so a reviewer can see what went wrong. */
    sourceOutput?: {
        cantonese: string
        mandarin: string
        english: string
    }
}

export interface ContributionReceipt {
    id: string
    status: 'pending'
    createdAt: string
}

/** One row of the existing glossary, used for the duplicate check. */
export interface GlossaryHit {
    token: string
    cantonese: string
    mandarin: string
    english: string
    function: string
}
