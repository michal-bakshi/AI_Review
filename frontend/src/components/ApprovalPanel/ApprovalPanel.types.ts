export interface ApprovalPanelProps {
  onApprove: (approved: boolean, feedback?: string) => void
  isLoading: boolean
}
