import type { AgentStatus } from '../../types'
import type { StatusConfigMap } from './AgentStatusBar.types'

export const STATUS_CONFIG: StatusConfigMap = {
  idle:       { label: 'Ready',    node: ''                     },
  parsing:    { label: 'Running',  node: 'Analysing your code'  },
  retrieving: { label: 'Running',  node: 'Fetching standards'   },
  writing:    { label: 'Running',  node: 'Writing review'       },
  complete:   { label: 'Complete', node: ''                     },
  error:      { label: 'Error',    node: ''                     },
}

export const ANIMATED_STATUSES: AgentStatus[] = [
  'parsing',
  'retrieving',
  'writing',
]

export const DOT_ANIMATION_DELAYS = [0, 75, 150] as const

export const SEPARATOR = '→'
