import { useRef, useState, useEffect } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import type { ChatMessage } from '../../types'
import styles from './ChatPanel.module.css'

interface ChatPanelProps {
  history: ChatMessage[]
  isLoading: boolean
  streamingMessage: string
  onSend: (question: string) => void
}

export function ChatPanel({ history, isLoading, streamingMessage, onSend }: ChatPanelProps) {
  const [input, setInput] = useState('')
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [history, isLoading])

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    const q = input.trim()
    if (!q || isLoading) return
    setInput('')
    onSend(q)
  }

  function handleKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit(e as unknown as React.FormEvent)
    }
  }

  return (
    <div className={styles.panel}>
      <div className={styles.header}>
        <span className={styles.headerIcon}>💬</span>
        <h3 className={styles.headerTitle}>Ask about this review</h3>
      </div>

      {history.length > 0 && (
        <div className={styles.messages}>
          {history.map((msg, i) => (
            <div
              key={i}
              className={msg.role === 'user' ? styles.userBubble : styles.assistantBubble}
            >
              {msg.role === 'user' ? (
                <p className={styles.userText}>{msg.content}</p>
              ) : (
                <article className="prose prose-invert prose-sm max-w-none prose-p:text-gray-300 prose-p:my-1 prose-headings:text-white prose-li:text-gray-300 prose-code:before:content-none prose-code:after:content-none prose-code:bg-gray-700 prose-code:px-1 prose-code:py-0.5 prose-code:rounded prose-code:text-indigo-300 prose-code:text-xs prose-pre:bg-gray-900 prose-pre:border prose-pre:border-gray-700">
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>{msg.content}</ReactMarkdown>
                </article>
              )}
            </div>
          ))}

          {isLoading && (
            <div className={styles.assistantBubble}>
              {streamingMessage ? (
                <article className="prose prose-invert prose-sm max-w-none prose-p:text-gray-300 prose-p:my-1 prose-headings:text-white prose-li:text-gray-300 prose-code:before:content-none prose-code:after:content-none prose-code:bg-gray-700 prose-code:px-1 prose-code:py-0.5 prose-code:rounded prose-code:text-indigo-300 prose-code:text-xs prose-pre:bg-gray-900 prose-pre:border prose-pre:border-gray-700">
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>{streamingMessage}</ReactMarkdown>
                  <span className={styles.streamingCursor} />
                </article>
              ) : (
                <span className={styles.typingDots}>
                  <span />
                  <span />
                  <span />
                </span>
              )}
            </div>
          )}

          <div ref={bottomRef} />
        </div>
      )}

      <form onSubmit={handleSubmit} className={styles.form}>
        <textarea
          className={styles.input}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask a follow-up question… (Enter to send, Shift+Enter for newline)"
          rows={2}
          disabled={isLoading}
        />
        <button type="submit" className={styles.sendBtn} disabled={isLoading || !input.trim()}>
          {isLoading ? '…' : '↑'}
        </button>
      </form>
    </div>
  )
}
