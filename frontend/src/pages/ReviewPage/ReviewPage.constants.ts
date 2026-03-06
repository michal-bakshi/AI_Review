import type { AgentStatus } from '../../types'

export const APP_NAME = 'AI Code Review Agent'

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
