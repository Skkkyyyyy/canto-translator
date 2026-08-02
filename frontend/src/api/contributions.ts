import { request, USE_MOCK } from './client'
import { mockSearchGlossary, mockSubmitContribution } from './mock'
import type { ContributionDraft, ContributionReceipt, GlossaryHit } from './types'

/** Does the glossary already have this token? Used to steer duplicates into corrections. */
export function searchGlossary(query: string): Promise<GlossaryHit[]> {
    if (USE_MOCK) return mockSearchGlossary(query)
    return request<{ results: GlossaryHit[] }>(
        `/glossary/search?q=${encodeURIComponent(query)}`,
    ).then((data) => data.results)
}

export function submitContribution(draft: ContributionDraft): Promise<ContributionReceipt> {
    if (USE_MOCK) return mockSubmitContribution(draft)
    return request<ContributionReceipt>('/contributions', {
        method: 'POST',
        body: JSON.stringify(draft),
    })
}
