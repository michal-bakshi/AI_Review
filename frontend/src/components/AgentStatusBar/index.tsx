import type { AgentStatusBarProps } from './AgentStatusBar.types'
import {
  ANIMATED_STATUSES,
  DOT_ANIMATION_DELAYS,
  SEPARATOR,
  STATUS_CONFIG,
} from './AgentStatusBar.constants'
import styles from './AgentStatusBar.module.css'

export function AgentStatusBar({ status }: AgentStatusBarProps) {
  const { label, node } = STATUS_CONFIG[status]
  const isAnimated = ANIMATED_STATUSES.includes(status)

  return (
    <div className={`${styles.bar} ${styles[status]}`}>
      {isAnimated && (
        <span className={styles.dot}>
          {DOT_ANIMATION_DELAYS.map((delay) => (
            <span key={delay} style={{ animationDelay: `${delay}ms` }} />
          ))}
        </span>
      )}
      <span className={styles.statusLabel}>{label}</span>
      {node && (
        <>
          <span className={styles.separator}>{SEPARATOR}</span>
          <span className={styles.nodeName}>{node}</span>
        </>
      )}
    </div>
  )
}
