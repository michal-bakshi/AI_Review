import type { AgentStatus } from '../../types'

export interface CodeInputPanelProps {
  status: AgentStatus
  onSubmit: (code: string) => void
}
