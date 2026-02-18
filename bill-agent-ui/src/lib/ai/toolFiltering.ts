/**
 * Tool filtering via prepareStep callback
 * Creates a prepareStep callback that uses BM25 to filter tools before each LLM step
 */

import { type BM25Index, searchBM25Index, getToolNames } from './bm25Index'
import { type AITool } from './toolMetadata'

/**
 * Tools that should always be available in every request, regardless of BM25 score.
 * These are fundamental tools needed for most queries.
 * Sleeper league tools are included because league context (rosters, matchups,
 * transactions) is needed in multi-step tool loops even when the user's original
 * query doesn't mention them explicitly.
 */
const ALWAYS_ON_TOOLS = [
  'get_player_info_tool', // Player lookup is fundamental to most fantasy football queries
  'get_sleeper_leagues_by_username', // League discovery from username
  'get_sleeper_league_rosters', // Roster data for trade/roster analysis
  'get_sleeper_league_matchups', // Matchup data for start/sit analysis
  'get_sleeper_league_users' // League member context
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
 * Extracts text content from a single message
 * Handles both string content and parts-based content (UIMessage v3)
 */
function extractMessageText(message: {
  role: string
  content:
    | string
    | Array<{ type: string; text?: string; [key: string]: unknown }>
  [key: string]: unknown
}): string {
  if (typeof message.content === 'string') {
    return message.content
  }

  if (Array.isArray(message.content)) {
    const textParts = message.content
      .filter(
        (p): p is { type: 'text'; text: string } =>
          p.type === 'text' && typeof p.text === 'string'
      )
      .map((p) => p.text)
    return textParts.join(' ')
  }

  return ''
}

/**
 * Builds a BM25 search query from the conversation context.
 * Combines the latest user message with the last assistant message (if any)
 * so that multi-step tool loops can discover tools based on the model's
 * intermediate reasoning, not just the user's original query.
 * @param context - The step context from ToolLoopAgent
 * @returns Combined query string for BM25 search
 */
function buildStepQuery(context: StepContext): string {
  const parts: string[] = []

  // Always include the latest user message
  const userMessages = context.messages.filter((m) => m.role === 'user')
  const lastUserMessage = userMessages[userMessages.length - 1]
  if (lastUserMessage) {
    parts.push(extractMessageText(lastUserMessage))
  }

  // Include the last assistant message text for multi-step context.
  // In tool loops, the assistant's intermediate response often mentions
  // tools or concepts (e.g., "rosters", "matchups") that the user's
  // original query didn't include.
  const assistantMessages = context.messages.filter(
    (m) => m.role === 'assistant'
  )
  const lastAssistantMessage = assistantMessages[assistantMessages.length - 1]
  if (lastAssistantMessage) {
    const assistantText = extractMessageText(lastAssistantMessage)
    // Limit assistant text to avoid BM25 noise from very long responses
    if (assistantText) {
      parts.push(assistantText.slice(0, 300))
    }
  }

  return parts.join(' ')
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
    // Build query from user message + assistant context for multi-step loops
    const query = buildStepQuery(context)

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
