'use client'

import { useState } from 'react'
import { useOnboarding } from '@/hooks/useOnboarding'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle
} from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import OnboardingModal from '@/components/onboarding/OnboardingModal'

/**
 * SleeperConnectionSettings component displays the user's current
 * Sleeper account connection and allows them to change it.
 *
 * Shows:
 * - Current Sleeper username
 * - Current connected league name
 * - Button to change/update the connection
 */
export default function SleeperConnectionSettings() {
  const { onboardingData, isLoading, refetch } = useOnboarding()
  const [showOnboardingModal, setShowOnboardingModal] = useState(false)

  /**
   * Handle completion of the onboarding modal
   * Refetch the onboarding data to show updated connection
   */
  async function handleOnboardingComplete() {
    await refetch()
    setShowOnboardingModal(false)
  }

  return (
    <>
      <Card>
        <CardHeader>
          <CardTitle>Sleeper Connection</CardTitle>
          <CardDescription>
            Manage your connected Sleeper account and league
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {isLoading ? (
            <div className="text-muted-foreground text-sm">
              Loading connection status...
            </div>
          ) : onboardingData?.sleeper_username ? (
            <div className="space-y-2">
              <div>
                <div className="text-sm font-medium">Username</div>
                <div className="text-muted-foreground text-sm">
                  {onboardingData.sleeper_username}
                </div>
              </div>
              {onboardingData.league_name && (
                <div>
                  <div className="text-sm font-medium">Connected League</div>
                  <div className="text-muted-foreground text-sm">
                    {onboardingData.league_name}
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="text-muted-foreground text-sm">
              No Sleeper account connected
            </div>
          )}

          <Button
            onClick={() => setShowOnboardingModal(true)}
            variant="outline"
            className="w-full sm:w-auto"
          >
            {onboardingData?.sleeper_username
              ? 'Change Connection'
              : 'Connect Sleeper Account'}
          </Button>
        </CardContent>
      </Card>

      <OnboardingModal
        open={showOnboardingModal}
        onOpenChange={setShowOnboardingModal}
        onComplete={handleOnboardingComplete}
        allowSkip={true}
      />
    </>
  )
}
