import type { UIMessage } from '@ai-sdk/react'

/**
 * Ensures every message has a non-empty `id`.
 *
 * The AI SDK's multi-step agent responses sometimes produce intermediate
 * assistant messages with empty-string IDs.  assistant-ui's MessageRepository
 * uses IDs to build a parent→child tree, so two messages sharing the same
 * `""` key corrupt the tree and cause earlier messages to vanish from the
 * rendered thread.
 *
 * Call this when loading messages from the database AND before persisting so
 * that stored data is always clean.
 */
export function ensureMessageIds(messages: UIMessage[]): UIMessage[] {
  return messages.map((msg) => {
    if (msg.id) return msg
    return { ...msg, id: crypto.randomUUID() }
  })
}

/**
 * Deduplicates tool calls and tool results by toolCallId
 * Prevents "Duplicate key toolCallId-xyz in tapResources" errors in Assistant UI
 * Keeps the first occurrence and removes subsequent duplicates
 * @param messages - Array of UI messages to deduplicate
 * @returns Messages with duplicate tool call IDs removed
 */
export function deduplicateToolCalls(messages: UIMessage[]): UIMessage[] {
  // Track tool-call and tool-result IDs separately
  // A tool-call and tool-result SHOULD share the same ID (call -> result)
  // But we shouldn't have TWO tool-calls with the same ID, or TWO tool-results with the same ID
  const seenToolCallIds = new Set<string>()
  const seenToolResultIds = new Set<string>()

  return messages.map((message) => {
    if (!message.parts) {
      return message
    }

    // Filter out duplicate tool-call and tool-result parts
    const deduplicatedParts = message.parts.filter((part) => {
      // Check if part has a toolCallId (any tool-related part)
      if ('toolCallId' in part && part.toolCallId) {
        const toolCallId = (part as { toolCallId: string }).toolCallId

        // Determine if this is a tool call or tool result based on part type
        // Tool calls: 'tool-call', 'tool-{toolName}', 'dynamic-tool'
        // Tool results: 'tool-result'
        const isToolResult = part.type === 'tool-result'

        if (isToolResult) {
          // Check for duplicate tool results
          if (seenToolResultIds.has(toolCallId)) {
            console.log(
              `[Message Dedup] Removing duplicate tool-result with ID: ${toolCallId}`
            )
            return false
          }
          seenToolResultIds.add(toolCallId)
        } else {
          // Check for duplicate tool calls (any other tool type)
          if (seenToolCallIds.has(toolCallId)) {
            console.log(
              `[Message Dedup] Removing duplicate tool-call (type: ${part.type}) with ID: ${toolCallId}`
            )
            return false
          }
          seenToolCallIds.add(toolCallId)
        }
      }

      return true
    })

    return {
      ...message,
      parts: deduplicatedParts
    }
  })
}
