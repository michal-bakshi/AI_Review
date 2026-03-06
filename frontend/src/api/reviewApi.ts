/** Typed fetch wrappers for the AI Code Review Agent backend API. */

import axios from 'axios'
import { API_BASE_URL, API_ENDPOINTS } from '../config/api.config'
import { SSE_DATA_PREFIX } from '../constants/sse'
import type { ChatRequest, ChatResponse, ChatStreamChunk, ReviewStartResponse, ReviewStreamChunk } from '../types'

const api = axios.create({ baseURL: API_BASE_URL })

// ── Non-streaming endpoints ────────────────────────────────────────────────────

export async function startReview(code: string): Promise<ReviewStartResponse> {
  const { data } = await api.post<ReviewStartResponse>(API_ENDPOINTS.reviewStart, { code })
  return data
}

export async function chatAboutReview(
  threadId: string,
  payload: ChatRequest,
): Promise<ChatResponse> {
  const { data } = await api.post<ChatResponse>(API_ENDPOINTS.reviewChat(threadId), payload)
  return data
}

// ── SSE streaming ──────────────────────────────────────────────────────────────

async function* readSseStream<T>(url: string, body: unknown): AsyncGenerator<T> {
  const response = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })

  if (!response.ok) throw new Error(`HTTP ${response.status}`)
  if (!response.body) throw new Error('No response body from server')

  const reader = response.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''

  while (true) {
    const { done, value } = await reader.read()
    if (done) break

    buffer += decoder.decode(value, { stream: true })
    const lines = buffer.split('\n')
    buffer = lines.pop() ?? ''

    for (const line of lines) {
      if (line.startsWith(SSE_DATA_PREFIX)) {
        const raw = line.slice(SSE_DATA_PREFIX.length).trim()
        if (raw) yield JSON.parse(raw) as T
      }
    }
  }
}

export function streamStartReview(code: string): AsyncGenerator<ReviewStreamChunk> {
  return readSseStream<ReviewStreamChunk>(
    `${API_BASE_URL}${API_ENDPOINTS.reviewStartStream}`,
    { code },
  )
}

export function streamChatAboutReview(
  threadId: string,
  payload: ChatRequest,
): AsyncGenerator<ChatStreamChunk> {
  return readSseStream<ChatStreamChunk>(
    `${API_BASE_URL}${API_ENDPOINTS.reviewChatStream(threadId)}`,
    payload,
  )
}
