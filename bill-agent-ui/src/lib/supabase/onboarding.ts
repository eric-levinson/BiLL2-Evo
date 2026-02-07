import { supabase } from '@/lib/supabase/client'

export interface UserOnboarding {
  id: string
  user_id: string
  completed: boolean
  sleeper_username: string | null
  selected_league_id: string | null
  league_name: string | null
  created_at: string
  updated_at: string
}

export interface UserOnboardingUpdate {
  completed?: boolean
  sleeper_username?: string | null
  selected_league_id?: string | null
  league_name?: string | null
}

/**
 * Retrieves the onboarding record for a user
 * @param userId - UUID of the user whose onboarding data to retrieve
 * @returns The onboarding record or null if not found
 */
export async function getUserOnboarding(
  userId: string
): Promise<UserOnboarding | null> {
  const { data, error } = await supabase
    .from('user_onboarding')
    .select('*')
    .eq('user_id', userId)
    .single()

  if (error) {
    // Return null if no record exists (expected for new users)
    if (error.code === 'PGRST116') {
      return null
    }
    console.error('Error fetching user onboarding:', error)
    return null
  }

  return data
}

/**
 * Creates a new onboarding record for a user
 * @param userId - UUID of the user creating the onboarding record
 * @param data - Optional initial onboarding data
 * @returns The created onboarding record or null if failed
 */
export async function createUserOnboarding(
  userId: string,
  data?: Partial<UserOnboardingUpdate>
): Promise<UserOnboarding | null> {
  const { data: result, error } = await supabase
    .from('user_onboarding')
    .insert({
      user_id: userId,
      completed: data?.completed ?? false,
      sleeper_username: data?.sleeper_username ?? null,
      selected_league_id: data?.selected_league_id ?? null,
      league_name: data?.league_name ?? null
    })
    .select()
    .single()

  if (error) {
    console.error('Error creating user onboarding:', error)
    return null
  }

  return result
}

/**
 * Updates an existing onboarding record for a user
 * @param userId - UUID of the user whose onboarding to update
 * @param data - Updated onboarding data fields
 * @returns The updated onboarding record or null if failed
 */
export async function updateUserOnboarding(
  userId: string,
  data: UserOnboardingUpdate
): Promise<UserOnboarding | null> {
  const { data: result, error } = await supabase
    .from('user_onboarding')
    .update(data)
    .eq('user_id', userId)
    .select()
    .single()

  if (error) {
    console.error('Error updating user onboarding:', error)
    return null
  }

  return result
}

/**
 * Marks onboarding as complete with Sleeper league connection details
 * This is a convenience function that combines the common completion fields
 * @param userId - UUID of the user completing onboarding
 * @param sleeperUsername - User's Sleeper username
 * @param leagueId - Selected Sleeper league ID
 * @param leagueName - Name of the selected league
 * @returns The updated onboarding record or null if failed
 */
export async function markOnboardingComplete(
  userId: string,
  sleeperUsername: string,
  leagueId: string,
  leagueName: string
): Promise<UserOnboarding | null> {
  // First, check if onboarding record exists
  const existing = await getUserOnboarding(userId)

  if (existing) {
    // Update existing record
    return updateUserOnboarding(userId, {
      completed: true,
      sleeper_username: sleeperUsername,
      selected_league_id: leagueId,
      league_name: leagueName
    })
  } else {
    // Create new record
    return createUserOnboarding(userId, {
      completed: true,
      sleeper_username: sleeperUsername,
      selected_league_id: leagueId,
      league_name: leagueName
    })
  }
}
