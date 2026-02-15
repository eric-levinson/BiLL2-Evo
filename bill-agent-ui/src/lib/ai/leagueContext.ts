/**
 * Pre-resolves league scoring settings from the Sleeper API.
 * Used in the context pipeline to inject league format into the system prompt,
 * eliminating redundant get_sleeper_league_by_id tool calls on every query.
 *
 * Results cached in-memory with a 5-minute TTL — scoring settings
 * don't change mid-conversation or mid-season.
 */

export interface LeagueContext {
  leagueName: string
  scoringFormat: string
  isSuperFlex: boolean
  teamCount: number
  rosterSummary: string
}

interface CacheEntry {
  data: LeagueContext
  expiresAt: number
}

const CACHE_TTL_MS = 5 * 60 * 1000 // 5 minutes
const cache = new Map<string, CacheEntry>()

/**
 * Classifies the scoring format from Sleeper scoring_settings.
 */
function classifyScoringFormat(
  scoringSettings: Record<string, number> | undefined
): string {
  if (!scoringSettings) return 'Standard'
  const rec = scoringSettings.rec ?? 0
  if (rec >= 1.0) return 'Full PPR'
  if (rec >= 0.5) return 'Half PPR'
  return 'Standard'
}

/**
 * Detects Superflex from roster_positions array.
 */
function detectSuperFlex(rosterPositions: string[] | undefined): boolean {
  if (!rosterPositions) return false
  return rosterPositions.includes('SUPER_FLEX')
}

/**
 * Builds a compact roster summary from roster_positions.
 * e.g. "1QB/2RB/2WR/1TE/1FLEX/1SFLEX/6BN/2IR"
 */
function buildRosterSummary(rosterPositions: string[] | undefined): string {
  if (!rosterPositions || rosterPositions.length === 0) return 'Unknown'

  const counts: Record<string, number> = {}
  for (const pos of rosterPositions) {
    counts[pos] = (counts[pos] ?? 0) + 1
  }

  const displayOrder = [
    'QB',
    'RB',
    'WR',
    'TE',
    'FLEX',
    'SUPER_FLEX',
    'REC_FLEX',
    'K',
    'DEF',
    'DL',
    'LB',
    'DB',
    'IDP_FLEX',
    'BN',
    'IR'
  ]

  const shortNames: Record<string, string> = {
    SUPER_FLEX: 'SFLEX',
    REC_FLEX: 'RFLEX',
    IDP_FLEX: 'IDP'
  }

  const parts: string[] = []
  for (const pos of displayOrder) {
    if (counts[pos]) {
      const label = shortNames[pos] ?? pos
      parts.push(`${counts[pos]}${label}`)
      delete counts[pos]
    }
  }

  // Any remaining positions not in displayOrder
  for (const [pos, count] of Object.entries(counts)) {
    const label = shortNames[pos] ?? pos
    parts.push(`${count}${label}`)
  }

  return parts.join('/')
}

/**
 * Fetches and resolves league settings from the Sleeper API.
 * Returns null on any failure — this is an optimization, not a requirement.
 * Cached for 5 minutes per league_id.
 */
export async function resolveLeagueSettings(
  leagueId: string
): Promise<LeagueContext | null> {
  // Check cache first
  const cached = cache.get(leagueId)
  if (cached && Date.now() < cached.expiresAt) {
    return cached.data
  }

  try {
    const response = await fetch(
      `https://api.sleeper.app/v1/league/${leagueId}`,
      { signal: AbortSignal.timeout(3000) }
    )

    if (!response.ok) {
      console.warn(
        `[League Context] Sleeper API returned ${response.status} for league ${leagueId}`
      )
      return null
    }

    const league = await response.json()

    const context: LeagueContext = {
      leagueName: league.name ?? 'Unknown League',
      scoringFormat: classifyScoringFormat(league.scoring_settings),
      isSuperFlex: detectSuperFlex(league.roster_positions),
      teamCount: league.total_rosters ?? 0,
      rosterSummary: buildRosterSummary(league.roster_positions)
    }

    // Store rec value detail for prompt
    const rec = league.scoring_settings?.rec ?? 0
    const formatDetail = `${context.scoringFormat} (rec = ${rec})`
    context.scoringFormat = formatDetail

    // Cache the result
    cache.set(leagueId, {
      data: context,
      expiresAt: Date.now() + CACHE_TTL_MS
    })

    console.log(
      `[League Context] Resolved league ${leagueId}: ${context.leagueName}, ${context.scoringFormat}, ${context.teamCount} teams`
    )

    return context
  } catch (err) {
    // Graceful degradation — agent falls back to asking user or fetching via tool
    console.warn(
      `[League Context] Failed to resolve league ${leagueId}:`,
      err instanceof Error ? err.message : String(err)
    )
    return null
  }
}
