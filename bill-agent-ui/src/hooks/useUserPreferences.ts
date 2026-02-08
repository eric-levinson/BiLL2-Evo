'use client'

import { useState, useEffect, useCallback } from 'react'
import { supabase } from '@/lib/supabase/client'
import {
  getUserPreferences,
  type UserPreferences
} from '@/lib/supabase/preferences'

interface UseUserPreferencesReturn {
  preferencesData: UserPreferences | null
  isLoading: boolean
  refetch: () => Promise<void>
}

/**
 * Hook to manage user preferences state for the current user.
 * Fetches the user's preferences record from Supabase including
 * connected leagues, favorite players, analysis style, and custom preferences.
 *
 * @returns {UseUserPreferencesReturn} Object containing:
 *   - preferencesData: The user's preferences record or null
 *   - isLoading: Whether the preferences data is being fetched
 *   - refetch: Function to manually refetch the preferences data
 */
export function useUserPreferences(): UseUserPreferencesReturn {
  const [preferencesData, setPreferencesData] =
    useState<UserPreferences | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  const fetchPreferences = useCallback(async () => {
    setIsLoading(true)
    try {
      const {
        data: { user },
        error: userError
      } = await supabase.auth.getUser()

      if (userError || !user) {
        console.warn(
          'No authenticated user found, skipping preferences fetch'
        )
        setPreferencesData(null)
        return
      }

      const data = await getUserPreferences(user.id)
      setPreferencesData(data)
    } catch (error) {
      console.error('Error fetching user preferences:', error)
      setPreferencesData(null)
    } finally {
      setIsLoading(false)
    }
  }, [])

  // Fetch preferences data on mount
  useEffect(() => {
    fetchPreferences()
  }, [fetchPreferences])

  return {
    preferencesData,
    isLoading,
    refetch: fetchPreferences
  }
}

export default useUserPreferences
