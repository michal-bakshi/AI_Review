export const APPROVAL_LABELS = {
  title: 'Human-in-the-Loop',
  description: 'The LangGraph graph is paused at',
  nodeName: 'human_approval',
  descriptionSuffix: '. Approve to finalise, or request changes to revise the review.',
  feedbackPlaceholder: "Describe the changes you'd like…",
  approveBtn: '✓ Approve',
  submitFeedbackBtn: '↩ Submit Feedback',
  requestChangesBtn: '✎ Request Changes',
} as const

export const FEEDBACK_ROWS = 4
