import { useEffect, useState } from 'react'
import { AgentStatusBar } from '../../components/AgentStatusBar'
import { ChatPanel } from '../../components/ChatPanel'
import { CodeInputPanel } from '../../components/CodeInputPanel'
import { DiffViewer } from '../../components/DiffViewer'
import { ReviewDisplay } from '../../components/ReviewDisplay'
import { StreamingIndicator } from '../../components/StreamingIndicator'
import { useReview } from '../../hooks/useReview'
import {
  APP_NAME,
  PROCESSING_LABELS,
  PROCESSING_STATUSES,
  REVIEW_PAGE_LABELS,
} from './ReviewPage.constants'
import styles from './ReviewPage.module.css'

type ActiveTab = 'review' | 'changes'

export function ReviewPage() {
  const {
    status,
    language,
    finalReview,
    chatHistory,
    isChatLoading,
    streamingMessage,
    error,
    diff,
    submitCode,
    askQuestion,
    reset,
  } = useReview()

  const [activeTab, setActiveTab] = useState<ActiveTab>('review')

  // Return to the Review tab whenever a new review is loaded or cleared
  useEffect(() => {
    setActiveTab('review')
  }, [finalReview])

  const isProcessing = PROCESSING_STATUSES.includes(status)
  const isWriting = status === 'writing'
  const hasDiff = Boolean(diff && diff !== 'No differences found.')

  // Show the partial review as tokens arrive; switch to finalReview when done
  const reviewContent = finalReview || (isWriting ? streamingMessage : '')

  return (
    <div className={styles.page}>
      <div className={styles.inner}>
        <div className={styles.topBar}>
          <div>
            <h1 className={styles.heading}>{APP_NAME}</h1>
          </div>
          {status !== 'idle' && (
            <button onClick={reset} className={styles.resetBtn}>
              {REVIEW_PAGE_LABELS.newReview}
            </button>
          )}
        </div>

        <div className={styles.statusRow}>
          <AgentStatusBar status={status} />
        </div>

        {error && (
          <div className={styles.error}>
            <strong>Error:</strong> {error}
          </div>
        )}

        <div className={styles.twoColLayout}>
          <div className={styles.leftCol}>
            <CodeInputPanel status={status} onSubmit={submitCode} />
            {language && (
              <div className={styles.languageBadge}>
                <span className={styles.languageTag}>{language}</span>
              </div>
            )}
          </div>

          <div className={styles.rightCol}>
            {/* Spinner for parsing / retrieving, and for writing before first token */}
            {isProcessing && (!isWriting || !streamingMessage) && (
              <StreamingIndicator label={PROCESSING_LABELS[status] ?? 'Processing…'} />
            )}

            {/* Live review while writing, then finalized review with tabs */}
            {reviewContent && (
              <>
                {finalReview && (
                  <div className={styles.tabBar}>
                    <button
                      className={`${styles.tab} ${activeTab === 'review' ? styles.tabActive : ''}`}
                      onClick={() => setActiveTab('review')}
                    >
                      {REVIEW_PAGE_LABELS.tabReview}
                    </button>
                    {hasDiff && (
                      <button
                        className={`${styles.tab} ${activeTab === 'changes' ? styles.tabActive : ''}`}
                        onClick={() => setActiveTab('changes')}
                      >
                        {REVIEW_PAGE_LABELS.tabChanges}
                      </button>
                    )}
                  </div>
                )}

                {(!finalReview || activeTab === 'review') && (
                  <>
                    <ReviewDisplay
                      content={reviewContent}
                      title={REVIEW_PAGE_LABELS.reviewTitle}
                      badge={isWriting ? 'writing…' : REVIEW_PAGE_LABELS.reviewBadge}
                      isStreaming={isWriting}
                    />
                    {finalReview && (
                      <ChatPanel
                        history={chatHistory}
                        isLoading={isChatLoading}
                        streamingMessage={streamingMessage}
                        onSend={askQuestion}
                      />
                    )}
                  </>
                )}

                {finalReview && activeTab === 'changes' && hasDiff && (
                  <DiffViewer diff={diff} title={REVIEW_PAGE_LABELS.diffTitle} />
                )}
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
