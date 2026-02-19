import { type FC, memo } from 'react'
import ReactMarkdown from 'react-markdown'
import rehypeRaw from 'rehype-raw'
import rehypeSanitize from 'rehype-sanitize'
import remarkGfm from 'remark-gfm'

import { cn } from '@/lib/utils'

import { type MarkdownRendererProps } from './types'
import { inlineComponents } from './inlineStyles'
import { components } from './styles'

// Module-level constants to avoid recreation on each render
const REMARK_PLUGINS = [remarkGfm]
const REHYPE_PLUGINS = [rehypeRaw, rehypeSanitize]

const MarkdownRendererBase: FC<MarkdownRendererProps> = ({
  children,
  classname,
  inline = false
}) => (
  <ReactMarkdown
    className={cn(
      'prose prose-h1:text-xl dark:prose-invert flex w-full flex-col gap-y-5 rounded-lg',
      classname
    )}
    components={inline ? inlineComponents : components}
    remarkPlugins={REMARK_PLUGINS}
    rehypePlugins={REHYPE_PLUGINS}
  >
    {children}
  </ReactMarkdown>
)

// Memoize with custom equality check
// Allow updates when content changes (important for streaming)
const MarkdownRenderer = memo(MarkdownRendererBase, (prevProps, nextProps) => {
  // Re-render if content/children changes (needed for streaming)
  if (prevProps.children !== nextProps.children) {
    return false
  }
  // Re-render if classname changes
  if (prevProps.classname !== nextProps.classname) {
    return false
  }
  // Re-render if inline mode changes
  if (prevProps.inline !== nextProps.inline) {
    return false
  }
  // Otherwise, skip re-render
  return true
})

MarkdownRenderer.displayName = 'MarkdownRenderer'

export default MarkdownRenderer
