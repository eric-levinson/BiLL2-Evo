import { NextResponse } from 'next/server'
import { createServerSupabaseClient } from '@/lib/supabase/server'
import { type MCPClient } from '@ai-sdk/mcp'
import {
  ToolLoopAgent,
  stepCountIs,
  createAgentUIStreamResponse,
  consumeStream,
  type UIMessage
} from 'ai'
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
import { MCPConnectionPool } from '@/lib/ai/mcpConnectionPool'
import { calculateTotalTokens } from '@/lib/ai/tokenEstimation'
import {
  getMessageText,
  filterBM25ToolCalls
} from '@/lib/utils/messageFiltering'
import { deduplicateToolCalls } from '@/lib/utils/deduplicateMessages'
import {
  getUserPreferences,
  formatPreferencesForPrompt
} from '@/lib/supabase/server/preferences'
import {
  createUpdateUserPreferenceTool,
  createAddConnectedLeagueTool,
  createUpdateRosterNotesTool,
  createUpdateSleeperConnectionTool
} from '@/lib/ai/tools/preferences'
import { getBillSystemPrompt } from '@/lib/ai/prompts/billSystemPrompt'
import { z } from 'zod'

/**
 * Request body schema — validates data shape at the API boundary.
 * Non-UUID session IDs (short random IDs from AI SDK) are silently dropped.
 */
const ChatRequestSchema = z.object({
  messages: z.array(z.any()).min(1, 'At least one message is required'),
  id: z
    .string()
    .regex(/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i)
    .optional()
    .catch(undefined)
})

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

/**
 * Global MCP connection pool instance
 * Maintains persistent connections to reduce per-request latency (50-100ms -> <10ms)
 */
const mcpConnectionPool = new MCPConnectionPool({
  serverUrl: process.env.MCP_SERVER_URL || 'http://localhost:8000/mcp/',
  circuitBreaker: mcpCircuitBreaker,
  onConnectionCreated: (connectionId) => {
    console.log(`[MCP Pool] New connection created: ${connectionId}`)
  },
  onConnectionClosed: (connectionId, reason) => {
    console.log(`[MCP Pool] Connection closed: ${connectionId} - ${reason}`)
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
  let streamCreated = false

  try {
    // Parse and validate request body at the API boundary
    const body = await req.json()
    const parsed = ChatRequestSchema.safeParse(body)

    if (!parsed.success) {
      return NextResponse.json(
        { error: 'Invalid request: ' + parsed.error.issues[0]?.message },
        { status: 400 }
      )
    }

    const { messages } = parsed.data
    // Non-UUID session IDs are silently dropped by the schema's .catch(undefined)
    const sessionId = parsed.data.id

    // Acquire MCP client from connection pool
    // Pool handles connection reuse, circuit breaker, and retry logic
    const poolAcquireStart = performance.now()
    mcpClient = await mcpConnectionPool.acquire()
    const poolAcquireEnd = performance.now()
    const poolAcquisitionTime = (poolAcquireEnd - poolAcquireStart).toFixed(2)
    console.log(
      `[Chat API] MCP client acquisition took ${poolAcquisitionTime}ms`
    )

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
          const preferenceToolNames = [
            'update_user_preference',
            'add_connected_league',
            'update_roster_notes',
            'update_sleeper_connection'
          ]
          const selectedTools = result?.activeTools || []
          const toolsWithPreferences = [
            ...new Set([...selectedTools, ...preferenceToolNames])
          ]

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
      update_roster_notes: createUpdateRosterNotesTool(user.id),
      update_sleeper_connection: createUpdateSleeperConnectionTool(user.id)
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
      instructions: getBillSystemPrompt(userContextSection)
    })

    // Mark stream as successfully created (before return)
    // This prevents the outer finally block from releasing the connection
    // since onFinish will handle it
    streamCreated = true

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
          // Filter out BM25 tool calls and deduplicate tool call IDs before persisting
          const bm25Filtered = filterBM25ToolCalls(completedMessages)
          const filteredMessages = deduplicateToolCalls(bm25Filtered)

          // Check if session exists in database (for auto-generated client IDs)
          let sessionExists = false
          if (sessionId) {
            const { data: existingSession } = await supabase
              .from('chat_sessions')
              .select('id')
              .eq('id', sessionId)
              .single()
            sessionExists = !!existingSession
          }

          if (!sessionId || !sessionExists) {
            // Create new session with title from first user message
            const firstUserMessage = filteredMessages.find(
              (m: UIMessage) => m.role === 'user'
            )
            const content = getMessageText(firstUserMessage)

            // Truncate title to 50 chars max (47 chars + '...')
            const title =
              content.length > 50 ? content.substring(0, 47) + '...' : content

            // Insert new session into database with provided or generated ID
            const { data: newSession, error: insertError } = await supabase
              .from('chat_sessions')
              .insert({
                id: sessionId, // Use client-provided ID if available
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
          // Release MCP client back to pool AFTER stream completes
          // Releasing in the outer finally block causes "request from a closed client"
          // errors because the finally runs before the stream's tool calls finish executing
          if (mcpClient) {
            await mcpConnectionPool.release(mcpClient)
          }
        }
      }
    })
  } catch (err) {
    console.error('Chat API error:', err)

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
  } finally {
    // CRITICAL: Release connection if stream was never created
    // If stream was successfully created, onFinish's finally block will handle release
    // This guarantees connection is always released, even if error handling itself fails
    if (!streamCreated && mcpClient) {
      console.log('[MCP Pool] Releasing connection after setup failure')
      await mcpConnectionPool.release(mcpClient)
    }
  }
}
