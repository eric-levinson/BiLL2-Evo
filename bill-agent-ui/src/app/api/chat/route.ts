import { NextResponse } from 'next/server'
import { createServerSupabaseClient } from '@/lib/supabase/server'
import { createMCPClient } from '@ai-sdk/mcp'
import { ToolLoopAgent, createAgentUIStreamResponse, stepCountIs } from 'ai'
import { anthropic } from '@ai-sdk/anthropic'

export async function POST(req: Request) {
  // Verify authentication
  const supabase = await createServerSupabaseClient()
  const { data } = await supabase.auth.getUser()
  const user = data?.user ?? null

  if (!user) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
  }

  let mcpClient

  try {
    // Parse request body
    const body = await req.json()
    const { messages } = body

    if (!messages || !Array.isArray(messages)) {
      return NextResponse.json(
        { error: 'Messages array is required' },
        { status: 400 }
      )
    }

    // Create MCP client with streamable HTTP transport
    const mcpServerUrl =
      process.env.MCP_SERVER_URL || 'http://localhost:8000/mcp/'
    mcpClient = await createMCPClient({
      transport: {
        type: 'http',
        url: mcpServerUrl
      }
    })

    // Get all available tools from MCP server
    const tools = await mcpClient.tools()

    // Create ToolLoopAgent with Claude
    const modelId = process.env.AI_MODEL_ID || 'claude-sonnet-4-20250514'
    const agent = new ToolLoopAgent({
      model: anthropic(modelId),
      tools,
      stopWhen: stepCountIs(10),
      instructions: `You are BiLL, an advanced fantasy football analyst powered by AI.

Your capabilities:
- Access to comprehensive NFL player stats (season & weekly advanced metrics)
- Real-time Sleeper league data (rosters, matchups, transactions, trending players)
- Dynasty and redraft rankings
- Game-level offensive and defensive statistics
- Player information and metrics metadata

Guidelines for tool usage:
1. Always use the appropriate tools to fetch data rather than relying on your training data
2. For player lookups, start with get_player_info_tool to get accurate player IDs and current team info
3. When analyzing stats, use the advanced stats tools (receiving/passing/rushing/defense) for deeper insights
4. For league-specific questions, use Sleeper API tools to get current roster and matchup data
5. When discussing rankings, fetch the latest dynasty or redraft rankings via get_fantasy_ranks
6. Provide data-driven insights and back up your recommendations with specific metrics
7. If you need clarification on available metrics, use get_metrics_metadata

Remember:
- Be conversational but analytical
- Cite specific stats when making recommendations
- Consider both current performance and historical trends
- For dynasty leagues, factor in player age and long-term value
- Always verify player names and team affiliations before making claims`
    })

    // Stream response back to client
    return createAgentUIStreamResponse({
      agent,
      uiMessages: messages
    })
  } catch (err) {
    console.error('Chat API error:', err)
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    )
  } finally {
    // Close MCP client to prevent resource leaks
    if (mcpClient) {
      await mcpClient.close()
    }
  }
}
