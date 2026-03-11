import { useRef, useState, useEffect, useCallback, type ReactNode, type ReactElement } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import type { Components } from 'react-markdown'
import type { ChatMessage } from '../../types'
import styles from './ChatPanel.module.css'

interface ChatPanelProps {
  history: ChatMessage[]
  isLoading: boolean
  streamingMessage: string
  onSend: (question: string) => void
}
//TODO  place it in the utils
function CopyIcon() {
  return (
    <svg className={styles.copyIcon} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
      <rect width="14" height="14" x="8" y="8" rx="2" ry="2" />
      <path d="M4 16c-1.1 0-2-.9-2-2V4c0-1.1.9-2 2-2h10c1.1 0 2 .9 2 2" />
    </svg>
  )
}

export function ChatPanel({ history, isLoading, streamingMessage, onSend }: ChatPanelProps) {
  const [input, setInput] = useState('')
  const [copiedCodeId, setCopiedCodeId] = useState<string | null>(null)
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [history, isLoading])

  const handleCopyCode = useCallback(async (code: string, codeBlockId: string) => {
    if (!code.trim()) return
    try {
      await navigator.clipboard.writeText(code)
      setCopiedCodeId(codeBlockId)
      setTimeout(() => setCopiedCodeId(null), 2000)
    } catch {
      /* clipboard not available */
    }
  }, [])

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

  function getCodeText(children: ReactNode): string {
    if (typeof children === 'string') return children
    if (Array.isArray(children)) return children.map(getCodeText).join('')
    if (children && typeof children === 'object' && 'props' in children) {
      const props = (children as ReactElement<{ children?: ReactNode }>).props
      return getCodeText(props.children)
    }
    return String(children ?? '')
  }

  function makeMarkdownComponents(bubbleId: number | 'streaming'): Components {
    let codeBlockIndex = 0
    return {
      pre({ children }) {
        const code = getCodeText(children).trim()
        const codeBlockId = `${bubbleId}-${codeBlockIndex++}`
        const isCopied = copiedCodeId === codeBlockId
        return (
          <div className={styles.codeBlockWrapper}>
            <button
              type="button"
              className={`${styles.copyCodeBtn} ${isCopied ? styles.copyCodeBtnCopied : ''}`}
              onClick={() => handleCopyCode(code, codeBlockId)}
              aria-label={isCopied ? 'Copied' : 'Copy code'}
            >
              <CopyIcon />
              {isCopied ? 'Copied!' : 'Copy code'}
            </button>
            <div className={styles.codeBlock}>{children}</div>
          </div>
        )
      },
    }
  }

  function renderAssistantBubble(content: string, id: number | 'streaming') {
    return (
      <div className={styles.assistantBubbleInner}>
        <article className={styles.assistantContent}>
          <ReactMarkdown remarkPlugins={[remarkGfm]} components={makeMarkdownComponents(id)}>
            {content}
          </ReactMarkdown>
          {isLoading && id === 'streaming' && <span className={styles.streamingCursor} />}
        </article>
      </div>
    )
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
                renderAssistantBubble(msg.content, i)
              )}
            </div>
          ))}

          {isLoading && (
            <div className={styles.assistantBubble}>
              {streamingMessage ? (
                renderAssistantBubble(streamingMessage, 'streaming')
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
