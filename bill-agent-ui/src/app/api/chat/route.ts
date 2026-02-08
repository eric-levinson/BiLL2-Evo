import { NextResponse } from 'next/server'
import { createServerSupabaseClient } from '@/lib/supabase/server'
import { createMCPClient, type MCPClient } from '@ai-sdk/mcp'
import {
  ToolLoopAgent,
  stepCountIs,
  createAgentUIStreamResponse,
  consumeStream,
  type UIMessage,
  tool
} from 'ai'
import { z } from 'zod'
import { detectProvider } from '@/lib/ai/providerDetection'
import { createModelInstance } from '@/lib/ai/modelFactory'
import { registerToolSearch } from '@/lib/ai/anthropicToolSearch'
import { buildBM25Index } from '@/lib/ai/bm25Index'
import { createPrepareStepCallback } from '@/lib/ai/toolFiltering'
import { type AITool } from '@/lib/ai/toolMetadata'
import {
  retryWithBackoff,
  isRetryableError,
  RetryExhaustedError
} from '@/lib/ai/toolRetry'
import {
  CircuitBreaker,
  CircuitBreakerOpenError
} from '@/lib/ai/circuitBreaker'

/**
 * Estimates token count for a tool definition
 * Rough heuristic: ~1.3 tokens per character (includes name, description, parameters)
 * @param toolName - Name of the tool
 * @param toolDef - Tool definition object with description and parameters
 * @returns Estimated token count
 */
function estimateToolTokens(toolName: string, toolDef: unknown): number {
  // Serialize the tool definition to JSON to estimate size
  const toolJson = JSON.stringify({
    name: toolName,
    ...(toolDef as Record<string, unknown>)
  })
  // Rough estimate: ~1.3 tokens per character (includes JSON structure overhead)
  return Math.ceil(toolJson.length / 0.77)
}

/**
 * Calculates total estimated tokens for a set of tools
 * @param tools - Record of tools or array of tool names with definitions
 * @returns Total estimated token count
 */
function calculateTotalTokens(
  tools: Record<string, unknown> | unknown[]
): number {
  if (Array.isArray(tools)) {
    return tools.reduce((total: number, tool) => {
      // For BM25 search results, estimate based on the tool object
      return total + estimateToolTokens('tool', tool)
    }, 0)
  }

  // For tools Record from MCP
  return Object.entries(tools).reduce((total: number, [name, def]) => {
    return total + estimateToolTokens(name, def)
  }, 0)
}

// Helper to extract text content from UIMessage v3 parts
function getMessageText(message: UIMessage | undefined): string {
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
function filterBM25ToolCalls(messages: UIMessage[]): UIMessage[] {
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

/**
 * Fetches user preferences from the database
 * Returns default empty preferences if user has not set any yet
 * @param userId - The user's ID
 * @returns User preferences object
 */
async function getUserPreferences(userId: string) {
  const supabase = await createServerSupabaseClient()

  const { data, error } = await supabase
    .from('user_preferences')
    .select('*')
    .eq('user_id', userId)
    .single()

  if (error || !data) {
    // Return empty preferences if not found
    return {
      connected_leagues: [],
      favorite_players: [],
      analysis_style: 'balanced',
      preference_tags: [],
      custom_preferences: {}
    }
  }

  return data
}

/**
 * Formats user preferences into a markdown string for system prompt injection
 * @param preferences - User preferences object
 * @returns Formatted markdown string
 */
function formatPreferencesForPrompt(preferences: unknown): string {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const prefs = preferences as any

  // Check if user has ANY preferences set (not just connected leagues)
  const hasPreferences =
    prefs &&
    (prefs.connected_leagues?.length > 0 ||
      prefs.favorite_players?.length > 0 ||
      (prefs.analysis_style && prefs.analysis_style !== 'balanced') ||
      prefs.preference_tags?.length > 0)

  if (!hasPreferences) {
    return 'No user preferences stored yet.'
  }

  let context = '## User Context\n\n'

  // Connected Leagues
  if (prefs.connected_leagues?.length > 0) {
    context += '**Connected Sleeper Leagues:**\n'
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    prefs.connected_leagues.forEach((league: any) => {
      context += `- ${league.name} (${league.season}, ${league.scoring_format})${league.is_primary ? ' [PRIMARY]' : ''}\n`
    })
    context += '\n'
  }

  // Favorite Players
  if (prefs.favorite_players?.length > 0) {
    context += `**Favorite Players:** ${prefs.favorite_players.join(', ')}\n\n`
  }

  // Analysis Style
  if (prefs.analysis_style) {
    context += `**Preferred Analysis Style:** ${prefs.analysis_style}\n\n`
  }

  // Tags
  if (prefs.preference_tags?.length > 0) {
    context += `**User Focus Areas:** ${prefs.preference_tags.join(', ')}\n\n`
  }

  // Roster Notes (if primary league set)
  if (prefs.primary_league_id && prefs.roster_notes?.[prefs.primary_league_id]) {
    const notes = prefs.roster_notes[prefs.primary_league_id]
    context += '**Primary Team Context:**\n'
    if (notes.team_name) context += `- Team: ${notes.team_name}\n`
    if (notes.key_players?.length)
      context += `- Key Players: ${notes.key_players.join(', ')}\n`
    if (notes.strengths?.length)
      context += `- Strengths: ${notes.strengths.join(', ')}\n`
    if (notes.needs?.length) context += `- Needs: ${notes.needs.join(', ')}\n`
  }

  return context
}

/**
 * Creates the update_user_preference custom tool for the AI agent
 * Allows the agent to update user preferences when explicitly asked by the user
 * @param userId - The authenticated user's ID
 * @returns Tool definition for updating user preferences
 */
function createUpdateUserPreferenceTool(userId: string) {
  return tool({
    description:
      "Update a user's preference. Use this when the user asks you to remember something about their analysis style, favorite players, or general preferences. REQUIRED: You must provide preference_type (one of: analysis_style, favorite_players, preference_tag, custom), value (string), and action (one of: set, add, remove).",
    parameters: z.object({
      preference_type: z
        .string()
        .describe('Type of preference: analysis_style, favorite_players, preference_tag, or custom'),
      value: z
        .string()
        .describe('The preference value to set'),
      action: z
        .string()
        .describe('Action: set, add, or remove. Default is set')
    }),
    execute: async (args) => {
      console.log('[update_user_preference] RAW ARGS:', JSON.stringify(args, null, 2))

      // Handle different AI providers sending different parameter names
      const argsObj = args as any
      let preference_type = argsObj.preference_type || argsObj.field || argsObj.type
      let value = argsObj.value
      let action = argsObj.action || 'set'
      let key = argsObj.key

      // Convert Gemini-style field names to our schema
      if (argsObj.field === 'preferred_analysis_style' || argsObj.field === 'analysis_style') {
        preference_type = 'analysis_style'
      }

      console.log('[update_user_preference] Normalized params:', { preference_type, key, value, action })
      const supabase = await createServerSupabaseClient()

      // Ensure user preferences record exists
      let { data: existing } = await supabase
        .from('user_preferences')
        .select('*')
        .eq('user_id', userId)
        .single()

      if (!existing) {
        // Insert new record and refetch it
        const { error: insertError } = await supabase
          .from('user_preferences')
          .insert({ user_id: userId })

        if (insertError) {
          console.error('[update_user_preference] Insert error:', insertError)
          return { success: false, error: insertError.message }
        }

        // Refetch the newly created record
        const { data: refetched } = await supabase
          .from('user_preferences')
          .select('*')
          .eq('user_id', userId)
          .single()

        existing = refetched
      }

      // Build update object based on preference_type
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      let update: any = {}

      switch (preference_type) {
        case 'analysis_style':
          update.analysis_style = value
          break

        case 'favorite_players':
          if (action === 'add') {
            update.favorite_players = [
              ...(existing?.favorite_players || []),
              ...(Array.isArray(value) ? value : [value])
            ]
          } else if (action === 'remove') {
            update.favorite_players = (
              existing?.favorite_players || []
            ).filter((p: string) => {
              const valuesToRemove = Array.isArray(value) ? value : [value]
              return !valuesToRemove.includes(p)
            })
          } else {
            update.favorite_players = Array.isArray(value) ? value : [value]
          }
          break

        case 'preference_tag':
          if (action === 'add') {
            update.preference_tags = [
              ...(existing?.preference_tags || []),
              ...(Array.isArray(value) ? value : [value])
            ]
          } else if (action === 'remove') {
            update.preference_tags = (existing?.preference_tags || []).filter(
              (t: string) => {
                const valuesToRemove = Array.isArray(value) ? value : [value]
                return !valuesToRemove.includes(t)
              }
            )
          } else {
            update.preference_tags = Array.isArray(value) ? value : [value]
          }
          break

        case 'custom':
          if (!key) {
            return {
              success: false,
              error: 'key parameter is required for custom preference type'
            }
          }
          const customPrefs = existing?.custom_preferences || {}
          customPrefs[key] = value
          update.custom_preferences = customPrefs
          break
      }

      console.log('[update_user_preference] Updating with:', update)

      const { error } = await supabase
        .from('user_preferences')
        .update(update)
        .eq('user_id', userId)

      if (error) {
        console.error('[update_user_preference] Update error:', error)
        return { success: false, error: error.message }
      }

      console.log('[update_user_preference] Success! Updated:', update)
      return { success: true, updated: update }
    }
  })
}

/**
 * Creates the add_connected_league custom tool for the AI agent
 * Allows the agent to save a Sleeper league to the user's connected leagues
 * @param userId - The authenticated user's ID
 * @returns Tool definition for adding a connected league
 */
function createAddConnectedLeagueTool(userId: string) {
  return tool({
    description:
      "Add a Sleeper league to the user's connected leagues. Use this when the user shares their league ID or you fetch their leagues via Sleeper tools.",
    parameters: z.object({
      league_id: z.string().describe('The Sleeper league ID'),
      league_name: z.string().describe('The name of the league'),
      scoring_format: z
        .string()
        .describe("e.g., 'PPR', 'Half-PPR', 'Standard', 'Superflex'"),
      season: z.number().describe('The season year (e.g., 2025)'),
      set_as_primary: z
        .boolean()
        .default(false)
        .describe("Whether this should be the user's primary league")
    }),
    execute: async ({
      league_id,
      league_name,
      scoring_format,
      season,
      set_as_primary
    }) => {
      const supabase = await createServerSupabaseClient()

      // Get existing preferences
      const { data: existing } = await supabase
        .from('user_preferences')
        .select('*')
        .eq('user_id', userId)
        .single()

      const connectedLeagues = existing?.connected_leagues || []

      // Check if league already exists
      const existingIndex = connectedLeagues.findIndex(
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        (l: any) => l.league_id === league_id
      )

      const newLeague = {
        league_id,
        name: league_name,
        scoring_format,
        season,
        is_primary: set_as_primary
      }

      if (existingIndex >= 0) {
        // Update existing league
        connectedLeagues[existingIndex] = newLeague
      } else {
        // Add new league
        connectedLeagues.push(newLeague)
      }

      // If setting as primary, unset is_primary on other leagues
      if (set_as_primary) {
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        connectedLeagues.forEach((l: any) => {
          if (l.league_id !== league_id) {
            l.is_primary = false
          }
        })
      }

      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const update: any = { connected_leagues: connectedLeagues }

      if (set_as_primary) {
        update.primary_league_id = league_id
      }

      // Upsert preferences (insert if not exists, update if exists)
      if (!existing) {
        const { error } = await supabase
          .from('user_preferences')
          .insert({ user_id: userId, ...update })

        if (error) {
          return { success: false, error: error.message }
        }
      } else {
        const { error } = await supabase
          .from('user_preferences')
          .update(update)
          .eq('user_id', userId)

        if (error) {
          return { success: false, error: error.message }
        }
      }

      return { success: true, league_added: newLeague }
    }
  })
}

/**
 * Creates the update_roster_notes custom tool for the AI agent
 * Allows the agent to remember the user's team composition, strengths, and needs per league
 * @param userId - The authenticated user's ID
 * @returns Tool definition for updating roster notes
 */
function createUpdateRosterNotesTool(userId: string) {
  return tool({
    description:
      "Update roster notes for a specific league. Use this to remember the user's team composition, strengths, and needs.",
    parameters: z.object({
      league_id: z.string().describe('The Sleeper league ID'),
      team_name: z.string().optional().describe('The name of the user\'s team'),
      key_players: z
        .array(z.string())
        .optional()
        .describe('Array of key players on the user\'s roster'),
      strengths: z
        .array(z.string())
        .optional()
        .describe('Array of team strengths (e.g., "RB depth", "Elite WR1")'),
      needs: z
        .array(z.string())
        .optional()
        .describe('Array of team needs (e.g., "WR2", "TE upgrade")')
    }),
    execute: async ({ league_id, team_name, key_players, strengths, needs }) => {
      const supabase = await createServerSupabaseClient()

      // Get existing preferences
      const { data: existing } = await supabase
        .from('user_preferences')
        .select('*')
        .eq('user_id', userId)
        .single()

      // Get or initialize roster_notes JSONB field
      const rosterNotes = existing?.roster_notes || {}

      // Update notes for this league (merge with existing if present)
      rosterNotes[league_id] = {
        ...rosterNotes[league_id],
        ...(team_name !== undefined && { team_name }),
        ...(key_players !== undefined && { key_players }),
        ...(strengths !== undefined && { strengths }),
        ...(needs !== undefined && { needs })
      }

      // Upsert preferences (insert if not exists, update if exists)
      if (!existing) {
        const { error } = await supabase
          .from('user_preferences')
          .insert({ user_id: userId, roster_notes: rosterNotes })

        if (error) {
          return { success: false, error: error.message }
        }
      } else {
        const { error } = await supabase
          .from('user_preferences')
          .update({ roster_notes: rosterNotes })
          .eq('user_id', userId)

        if (error) {
          return { success: false, error: error.message }
        }
      }

      return { success: true, updated_notes: rosterNotes[league_id] }
    }
  })
}

/**
 * Global circuit breaker instance for MCP server protection
 * Tracks consecutive failures and opens circuit after threshold is reached
 */
const mcpCircuitBreaker = new CircuitBreaker({
  onStateChange: (serviceName, oldState, newState) => {
    console.log(
      `[Circuit Breaker] ${serviceName} state changed: ${oldState} -> ${newState}`
    )
  }
})

export async function POST(req: Request) {
  // Verify authentication
  const supabase = await createServerSupabaseClient()
  const { data } = await supabase.auth.getUser()
  const user = data?.user ?? null

  if (!user) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
  }

  let mcpClient: MCPClient | undefined

  try {
    // Parse request body
    const body = await req.json()
    // `id` is auto-generated by useChat SDK - we use a separate `sessionId` for DB persistence
    const { messages, sessionId } = body

    if (!messages || !Array.isArray(messages)) {
      return NextResponse.json(
        { error: 'Messages array is required' },
        { status: 400 }
      )
    }

    // Create MCP client with streamable HTTP transport
    const mcpServerUrl =
      process.env.MCP_SERVER_URL || 'http://localhost:8000/mcp/'

    // Wrap MCP client creation with retry logic and circuit breaker
    mcpClient = await mcpCircuitBreaker.execute('mcp-server', async () => {
      return await retryWithBackoff(
        async () => {
          console.log(`[MCP Client] Connecting to ${mcpServerUrl}`)
          return await createMCPClient({
            transport: {
              type: 'http',
              url: mcpServerUrl
            }
          })
        },
        {
          shouldRetry: isRetryableError,
          onRetry: (error, attempt, delayMs) => {
            const errorType =
              error instanceof Error ? error.constructor.name : 'Unknown'
            const errorMsg =
              error instanceof Error ? error.message : String(error)
            console.error(`[Error Recovery] MCP Client connection failed`, {
              service: 'mcp-server',
              operation: 'createMCPClient',
              attempt,
              delayMs,
              errorType,
              errorMessage: errorMsg
            })
          }
        }
      )
    })

    // Get all available tools from MCP server with retry logic and circuit breaker
    const tools = await mcpCircuitBreaker.execute('mcp-server', async () => {
      return await retryWithBackoff(
        async () => {
          console.log('[MCP Tools] Fetching available tools from server')
          return await mcpClient!.tools()
        },
        {
          shouldRetry: isRetryableError,
          onRetry: (error, attempt, delayMs) => {
            const errorType =
              error instanceof Error ? error.constructor.name : 'Unknown'
            const errorMsg =
              error instanceof Error ? error.message : String(error)
            console.error(`[Error Recovery] MCP Tools fetch failed`, {
              service: 'mcp-server',
              operation: 'mcpClient.tools()',
              attempt,
              delayMs,
              errorType,
              errorMessage: errorMsg
            })
          }
        }
      )
    })

    // Detect provider from model ID
    const modelId = process.env.AI_MODEL_ID || 'claude-sonnet-4-5-20250929'
    const provider = detectProvider(modelId)

    // Get max results for tool filtering from env var
    const maxResults = parseInt(process.env.TOOL_SEARCH_MAX_RESULTS || '7', 10)

    // Calculate baseline token count (all tools)
    const totalToolCount = Object.keys(tools).length
    const baselineTokens = calculateTotalTokens(tools)

    console.log(`[Tool Filtering] Provider: ${provider}, Model: ${modelId}`)
    console.log(`[Tool Filtering] Total tools available: ${totalToolCount}`)
    console.log(
      `[Tool Filtering] Estimated baseline tokens (all tools): ${baselineTokens.toLocaleString()}`
    )

    // Convert tools Record to array for BM25 indexing, injecting name from Record keys
    const toolsArray = Object.entries(tools).map(([name, tool]) => ({
      ...(tool as Record<string, unknown>),
      name
    })) as AITool[]

    // Build BM25 index for client-side tool filtering (used by non-Anthropic providers)
    const bm25Index = buildBM25Index(toolsArray)

    // Apply Tool Search optimization for Anthropic models
    // For Claude, this marks all MCP tools with deferLoading: true
    // and adds the Tool Search meta-tool for on-demand discovery
    const optimizedTools =
      provider === 'anthropic' ? registerToolSearch(tools) : tools

    // Log path-specific optimization strategy
    if (provider === 'anthropic') {
      // Anthropic Tool Search: Server-side on-demand tool loading
      // Estimated tokens: ~500 for Tool Search meta-tool + selected tools loaded on-demand
      const estimatedFilteredTokens =
        500 + maxResults * (baselineTokens / totalToolCount)
      const tokenSavings = baselineTokens - estimatedFilteredTokens
      const savingsPercentage = ((tokenSavings / baselineTokens) * 100).toFixed(
        1
      )

      console.log(
        `[Tool Filtering] Strategy: Anthropic Tool Search (server-side)`
      )
      console.log(
        `[Tool Filtering] Estimated filtered tokens: ${estimatedFilteredTokens.toLocaleString()} (Tool Search meta-tool + ~${maxResults} tools on-demand)`
      )
      console.log(
        `[Tool Filtering] Estimated token savings: ${tokenSavings.toLocaleString()} tokens (${savingsPercentage}% reduction)`
      )
    } else {
      // Client-side BM25: Tools filtered before each LLM step via prepareStep
      const estimatedFilteredTokens =
        maxResults * (baselineTokens / totalToolCount)
      const tokenSavings = baselineTokens - estimatedFilteredTokens
      const savingsPercentage = ((tokenSavings / baselineTokens) * 100).toFixed(
        1
      )

      console.log(
        `[Tool Filtering] Strategy: Client-side BM25 filtering via prepareStep`
      )
      console.log(
        `[Tool Filtering] Estimated filtered tokens: ${estimatedFilteredTokens.toLocaleString()} (~${maxResults} tools per request)`
      )
      console.log(
        `[Tool Filtering] Estimated token savings: ${tokenSavings.toLocaleString()} tokens (${savingsPercentage}% reduction)`
      )
    }

    // Create prepareStep callback for BM25 filtering (non-Anthropic providers)
    // For Anthropic providers, Tool Search handles this server-side, so no prepareStep needed
    // Wrap the callback to add logging
    const basePrepareStep =
      provider !== 'anthropic'
        ? createPrepareStepCallback(bm25Index, toolsArray, maxResults)
        : undefined

    const prepareStep = basePrepareStep
      ? (context: Parameters<typeof basePrepareStep>[0]) => {
          const result = basePrepareStep(context)

          // ALWAYS include preference tools in addition to BM25 selection
          const preferenceToolNames = ['update_user_preference', 'add_connected_league', 'update_roster_notes']
          const selectedTools = result?.activeTools || []
          const toolsWithPreferences = [...new Set([...selectedTools, ...preferenceToolNames])]

          // Log selected tools for this step
          if (result?.activeTools && result.activeTools.length > 0) {
            console.log(
              `[Tool Selection] BM25 selected ${result.activeTools.length} tools + ${preferenceToolNames.length} preference tools: ${toolsWithPreferences.join(', ')}`
            )
          } else {
            console.log(
              `[Tool Selection] BM25 fallback: using all ${totalToolCount} tools + ${preferenceToolNames.length} preference tools`
            )
          }

          return {
            ...result,
            activeTools: toolsWithPreferences
          }
        }
      : undefined

    // Fetch user preferences for cross-session memory
    const userPreferences = await getUserPreferences(user.id)
    const userContextSection = formatPreferencesForPrompt(userPreferences)

    // Create preference management tools
    const preferenceTools = {
      update_user_preference: createUpdateUserPreferenceTool(user.id),
      add_connected_league: createAddConnectedLeagueTool(user.id),
      update_roster_notes: createUpdateRosterNotesTool(user.id)
    }

    // Merge preference tools with MCP tools
    const allTools = {
      ...optimizedTools,
      ...preferenceTools
    }

    // Create ToolLoopAgent with detected provider model
    const agent = new ToolLoopAgent({
      model: createModelInstance(modelId),
      tools: allTools,
      stopWhen: stepCountIs(10),
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      prepareStep: prepareStep as any,
      instructions: `You are BiLL, an advanced fantasy football analyst powered by AI.

Today's date: ${new Date().toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' })}
The 2025 NFL season is COMPLETE. The database contains data through the 2025 season.
The most recent completed NFL season is 2025. The 2026 NFL season has not started yet.

${userContextSection}

Your capabilities:
- Access to comprehensive NFL player stats (season & weekly advanced metrics)
- Real-time Sleeper league data (rosters, matchups, transactions, trending players)
- Dynasty and redraft rankings
- Game-level offensive and defensive statistics
- Player information and metrics metadata
- User preference management (store and retrieve user context across sessions)

Guidelines for tool usage:
1. NEVER assume data doesn't exist — always query the tools first. Your training data may be outdated.
2. For player lookups, start with get_player_info_tool to get accurate player IDs and current team info
3. When analyzing stats, use the advanced stats tools (receiving/passing/rushing/defense) for deeper insights
4. For league-specific questions, use Sleeper API tools to get current roster and matchup data
5. When discussing rankings, fetch the latest dynasty or redraft rankings via get_fantasy_ranks
6. Provide data-driven insights and back up your recommendations with specific metrics
7. If you need clarification on available metrics, use get_metrics_metadata
8. If seasonal aggregate data isn't available, check the weekly stats tools — they may have more recent data
9. Do NOT make more than 4 tool calls for a single question. If data isn't found after a few attempts, tell the user what's available instead of endlessly retrying.
10. When users ask you to remember something (league, preferences, favorite players, roster notes), use the update_user_preference, add_connected_league, or update_roster_notes tools to persist that information.

Remember:
- Be conversational but analytical
- Cite specific stats when making recommendations
- Consider both current performance and historical trends
- For dynasty leagues, factor in player age and long-term value
- Always verify player names and team affiliations before making claims
- Use the user context above to personalize your responses without asking the user to re-state their preferences`
    })

    // Use createAgentUIStreamResponse which properly handles the agent stream
    return createAgentUIStreamResponse({
      agent,
      uiMessages: messages,
      // CRITICAL: Consume stream to ensure completion even on client disconnect
      // This prevents data loss when client closes browser or network disconnects
      consumeSseStream: consumeStream,
      // SERVER-SIDE persistence - fires even when client disconnects
      onFinish: async ({ messages: completedMessages }) => {
        try {
          // Filter out BM25 tool calls before persisting to avoid replay validation errors
          const filteredMessages = filterBM25ToolCalls(completedMessages)

          if (!sessionId) {
            // Create new session with title from first user message
            const firstUserMessage = filteredMessages.find(
              (m: UIMessage) => m.role === 'user'
            )
            const content = getMessageText(firstUserMessage)

            // Truncate title to 50 chars max (47 chars + '...')
            const title =
              content.length > 50 ? content.substring(0, 47) + '...' : content

            // Insert new session into database
            const { data: newSession, error: insertError } = await supabase
              .from('chat_sessions')
              .insert({
                user_id: user.id,
                title,
                messages: filteredMessages
              })
              .select('id')
              .single()

            if (insertError) {
              console.error('Server-side session creation failed:', insertError)
            } else {
              console.log(
                'Server-side persistence: Created new session:',
                newSession?.id,
                'with title:',
                title
              )
            }
          } else {
            // Update existing session with new messages
            const { error: updateError } = await supabase
              .from('chat_sessions')
              .update({
                messages: filteredMessages
              })
              .eq('id', sessionId)

            if (updateError) {
              console.error('Server-side session update failed:', updateError)
            } else {
              console.log('Server-side persistence: Updated session', sessionId)
            }
          }
        } catch (err) {
          console.error('Server-side persistence error:', err)
        } finally {
          // Close MCP client AFTER stream completes — closing in the outer
          // finally block causes "request from a closed client" errors because
          // the finally runs before the stream's tool calls finish executing
          if (mcpClient) {
            await mcpClient.close()
          }
        }
      }
    })
  } catch (err) {
    console.error('Chat API error:', err)
    // Close MCP client on setup errors (stream never started)
    if (mcpClient) {
      await mcpClient.close()
    }

    // Provide user-friendly error messages based on error type
    if (err instanceof CircuitBreakerOpenError) {
      console.error(`[Circuit Breaker] Service unavailable - circuit open`, {
        serviceName: err.serviceName,
        resetAt: err.resetAt.toISOString(),
        message: err.message
      })
      return NextResponse.json(
        {
          error:
            'The fantasy football data service is temporarily unavailable. Please try again in a moment.'
        },
        { status: 503 }
      )
    }

    if (err instanceof RetryExhaustedError) {
      const lastError = err.lastError
      const lastErrorDetails =
        lastError instanceof Error
          ? {
              type: lastError.constructor.name,
              message: lastError.message,
              stack: lastError.stack
            }
          : { message: String(lastError) }

      console.error(`[Retry Exhausted] All retry attempts failed`, {
        attempts: err.attempts,
        lastError: lastErrorDetails
      })
      return NextResponse.json(
        {
          error:
            'Unable to connect to the fantasy football data service. Please ensure the MCP server is running and try again.'
        },
        { status: 503 }
      )
    }

    // Check for specific error types to provide context-aware messages
    const errorMessage = err instanceof Error ? err.message.toLowerCase() : ''
    const errorType = err instanceof Error ? err.constructor.name : ''

    // Network and connection errors
    if (
      errorMessage.includes('econnrefused') ||
      errorMessage.includes('econnreset') ||
      errorMessage.includes('network') ||
      errorMessage.includes('connection')
    ) {
      console.error(`[Network Error] Connection failed`, {
        type: errorType,
        message: err instanceof Error ? err.message : String(err)
      })
      return NextResponse.json(
        {
          error:
            'Unable to connect to the data service. Please check your network connection and ensure all required services are running.'
        },
        { status: 503 }
      )
    }

    // Timeout errors
    if (
      errorMessage.includes('timeout') ||
      errorMessage.includes('etimedout')
    ) {
      console.error(`[Timeout Error] Request timed out`, {
        type: errorType,
        message: err instanceof Error ? err.message : String(err)
      })
      return NextResponse.json(
        {
          error:
            'The request took too long to complete. The service may be experiencing high load. Please try again.'
        },
        { status: 504 }
      )
    }

    // Authentication errors
    if (
      errorMessage.includes('unauthorized') ||
      errorMessage.includes('authentication') ||
      errorMessage.includes('unauthenticated')
    ) {
      console.error(`[Auth Error] Authentication failed`, {
        type: errorType,
        message: err instanceof Error ? err.message : String(err)
      })
      return NextResponse.json(
        {
          error:
            'Authentication failed. Please log out and log back in to continue.'
        },
        { status: 401 }
      )
    }

    // Rate limit errors
    if (errorMessage.includes('rate limit') || errorMessage.includes('429')) {
      console.error(`[Rate Limit] Too many requests`, {
        type: errorType,
        message: err instanceof Error ? err.message : String(err)
      })
      return NextResponse.json(
        {
          error: 'Too many requests. Please wait a moment before trying again.'
        },
        { status: 429 }
      )
    }

    // Generic error fallback - log full details for debugging but show friendly message
    const errorDetails =
      err instanceof Error
        ? {
            type: err.constructor.name,
            message: err.message,
            stack: err.stack
          }
        : { message: String(err) }

    console.error(`[Chat API] Unhandled error occurred`, {
      error: errorDetails
    })

    return NextResponse.json(
      {
        error:
          'An unexpected error occurred while processing your request. Please try again or contact support if the problem persists.'
      },
      { status: 500 }
    )
  }
}
