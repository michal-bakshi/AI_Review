/** Shared TypeScript types for the AI Code Review Agent frontend. */

import type { SseEventType } from '../constants/sse'

export interface ReviewStartResponse {
  thread_id: string
  final_review: string
  language: string
}

export interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
}

export interface ChatRequest {
  question: string
  history: ChatMessage[]
  current_code?: string
}

export interface ChatResponse {
  answer: string
  diff?: string | null
}

export type AgentStatus =
  | 'idle'
  | 'parsing'
  | 'retrieving'
  | 'writing'
  | 'complete'
  | 'error'

export interface ReviewStreamChunk {
  type: SseEventType
  content?: string
  thread_id?: string
  language?: string
  final_review?: string
}

export interface ChatStreamChunk {
  type: SseEventType
  content?: string
  diff?: string | null
  generated_code?: string
  updated_review?: string
}
