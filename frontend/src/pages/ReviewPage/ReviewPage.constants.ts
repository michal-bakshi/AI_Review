import type { AgentStatus } from '../../types'

export const APP_NAME = 'AI Code Review Agent'

export const WELCOME_PANEL = {
  title: 'Get started',
  subtitle: 'Paste your code on the left and run a review to see feedback, suggestions, and optional code changes.',
  steps: [
    { label: 'Paste or type your code', detail: 'Any language supported' },
    { label: 'Run AI Review', detail: 'Analysis and standards-based feedback' },
    { label: 'Read and iterate', detail: 'Ask follow-up questions in chat' },
  ],
} as const

export const REVIEW_PAGE_LABELS = {
  newReview: 'New Review',
  reviewTitle: 'Code Review',
  reviewBadge: 'complete',
  tabReview: 'Review',
  tabChanges: 'Changes',
  diffTitle: 'Code Changes',
} as const

export const PROCESSING_LABELS: Record<string, string> = {
  parsing:    'Analysing your code…',
  retrieving: 'Fetching coding standards…',
  writing:    'Writing your review…',
}

export const PROCESSING_STATUSES: AgentStatus[] = [
  'parsing',
  'retrieving',
  'writing',
]
