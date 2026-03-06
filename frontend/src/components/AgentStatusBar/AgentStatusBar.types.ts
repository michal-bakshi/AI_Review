import type { AgentStatus } from '../../types'

export interface AgentStatusBarProps {
  status: AgentStatus
}

export interface StatusConfig {
  label: string
  node: string
}

export type StatusConfigMap = Record<AgentStatus, StatusConfig>
