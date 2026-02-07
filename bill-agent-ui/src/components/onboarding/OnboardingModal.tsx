'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import SleeperConnect from './SleeperConnect'
import LeagueSelector, { type SleeperLeague } from './LeagueSelector'
import { markOnboardingComplete } from '@/lib/supabase/onboarding'
import { supabase } from '@/lib/supabase/client'

interface OnboardingModalProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  onComplete?: () => void
  allowSkip?: boolean
}

type OnboardingStep = 'connect' | 'select-league' | 'complete'

export default function OnboardingModal({
  open,
  onOpenChange,
  onComplete,
  allowSkip = false
}: OnboardingModalProps) {
  const router = useRouter()
  const [step, setStep] = useState<OnboardingStep>('connect')
  const [username, setUsername] = useState<string>('')
  const [leagues, setLeagues] = useState<SleeperLeague[]>([])
  const [selectedLeague, setSelectedLeague] = useState<SleeperLeague | null>(
    null
  )
  const [error, setError] = useState<string | null>(null)

  /**
   * Step 1: Fetch leagues from Sleeper API via MCP tools
   */
  async function handleSleeperSubmit(sleeperUsername: string) {
    setError(null)
    setUsername(sleeperUsername)

    try {
      // Call the Sleeper MCP tool via the API route
      const response = await fetch('/api/sleeper/leagues', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ username: sleeperUsername })
      })

      const data = await response.json()

      if (!response.ok) {
        throw new Error(data.error || 'Failed to fetch leagues')
      }

      if (!data.leagues || data.leagues.length === 0) {
        throw new Error('No leagues found for this username')
      }

      setLeagues(data.leagues)
      setStep('select-league')
    } catch (err) {
      throw err instanceof Error ? err : new Error('Failed to fetch leagues')
    }
  }

  /**
   * Step 2: User selects a league
   */
  function handleLeagueSelect(league: SleeperLeague) {
    setSelectedLeague(league)
    setStep('complete')
  }

  /**
   * Step 3: Save onboarding data and navigate to chat
   */
  async function handleGetStarted() {
    if (!selectedLeague || !username) {
      setError('Missing required onboarding data')
      return
    }

    try {
      const {
        data: { user }
      } = await supabase.auth.getUser()

      if (!user) {
        throw new Error('No authenticated user found')
      }

      await markOnboardingComplete(
        user.id,
        username,
        selectedLeague.league_id,
        selectedLeague.name
      )

      onOpenChange(false)
      onComplete?.()
      router.push('/app')
    } catch (err) {
      setError(
        err instanceof Error ? err.message : 'Failed to complete onboarding'
      )
    }
  }

  /**
   * Reset modal state when closed
   */
  function handleOpenChange(isOpen: boolean) {
    if (!isOpen) {
      // Reset state when closing
      setStep('connect')
      setUsername('')
      setLeagues([])
      setSelectedLeague(null)
      setError(null)
    }
    onOpenChange(isOpen)
  }

  // Determine step title and description
  const stepConfig = {
    connect: {
      title: 'Welcome to BiLL-2 Evo',
      description:
        'Connect your Sleeper account to get personalized fantasy football insights'
    },
    'select-league': {
      title: 'Select Your League',
      description: 'Choose which league you want to analyze'
    },
    complete: {
      title: "You're All Set!",
      description:
        'Your Sleeper account is connected and ready to go'
    }
  }

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogContent
        className="sm:max-w-[500px] max-h-[85vh]"
        onInteractOutside={(e) => {
          // Prevent closing by clicking outside if skip is not allowed
          if (!allowSkip) {
            e.preventDefault()
          }
        }}
        onEscapeKeyDown={(e) => {
          // Prevent closing with Escape key if skip is not allowed
          if (!allowSkip) {
            e.preventDefault()
          }
        }}
      >
        <DialogHeader>
          <DialogTitle>{stepConfig[step].title}</DialogTitle>
          <DialogDescription>{stepConfig[step].description}</DialogDescription>
        </DialogHeader>

        {error && (
          <div className="rounded-md bg-red-50 p-4 text-sm text-red-800">
            {error}
          </div>
        )}

        <div className="mt-4">
          {step === 'connect' && (
            <SleeperConnect
              onSubmit={handleSleeperSubmit}
              initialUsername={username}
            />
          )}

          {step === 'select-league' && (
            <LeagueSelector
              leagues={leagues}
              onSelect={handleLeagueSelect}
              selectedLeagueId={selectedLeague?.league_id}
            />
          )}

          {step === 'complete' && selectedLeague && (
            <Button
              onClick={handleGetStarted}
              className="w-full text-black"
            >
              Get Started
            </Button>
          )}
        </div>
      </DialogContent>
    </Dialog>
  )
}
