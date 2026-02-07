import { NextResponse } from 'next/server'

const SLEEPER_API_BASE = 'https://api.sleeper.app/v1'

/**
 * POST /api/sleeper/leagues
 * Fetches Sleeper leagues for a given username via the public Sleeper API
 */
export async function POST(request: Request) {
  try {
    const { username } = await request.json()

    if (!username || typeof username !== 'string') {
      return NextResponse.json(
        { error: 'Username is required' },
        { status: 400 }
      )
    }

    // Step 1: Resolve username to user_id
    const userRes = await fetch(`${SLEEPER_API_BASE}/user/${username}`)

    if (!userRes.ok || userRes.status === 404) {
      return NextResponse.json(
        { error: 'Sleeper user not found. Please check your username.' },
        { status: 404 }
      )
    }

    const userData = await userRes.json()

    if (!userData?.user_id) {
      return NextResponse.json(
        { error: 'Sleeper user not found. Please check your username.' },
        { status: 404 }
      )
    }

    // Step 2: Fetch leagues for the user
    const leaguesRes = await fetch(
      `${SLEEPER_API_BASE}/user/${userData.user_id}/leagues/nfl/2025`
    )

    if (!leaguesRes.ok) {
      return NextResponse.json(
        { error: 'Failed to fetch leagues from Sleeper' },
        { status: 502 }
      )
    }

    const leagues = await leaguesRes.json()

    if (!Array.isArray(leagues) || leagues.length === 0) {
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
  }
}
