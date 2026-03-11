import { useState, useRef, useEffect } from 'react'
import type { CodeInputPanelProps } from './CodeInputPanel.types'
import {
  CODE_INPUT_LABELS,
  LOADING_STATUSES,
  PLACEHOLDER_CODE,
} from './CodeInputPanel.constants'
import styles from './CodeInputPanel.module.css'

const LINE_HEIGHT_REM = 1.65

export function CodeInputPanel({ status, onSubmit }: CodeInputPanelProps) {
  const [code, setCode] = useState('')
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const isLoading = LOADING_STATUSES.includes(status)
//TODO  place it
  const lineCount = Math.max(1, code.split('\n').length)

  useEffect(() => {
    const ta = textareaRef.current
    if (!ta) return
    const minHeight = 20 * 16
    ta.style.height = '0'
    ta.style.height = `${Math.max(ta.scrollHeight, minHeight)}px`
  }, [code])

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (code.trim()) onSubmit(code.trim())
  }

  return (
    <form onSubmit={handleSubmit} className={styles.form}>
      <div className={styles.header}>
        <h2 className={styles.title}>{CODE_INPUT_LABELS.title}</h2>
        <span className={styles.hint}>{CODE_INPUT_LABELS.hint}</span>
      </div>

      <div className={styles.editorWrapper}>
        <div
          className={styles.lineNumbers}
          style={{ lineHeight: LINE_HEIGHT_REM }}
          aria-hidden
        >
          {Array.from({ length: lineCount }, (_, i) => (
            <span key={i} className={styles.lineNumber}>
              {i + 1}
            </span>
          ))}
        </div>
        <div className={styles.codeArea}>
          <textarea
            ref={textareaRef}
            value={code}
            onChange={(e) => setCode(e.target.value)}
            placeholder={PLACEHOLDER_CODE}
            disabled={isLoading}
            className={styles.textarea}
            spellCheck={false}
            aria-label="Code input"
          />
        </div>
      </div>

      <button
        type="submit"
        disabled={!code.trim() || isLoading}
        className={styles.submitBtn}
      >
        {isLoading ? CODE_INPUT_LABELS.loading : CODE_INPUT_LABELS.submit}
      </button>
    </form>
  )
}
