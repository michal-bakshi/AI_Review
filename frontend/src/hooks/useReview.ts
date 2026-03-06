/** Custom hook that orchestrates the full code review lifecycle. */

import { useState } from 'react'
import { streamChatAboutReview, streamStartReview } from '../api/reviewApi'
import { SSE_TYPE } from '../constants/sse'
import type { AgentStatus, ChatMessage } from '../types'

interface UseReviewResult {
  status: AgentStatus
  finalReview: string
  language: string
  threadId: string | null
  chatHistory: ChatMessage[]
  isChatLoading: boolean
  streamingMessage: string
  error: string | null
  diff: string | null
  submitCode: (code: string) => Promise<void>
  askQuestion: (question: string) => Promise<void>
  reset: () => void
}

export function useReview(): UseReviewResult {
  const [status, setStatus] = useState<AgentStatus>('idle')
  const [threadId, setThreadId] = useState<string | null>(null)
  const [finalReview, setFinalReview] = useState('')
  const [language, setLanguage] = useState('')
  const [chatHistory, setChatHistory] = useState<ChatMessage[]>([])
  const [isChatLoading, setIsChatLoading] = useState(false)
  const [streamingMessage, setStreamingMessage] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [diff, setDiff] = useState<string | null>(null)

  /**
   * Tracks the "current" code state. Starts as the submitted code, then updates
   * each time the AI generates a fix so that follow-up modification requests diff
   * against the previous fix rather than the original submitted code.
   */
  const [currentCode, setCurrentCode] = useState<string>('')

  async function submitCode(code: string): Promise<void> {
    setStatus('parsing')
    setError(null)
    setFinalReview('')
    setStreamingMessage('')
    setChatHistory([])
    setDiff(null)
    setCurrentCode(code)

    let accumulated = ''

    try {
      for await (const chunk of streamStartReview(code)) {
        if (chunk.type === SSE_TYPE.STATUS) {
          setStatus(chunk.content as AgentStatus)
        } else if (chunk.type === SSE_TYPE.TOKEN) {
          accumulated += chunk.content ?? ''
          setStreamingMessage(accumulated)
        } else if (chunk.type === SSE_TYPE.DONE) {
          setThreadId(chunk.thread_id!)
          setLanguage(chunk.language!)
          setFinalReview(accumulated || chunk.final_review || '')
          setStatus('complete')
        } else if (chunk.type === SSE_TYPE.ERROR) {
          throw new Error(chunk.content)
        }
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error starting review')
      setStatus('error')
    } finally {
      setStreamingMessage('')
    }
  }

  async function askQuestion(question: string): Promise<void> {
    if (!threadId) return
    setIsChatLoading(true)
    setStreamingMessage('')
    setError(null)

    const userMsg: ChatMessage = { role: 'user', content: question }
    const historyWithUser = [...chatHistory, userMsg]
    setChatHistory(historyWithUser)

    let accumulated = ''

    try {
      for await (const chunk of streamChatAboutReview(threadId, {
        question,
        history: chatHistory,
        current_code: currentCode,
      })) {
        if (chunk.type === SSE_TYPE.TOKEN) {
          accumulated += chunk.content ?? ''
          setStreamingMessage(accumulated)
        } else if (chunk.type === SSE_TYPE.DONE) {
          if (chunk.diff != null) setDiff(chunk.diff)
          if (chunk.generated_code) setCurrentCode(chunk.generated_code)
        } else if (chunk.type === SSE_TYPE.SCORE_UPDATE) {
          if (chunk.updated_review) setFinalReview(chunk.updated_review)
        } else if (chunk.type === SSE_TYPE.ERROR) {
          throw new Error(chunk.content)
        }
      }
      setChatHistory([...historyWithUser, { role: 'assistant', content: accumulated }])
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error in chat')
      setChatHistory(chatHistory)
    } finally {
      setStreamingMessage('')
      setIsChatLoading(false)
    }
  }

  function reset(): void {
    setStatus('idle')
    setThreadId(null)
    setFinalReview('')
    setLanguage('')
    setChatHistory([])
    setIsChatLoading(false)
    setStreamingMessage('')
    setError(null)
    setDiff(null)
    setCurrentCode('')
  }

  return {
    status,
    finalReview,
    language,
    threadId,
    chatHistory,
    isChatLoading,
    streamingMessage,
    error,
    diff,
    submitCode,
    askQuestion,
    reset,
  }
}
