import type { UIMessage } from '@ai-sdk/react'

/**
 * Helper to extract text content from UIMessage v3 parts
 * @param message - UIMessage to extract text from
 * @returns The text content or 'New Chat' if not found
 */
export function getMessageText(message: UIMessage | undefined): string {
  if (!message) return 'New Chat'
  // UIMessage v3 uses parts array, not content string
  const textPart = message.parts?.find(
    (p): p is { type: 'text'; text: string } => p.type === 'text'
  )
  return textPart?.text || 'New Chat'
}

/**
 * Filters out BM25 tool search calls from message history
 * BM25 is an internal tool filtering mechanism for non-Anthropic providers
 * These tool calls should not be persisted as they cause validation errors on replay
 * @param messages - Array of UI messages to filter
 * @returns Filtered messages with BM25 tool calls removed
 */
export function filterBM25ToolCalls(messages: UIMessage[]): UIMessage[] {
  return messages.map((message) => {
    if (!message.parts || message.role !== 'assistant') {
      return message
    }

    // Filter out tool-call and tool-result parts that reference BM25
    const filteredParts = message.parts.filter((part) => {
      // Remove BM25 tool call parts (tool name starts with "toolSearchBm25_")
      if (part.type === 'tool-call' && 'toolName' in part) {
        const toolName = (part as { toolName: string }).toolName
        if (toolName.startsWith('toolSearchBm25_')) {
          console.log(
            `[Message Filter] Removing BM25 tool call from history: ${toolName}`
          )
          return false
        }
      }

      // Remove BM25 tool result parts (tool name starts with "toolSearchBm25_")
      if (part.type === 'tool-result' && 'toolName' in part) {
        const toolName = (part as { toolName: string }).toolName
        if (toolName.startsWith('toolSearchBm25_')) {
          console.log(
            `[Message Filter] Removing BM25 tool result from history: ${toolName}`
          )
          return false
        }
      }

      return true
    })

    return {
      ...message,
      parts: filteredParts
    }
  })
}
