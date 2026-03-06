import type { StreamingIndicatorProps } from './StreamingIndicator.types'
import { DEFAULT_LABEL, DOT_ANIMATION_DELAYS } from './StreamingIndicator.constants'
import styles from './StreamingIndicator.module.css'

export function StreamingIndicator({ label = DEFAULT_LABEL }: StreamingIndicatorProps) {
  return (
    <div className={styles.wrapper}>
      <div className={styles.dots}>
        {DOT_ANIMATION_DELAYS.map((delay) => (
          <span key={delay} className={styles.dot} style={{ animationDelay: `${delay}ms` }} />
        ))}
      </div>
      <span className={styles.label}>{label}</span>
    </div>
  )
}
