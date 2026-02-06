/**
 * Tool filtering via prepareStep callback
 * Creates a prepareStep callback that uses BM25 to filter tools before each LLM step
 */

import { type BM25Index, searchBM25Index, getToolNames } from './bm25Index'
import { type AITool } from './toolMetadata'

/**
 * Step context from AI SDK ToolLoopAgent
 * Contains messages and other step information
 */
interface StepContext {
  messages: Array<{
    role: string
    content: string | Array<{ type: string; text?: string; [key: string]: unknown }>
    [key: string]: unknown
  }>
  [key: string]: unknown
}

/**
 * Result from prepareStep callback
 * Used to dynamically filter active tools before the LLM step
 */
interface PrepareStepResult {
  /** Array of tool names to make available for this step */
  activeTools?: string[]
}

/**
 * Extracts the latest user message text from step context
 * Handles both string content and parts-based content (UIMessage v3)
 * @param context - The step context from ToolLoopAgent
 * @returns The latest user message text, or empty string if not found
 */
function getLatestUserQuery(context: StepContext): string {
  // Find the last user message
  const userMessages = context.messages.filter(m => m.role === 'user')
  const lastUserMessage = userMessages[userMessages.length - 1]

  if (!lastUserMessage) return ''

  // Handle string content (legacy format)
  if (typeof lastUserMessage.content === 'string') {
    return lastUserMessage.content
  }

  // Handle parts-based content (UIMessage v3)
  if (Array.isArray(lastUserMessage.content)) {
    const textPart = lastUserMessage.content.find(
      (p): p is { type: 'text'; text: string } => p.type === 'text' && typeof p.text === 'string'
    )
    return textPart?.text || ''
  }

  return ''
}

/**
 * Creates a prepareStep callback for tool filtering via BM25
 * @param bm25Index - The BM25 index built from all tools
 * @param allTools - Array of all available AI tools
 * @param maxResults - Maximum number of tools to return (default: 7)
 * @returns A prepareStep callback function for ToolLoopAgent
 */
export function createPrepareStepCallback(
  bm25Index: BM25Index,
  allTools: AITool[],
  maxResults: number = 7
): (context: StepContext) => PrepareStepResult {
  return (context: StepContext): PrepareStepResult => {
    // Extract the latest user query
    const query = getLatestUserQuery(context)

    // If no query, return all tools (fallback)
    if (!query || query.trim().length === 0) {
      return {}
    }

    // Search the BM25 index for relevant tools
    const searchResults = searchBM25Index(bm25Index, query, maxResults)

    // Extract tool names for activeTools
    const activeToolNames = getToolNames(searchResults)

    // If no results, return all tools (fallback)
    if (activeToolNames.length === 0) {
      return {}
    }

    // Return the filtered activeTools list
    return {
      activeTools: activeToolNames
    }
  }
}
