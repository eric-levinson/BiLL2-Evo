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
