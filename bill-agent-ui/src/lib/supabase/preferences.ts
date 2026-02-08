import { supabase } from '@/lib/supabase/client'

export interface ConnectedLeague {
  league_id: string
  name: string
  scoring_format: string
  season: number
  is_primary: boolean
}

export interface RosterNotes {
  [league_id: string]: {
    team_name?: string
    key_players?: string[]
    strengths?: string[]
    needs?: string[]
  }
}

export interface UserPreferences {
  id: string
  user_id: string
  connected_leagues: ConnectedLeague[]
  primary_league_id: string | null
  favorite_players: string[]
  roster_notes: RosterNotes
  analysis_style: string
  preference_tags: string[]
  custom_preferences: Record<string, any>
  created_at: string
  updated_at: string
}

export interface UserPreferencesUpdate {
  connected_leagues?: ConnectedLeague[]
  primary_league_id?: string | null
  favorite_players?: string[]
  roster_notes?: RosterNotes
  analysis_style?: string
  preference_tags?: string[]
  custom_preferences?: Record<string, any>
}

/**
 * Retrieves the preferences record for a user
 * @param userId - UUID of the user whose preferences to retrieve
 * @returns The preferences record or null if not found
 */
export async function getUserPreferences(
  userId: string
): Promise<UserPreferences | null> {
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
 * Creates a new preferences record for a user
 * @param userId - UUID of the user creating the preferences record
 * @param data - Optional initial preferences data
 * @returns The created preferences record or null if failed
 */
export async function createUserPreferences(
  userId: string,
  data?: Partial<UserPreferencesUpdate>
): Promise<UserPreferences | null> {
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
 * Updates an existing preferences record for a user
 * @param userId - UUID of the user whose preferences to update
 * @param data - Updated preferences data fields
 * @returns The updated preferences record or null if failed
 */
export async function updateUserPreferences(
  userId: string,
  data: UserPreferencesUpdate
): Promise<UserPreferences | null> {
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
