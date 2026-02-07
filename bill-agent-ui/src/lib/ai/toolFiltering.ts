/**
 * Tool filtering via prepareStep callback
 * Creates a prepareStep callback that uses BM25 to filter tools before each LLM step
 */

import { type BM25Index, searchBM25Index, getToolNames } from './bm25Index'
import { type AITool } from './toolMetadata'

/**
 * Tools that should always be available in every request, regardless of BM25 score.
 * These are fundamental tools needed for most queries.
 */
const ALWAYS_ON_TOOLS = [
  'get_player_info_tool' // Player lookup is fundamental to most fantasy football queries
]

/**
 * Step context from AI SDK ToolLoopAgent
 * Contains messages and other step information
 */
interface StepContext {
  messages: Array<{
    role: string
    content:
      | string
      | Array<{ type: string; text?: string; [key: string]: unknown }>
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
  const userMessages = context.messages.filter(
    (m: { role: string }) => m.role === 'user'
  )
  const lastUserMessage = userMessages[userMessages.length - 1]

  if (!lastUserMessage) return ''

  // Handle string content (legacy format)
  if (typeof lastUserMessage.content === 'string') {
    return lastUserMessage.content
  }

  // Handle parts-based content (UIMessage v3)
  if (Array.isArray(lastUserMessage.content)) {
    const textPart = lastUserMessage.content.find(
      (p: {
        type: string
        text?: string
        [key: string]: unknown
      }): p is { type: 'text'; text: string } =>
        p.type === 'text' && typeof p.text === 'string'
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

    // If no query, return only always-on tools
    if (!query || query.trim().length === 0) {
      return {
        activeTools: [...ALWAYS_ON_TOOLS]
      }
    }

    // Search the BM25 index for relevant tools
    const searchResults = searchBM25Index(bm25Index, query, maxResults)

    // Extract tool names for activeTools
    const activeToolNames = getToolNames(searchResults)

    // Merge always-on tools with BM25 results, removing duplicates
    const mergedTools = Array.from(
      new Set([...ALWAYS_ON_TOOLS, ...activeToolNames])
    )

    // If BM25 returned no results, we still have always-on tools
    // Return the merged list (always-on tools + BM25 results)
    return {
      activeTools: mergedTools
    }
  }
}
