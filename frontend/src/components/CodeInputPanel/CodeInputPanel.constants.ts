import type { AgentStatus } from '../../types'

export const CODE_INPUT_LABELS = {
  title: 'Code Input',
  hint: 'Paste any language',
  submit: 'Run AI Review',
  loading: 'Reviewing…',
} as const

export const TEXTAREA_ROWS = 18

export const LOADING_STATUSES: AgentStatus[] = [
  'parsing',
  'retrieving',
  'writing',
]

export const PLACEHOLDER_CODE = `// Paste your code here for review…

function calculateTotal(items) {
  var total = 0
  for (var i = 0; i < items.length; i++) {
    total = total + items[i].price
  }
  return total
}`
