'use client'

import { useState, useEffect, useCallback } from 'react'
import { supabase } from '@/lib/supabase/client'
import {
  getUserOnboarding,
  type UserOnboarding
} from '@/lib/supabase/onboarding'

interface UseOnboardingReturn {
  onboardingData: UserOnboarding | null
  isLoading: boolean
  showOnboarding: boolean
  refetch: () => Promise<void>
}

/**
 * Hook to manage onboarding state for the current user.
 * Fetches the user's onboarding record from Supabase and determines
 * whether the onboarding modal should be displayed.
 *
 * @returns {UseOnboardingReturn} Object containing:
 *   - onboardingData: The user's onboarding record or null
 *   - isLoading: Whether the onboarding data is being fetched
 *   - showOnboarding: Whether to show the onboarding modal (!completed)
 *   - refetch: Function to manually refetch the onboarding data
 */
export function useOnboarding(): UseOnboardingReturn {
  const [onboardingData, setOnboardingData] = useState<UserOnboarding | null>(
    null
  )
  const [isLoading, setIsLoading] = useState(true)

  const fetchOnboarding = useCallback(async () => {
    setIsLoading(true)
    try {
      const {
        data: { user },
        error: userError
      } = await supabase.auth.getUser()

      if (userError || !user) {
        console.warn('No authenticated user found, skipping onboarding fetch')
        setOnboardingData(null)
        return
      }

      const data = await getUserOnboarding(user.id)
      setOnboardingData(data)
    } catch (error) {
      console.error('Error fetching onboarding data:', error)
      setOnboardingData(null)
    } finally {
      setIsLoading(false)
    }
  }, [])

  // Fetch onboarding data on mount
  useEffect(() => {
    fetchOnboarding()
  }, [fetchOnboarding])

  // Determine if onboarding should be shown
  // Show onboarding if: user is authenticated AND (no record exists OR completed is false)
  const showOnboarding = !onboardingData?.completed

  return {
    onboardingData,
    isLoading,
    showOnboarding,
    refetch: fetchOnboarding
  }
}

export default useOnboarding
