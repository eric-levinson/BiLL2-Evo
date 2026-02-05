import type { ToolCall } from '@/types/playground'
import type { UIMessage } from '@ai-sdk/react'

export type { UIMessage }

/**
 * Adapted message format for rendering in the chat UI.
 * This format is compatible with MessageItem components.
 */
export interface AdaptedMessage {
  id: string
  role: 'user' | 'assistant' | 'system'
  content: string
  tool_calls?: ToolCall[]
  created_at: number
}

/**
 * Converts a Vercel AI SDK v3 UIMessage to a format that can be rendered
 * by the existing MessageItem components.
 *
 * Handles these message part types:
 * - text: Regular message content
 * - dynamic-tool: Tool calls from MCP (with states: input-available, output-available, etc.)
 *
 * @param message - The UIMessage from useChat() hook
 * @returns An adapted message compatible with MessageItem rendering
 */
export function adaptUIMessage(message: UIMessage): AdaptedMessage {
  const now = Date.now()

  // Extract text content from text parts
  const textContent = message.parts
    .filter((part) => part.type === 'text')
    .map((part) => (part as { type: 'text'; text: string }).text)
    .join('')

  // Extract tool calls from dynamic-tool parts
  const toolParts = message.parts.filter(
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    (part: any) => part.type === 'dynamic-tool'
  )

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const toolCalls: ToolCall[] = toolParts.map((part: any) => {
    const hasOutput = part.state === 'output-available'
    const hasError = part.state === 'output-error'

    return {
      role: 'assistant' as const,
      content: hasOutput ? JSON.stringify(part.output, null, 2) : null,
      tool_call_id: part.toolCallId,
      tool_name: part.toolName,
      tool_args: (part.input ?? {}) as Record<string, string>,
      tool_call_error: hasError,
      metrics: {
        time: 0
      },
      created_at: now
    }
  })

  return {
    id: message.id,
    role: message.role,
    content: textContent,
    tool_calls: toolCalls.length > 0 ? toolCalls : undefined,
    created_at: now
  }
}

/**
 * Converts an array of UIMessages to adapted format.
 *
 * @param messages - Array of UIMessages from useChat() hook
 * @returns Array of adapted messages ready for rendering
 */
export function adaptUIMessages(messages: UIMessage[]): AdaptedMessage[] {
  return messages.map(adaptUIMessage)
}
