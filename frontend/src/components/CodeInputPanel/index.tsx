import { useState } from 'react'
import type { CodeInputPanelProps } from './CodeInputPanel.types'
import {
  CODE_INPUT_LABELS,
  LOADING_STATUSES,
  PLACEHOLDER_CODE,
  TEXTAREA_ROWS,
} from './CodeInputPanel.constants'
import styles from './CodeInputPanel.module.css'

export function CodeInputPanel({ status, onSubmit }: CodeInputPanelProps) {
  const [code, setCode] = useState('')
  const isLoading = LOADING_STATUSES.includes(status)

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

      <textarea
        value={code}
        onChange={(e) => setCode(e.target.value)}
        placeholder={PLACEHOLDER_CODE}
        disabled={isLoading}
        rows={TEXTAREA_ROWS}
        className={styles.textarea}
      />

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
