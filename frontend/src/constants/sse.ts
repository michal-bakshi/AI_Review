/** Constants for the Server-Sent Events stream protocol. */

export const SSE_DATA_PREFIX = 'data: '

export const SSE_TYPE = {
  STATUS:       'status',
  TOKEN:        'token',
  DONE:         'done',
  ERROR:        'error',
  SCORE_UPDATE: 'score_update',
} as const

export type SseEventType = typeof SSE_TYPE[keyof typeof SSE_TYPE]
