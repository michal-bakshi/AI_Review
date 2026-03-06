import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import type { Components } from 'react-markdown'
import type { ReviewDisplayProps } from './ReviewDisplay.types'
import styles from './ReviewDisplay.module.css'

const markdownComponents: Components = {
  // Replace <pre> with a styled div so prose styles don't interfere
  pre({ children }) {
    return <div className={styles.codeBlock}>{children}</div>
  },

  code({ className, children, ...props }) {
    const isBlock = !!className
    const lang = className?.replace('language-', '') ?? ''

    if (isBlock) {
      return (
        <>
          {lang && (
            <div className={styles.codeLangBar}>
              <span className={styles.codeLangDot} />
              <span className={styles.codeLangDot} />
              <span className={styles.codeLangDot} />
              <span className={styles.codeLangLabel}>{lang}</span>
            </div>
          )}
          <code className={styles.codeContent} {...props}>
            {children}
          </code>
        </>
      )
    }

    return (
      <code className={styles.inlineCode} {...props}>
        {children}
      </code>
    )
  },
}

export function ReviewDisplay({ content, title = 'Review', badge, isStreaming = false }: ReviewDisplayProps) {
  if (!content) return null

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <h3 className={styles.title}>{title}</h3>
        {badge && <span className={styles.badge}>{badge}</span>}
      </div>

      <article
        className={[
          'prose prose-invert prose-sm max-w-none',
          'prose-headings:font-semibold prose-headings:text-white prose-headings:border-b prose-headings:border-gray-700/60 prose-headings:pb-1 prose-headings:mb-3',
          'prose-p:text-gray-300 prose-p:leading-relaxed',
          'prose-li:text-gray-300',
          'prose-strong:text-white prose-strong:font-semibold',
          'prose-blockquote:border-l-indigo-500 prose-blockquote:text-gray-400',
          // Remove default prose styling for code so our custom classes take over
          'prose-code:before:content-none prose-code:after:content-none',
          'prose-code:bg-transparent prose-code:text-inherit prose-code:font-normal prose-code:p-0',
          'prose-pre:bg-transparent prose-pre:p-0 prose-pre:my-0',
          styles.prose,
        ].join(' ')}
      >
        <ReactMarkdown remarkPlugins={[remarkGfm]} components={markdownComponents}>
          {content}
        </ReactMarkdown>
        {isStreaming && <span className={styles.streamingCursor} />}
      </article>
    </div>
  )
}
