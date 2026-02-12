import { createServerSupabaseClient } from '../server'
import type {
  UserPreferences,
  UserPreferencesUpdate
} from '../preferences'

/**
 * Retrieves the preferences record for a user (server-side)
 * @param userId - UUID of the user whose preferences to retrieve
 * @returns The preferences record or null if not found
 */
export async function getUserPreferences(
  userId: string
): Promise<UserPreferences | null> {
  const supabase = await createServerSupabaseClient()

  const { data, error } = await supabase
    .from('user_preferences')
    .select('*')
    .eq('user_id', userId)
    .single()

  if (error) {
    // Return null if no record exists (expected for new users)
    if (error.code === 'PGRST116') {
      return null
    }
    console.error('Error fetching user preferences:', error)
    return null
  }

  return data
}

/**
 * Creates a new preferences record for a user (server-side)
 * @param userId - UUID of the user creating the preferences record
 * @param data - Optional initial preferences data
 * @returns The created preferences record or null if failed
 */
export async function createUserPreferences(
  userId: string,
  data?: Partial<UserPreferencesUpdate>
): Promise<UserPreferences | null> {
  const supabase = await createServerSupabaseClient()

  const { data: result, error } = await supabase
    .from('user_preferences')
    .insert({
      user_id: userId,
      connected_leagues: data?.connected_leagues ?? [],
      primary_league_id: data?.primary_league_id ?? null,
      favorite_players: data?.favorite_players ?? [],
      roster_notes: data?.roster_notes ?? {},
      analysis_style: data?.analysis_style ?? 'balanced',
      preference_tags: data?.preference_tags ?? [],
      custom_preferences: data?.custom_preferences ?? {}
    })
    .select()
    .single()

  if (error) {
    console.error('Error creating user preferences:', error)
    return null
  }

  return result
}

/**
 * Updates an existing preferences record for a user (server-side)
 * @param userId - UUID of the user whose preferences to update
 * @param data - Updated preferences data fields
 * @returns The updated preferences record or null if failed
 */
export async function updateUserPreferences(
  userId: string,
  data: UserPreferencesUpdate
): Promise<UserPreferences | null> {
  const supabase = await createServerSupabaseClient()

  const { data: result, error } = await supabase
    .from('user_preferences')
    .update(data)
    .eq('user_id', userId)
    .select()
    .single()

  if (error) {
    console.error('Error updating user preferences:', error)
    return null
  }

  return result
}

/**
 * Formats user preferences into a markdown string for system prompt injection
 * @param preferences - User preferences object
 * @returns Formatted markdown string
 */
export function formatPreferencesForPrompt(preferences: UserPreferences | null): string {
  // Check if user has ANY preferences set (not just connected leagues)
  const hasPreferences =
    preferences &&
    (preferences.connected_leagues?.length > 0 ||
      preferences.favorite_players?.length > 0 ||
      (preferences.analysis_style && preferences.analysis_style !== 'balanced') ||
      preferences.preference_tags?.length > 0)

  if (!hasPreferences) {
    return 'No user preferences stored yet.'
  }

  let context = '## User Context\n\n'

  // Connected Leagues
  if (preferences.connected_leagues?.length > 0) {
    context += '**Connected Sleeper Leagues:**\n'
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    preferences.connected_leagues.forEach((league: any) => {
      context += `- ${league.name} (${league.season}, ${league.scoring_format})${league.is_primary ? ' [PRIMARY]' : ''}\n`
    })
    context += '\n'
  }

  // Favorite Players
  if (preferences.favorite_players?.length > 0) {
    context += `**Favorite Players:** ${preferences.favorite_players.join(', ')}\n\n`
  }

  // Analysis Style
  if (preferences.analysis_style) {
    context += `**Preferred Analysis Style:** ${preferences.analysis_style}\n\n`
  }

  // Tags
  if (preferences.preference_tags?.length > 0) {
    context += `**User Focus Areas:** ${preferences.preference_tags.join(', ')}\n\n`
  }

  // Roster Notes (if primary league set)
  if (preferences.primary_league_id && preferences.roster_notes?.[preferences.primary_league_id]) {
    const notes = preferences.roster_notes[preferences.primary_league_id]
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
