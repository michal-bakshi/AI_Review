import { useState } from 'react'
import type { ApprovalPanelProps } from './ApprovalPanel.types'
import { APPROVAL_LABELS, FEEDBACK_ROWS } from './ApprovalPanel.constants'
import styles from './ApprovalPanel.module.css'

export function ApprovalPanel({ onApprove, isLoading }: ApprovalPanelProps) {
  const [feedback, setFeedback] = useState('')
  const [showFeedback, setShowFeedback] = useState(false)

  function handleApprove() {
    onApprove(true)
  }

  function handleRequestChanges() {
    if (!showFeedback) {
      setShowFeedback(true)
      return
    }
    onApprove(false, feedback)
  }

  return (
    <div className={styles.panel}>
      <div className={styles.header}>
        <span className={styles.pulse} />
        <h3 className={styles.title}>{APPROVAL_LABELS.title}</h3>
      </div>

      <p className={styles.description}>
        {APPROVAL_LABELS.description}{' '}
        <code className={styles.nodeName}>{APPROVAL_LABELS.nodeName}</code>
        {APPROVAL_LABELS.descriptionSuffix}
      </p>

      {showFeedback && (
        <textarea
          value={feedback}
          onChange={(e) => setFeedback(e.target.value)}
          placeholder={APPROVAL_LABELS.feedbackPlaceholder}
          rows={FEEDBACK_ROWS}
          className={styles.feedbackArea}
        />
      )}

      <div className={styles.actions}>
        <button onClick={handleApprove} disabled={isLoading} className={styles.approveBtn}>
          {APPROVAL_LABELS.approveBtn}
        </button>
        <button onClick={handleRequestChanges} disabled={isLoading} className={styles.changesBtn}>
          {showFeedback ? APPROVAL_LABELS.submitFeedbackBtn : APPROVAL_LABELS.requestChangesBtn}
        </button>
      </div>
    </div>
  )
}
