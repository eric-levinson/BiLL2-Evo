import type { ToolCall } from '@/types/playground'

/**
 * Represents a UI message part from the Vercel AI SDK.
 * Messages can contain multiple parts: text, tool invocations, and tool results.
 */
export type UIMessagePart =
  | {
      type: 'text'
      text: string
    }
  | {
      type: 'tool-invocation'
      toolCallId: string
      toolName: string
      args: Record<string, unknown>
      state?: 'partial' | 'call'
    }
  | {
      type: 'tool-result'
      toolCallId: string
      toolName: string
      result: unknown
    }

/**
 * Represents a message from the Vercel AI SDK useChat() hook.
 */
export interface UIMessage {
  id: string
  role: 'user' | 'assistant' | 'system'
  content: string
  parts?: UIMessagePart[]
  createdAt?: Date
}

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
 * Converts a Vercel AI SDK UIMessage to a format that can be rendered
 * by the existing MessageItem components.
 *
 * Handles three types of message parts:
 * - text: Regular message content
 * - tool-invocation: When the AI calls a tool (shows tool name + args)
 * - tool-result: The result returned from a tool call
 *
 * @param message - The UIMessage from useChat() hook
 * @returns An adapted message compatible with MessageItem rendering
 */
export function adaptUIMessage(message: UIMessage): AdaptedMessage {
  const createdAt = message.createdAt
    ? message.createdAt.getTime()
    : Date.now()

  // If no parts, return simple message with content
  if (!message.parts || message.parts.length === 0) {
    return {
      id: message.id,
      role: message.role,
      content: message.content,
      created_at: createdAt,
    }
  }

  // Extract text content from text parts
  const textParts = message.parts.filter(
    (part): part is Extract<UIMessagePart, { type: 'text' }> =>
      part.type === 'text'
  )
  const textContent = textParts.map((part) => part.text).join('')

  // Extract tool invocations and results
  const toolInvocations = message.parts.filter(
    (part): part is Extract<UIMessagePart, { type: 'tool-invocation' }> =>
      part.type === 'tool-invocation'
  )

  const toolResults = message.parts.filter(
    (part): part is Extract<UIMessagePart, { type: 'tool-result' }> =>
      part.type === 'tool-result'
  )

  // Build ToolCall array from invocations and results
  const toolCalls: ToolCall[] = toolInvocations.map((invocation) => {
    // Find matching result for this tool call
    const result = toolResults.find(
      (r) => r.toolCallId === invocation.toolCallId
    )

    // Determine if there was an error
    const hasError =
      result?.result &&
      typeof result.result === 'object' &&
      'error' in result.result

    return {
      role: 'assistant',
      content: result ? JSON.stringify(result.result, null, 2) : null,
      tool_call_id: invocation.toolCallId,
      tool_name: invocation.toolName,
      tool_args: invocation.args as Record<string, string>,
      tool_call_error: hasError,
      metrics: {
        time: 0, // MCP doesn't provide timing info by default
      },
      created_at: createdAt,
    }
  })

  return {
    id: message.id,
    role: message.role,
    content: textContent || message.content,
    tool_calls: toolCalls.length > 0 ? toolCalls : undefined,
    created_at: createdAt,
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
