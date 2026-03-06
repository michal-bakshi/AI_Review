import type { DiffViewerProps } from './DiffViewer.types'
import styles from './DiffViewer.module.css'

const NO_DIFF_SENTINEL = 'No differences found.'

function getLineClass(line: string): string {
  if (line.startsWith('+++') || line.startsWith('---')) return styles.lineHeader
  if (line.startsWith('+')) return styles.lineAdd
  if (line.startsWith('-')) return styles.lineDelete
  if (line.startsWith('@@')) return styles.lineChunk
  return styles.lineContext
}

export function DiffViewer({ diff, title = 'Changes' }: DiffViewerProps) {
  const isEmpty = !diff || diff.trim() === '' || diff.trim() === NO_DIFF_SENTINEL

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <h3 className={styles.title}>{title}</h3>
      </div>

      {isEmpty ? (
        <div className={styles.empty}>
          <span className={styles.emptyText}>No differences — the generated code required no revision.</span>
        </div>
      ) : (
        <div className={styles.diffBlock}>
          {diff!.split('\n').map((line, index) => (
            <div key={index} className={`${styles.line} ${getLineClass(line)}`}>
              <span className={styles.lineNumber}>{index + 1}</span>
              <span className={styles.lineContent}>{line}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
