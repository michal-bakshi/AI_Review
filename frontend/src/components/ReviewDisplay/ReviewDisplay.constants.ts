/**
 * prose-* classes from @tailwindcss/typography cannot be used with @apply
 * inside CSS modules — PostCSS raises a circular dependency error.
 * Applied directly as a className string in the component instead.
 */
export const PROSE_CLASSES =
  'prose prose-invert prose-sm max-w-none ' +
  'prose-headings:text-gray-200 ' +
  'prose-p:text-gray-300 ' +
  'prose-code:text-indigo-300 prose-code:bg-gray-800 prose-code:rounded prose-code:px-1 ' +
  'prose-pre:bg-gray-800 ' +
  'prose-strong:text-gray-100 ' +
  'prose-li:text-gray-300'
