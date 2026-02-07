'use client'

import { useState, useEffect } from 'react'
import OnboardingModal from './OnboardingModal'
import { useOnboarding } from '@/hooks/useOnboarding'

/**
 * Client component wrapper that manages onboarding modal state.
 * Shows the onboarding modal for new users who haven't completed onboarding.
 */
export default function OnboardingWrapper() {
  const { showOnboarding, refetch, isLoading } = useOnboarding()
  const [isOpen, setIsOpen] = useState(false)

  // Update modal open state when showOnboarding changes
  // This ensures the modal appears for new users once data is loaded
  useEffect(() => {
    if (!isLoading && showOnboarding) {
      setIsOpen(true)
    }
  }, [showOnboarding, isLoading])

  function handleComplete() {
    // Refetch onboarding data to update state
    refetch()
    setIsOpen(false)
  }

  return (
    <OnboardingModal
      open={isOpen}
      onOpenChange={setIsOpen}
      onComplete={handleComplete}
      allowSkip={false}
    />
  )
}
