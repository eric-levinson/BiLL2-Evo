import { NextResponse } from 'next/server'
import { createMCPClient } from '@ai-sdk/mcp'

/**
 * POST /api/sleeper/leagues
 * Fetches Sleeper leagues for a given username via MCP tool
 */
export async function POST(request: Request) {
  let mcpClient: Awaited<ReturnType<typeof createMCPClient>> | undefined

  try {
    const { username } = await request.json()

    if (!username || typeof username !== 'string') {
      return NextResponse.json(
        { error: 'Username is required' },
        { status: 400 }
      )
    }

    // Create MCP client to connect to fantasy-tools-mcp server
    const mcpServerUrl =
      process.env.MCP_SERVER_URL || 'http://localhost:8000/mcp/'

    mcpClient = await createMCPClient({
      transport: {
        type: 'http',
        url: mcpServerUrl
      },
      name: 'fantasy-tools'
    })

    // Call the get_sleeper_leagues_by_username MCP tool
    const result = await mcpClient.callTool({
      name: 'get_sleeper_leagues_by_username',
      arguments: {
        username,
        verbose: false // Don't need full settings for onboarding
      }
    })

    // Parse the result
    // MCP tool returns result in result.content array
    if (!result.content || result.content.length === 0) {
      return NextResponse.json(
        { error: 'No response from MCP server' },
        { status: 500 }
      )
    }

    // Extract leagues from MCP response
    // The content is typically an array with a text item containing JSON
    const content = result.content[0]
    let leagues = []

    if (content.type === 'text') {
      const data = JSON.parse(content.text)
      leagues = data.leagues || data || []
    }

    if (!leagues || leagues.length === 0) {
      return NextResponse.json(
        { error: 'No leagues found for this username' },
        { status: 404 }
      )
    }

    return NextResponse.json({ leagues })
  } catch (error) {
    console.error('Error fetching Sleeper leagues:', error)
    return NextResponse.json(
      {
        error:
          error instanceof Error
            ? error.message
            : 'Failed to fetch Sleeper leagues'
      },
      { status: 500 }
    )
  } finally {
    // Clean up MCP client resources
    await mcpClient?.close()
  }
}
