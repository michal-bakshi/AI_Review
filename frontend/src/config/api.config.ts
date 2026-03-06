/** Single source of truth for all API configuration. */

export const API_BASE_URL: string = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

export const API_ENDPOINTS = {
  reviewStart:       '/review/start',
  reviewStartStream: '/review/start/stream',
  reviewChat:        (threadId: string) => `/review/${threadId}/chat`,
  reviewChatStream:  (threadId: string) => `/review/${threadId}/chat/stream`,
} as const
