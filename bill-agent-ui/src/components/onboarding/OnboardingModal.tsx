'use client'

import { useState } from 'react'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle
} from '@/components/ui/dialog'
import SleeperConnect from './SleeperConnect'
import LeagueSelector, { type SleeperLeague } from './LeagueSelector'
import ExampleQueries from './ExampleQueries'
import { markOnboardingComplete } from '@/lib/supabase/onboarding'
import { supabase } from '@/lib/supabase/client'

interface OnboardingModalProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  onComplete?: () => void
  allowSkip?: boolean
}

type OnboardingStep = 'connect' | 'select-league' | 'examples'

export default function OnboardingModal({
  open,
  onOpenChange,
  onComplete,
  allowSkip = false
}: OnboardingModalProps) {
  const [step, setStep] = useState<OnboardingStep>('connect')
  const [username, setUsername] = useState<string>('')
  const [leagues, setLeagues] = useState<SleeperLeague[]>([])
  const [selectedLeague, setSelectedLeague] = useState<SleeperLeague | null>(null)
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

      if (!response.ok) {
        throw new Error('Failed to fetch leagues')
      }

      const data = await response.json()

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
    setStep('examples')
  }

  /**
   * Step 3: User completes onboarding
   */
  async function handleComplete() {
    if (!selectedLeague || !username) {
      setError('Missing required onboarding data')
      return
    }

    try {
      // Get current user
      const {
        data: { user }
      } = await supabase.auth.getUser()

      if (!user) {
        throw new Error('No authenticated user found')
      }

      // Save onboarding data to Supabase
      await markOnboardingComplete(
        user.id,
        username,
        selectedLeague.league_id,
        selectedLeague.name
      )

      // Close modal and trigger completion callback
      onOpenChange(false)
      onComplete?.()
    } catch (err) {
      setError(
        err instanceof Error ? err.message : 'Failed to complete onboarding'
      )
    }
  }

  /**
   * Auto-fill chat with selected example query
   */
  function handleQuerySelect(query: string) {
    // This will be implemented when integrating with the chat UI
    // For now, we'll just log it
    console.info('Selected query:', query)
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
    examples: {
      title: "You're All Set!",
      description:
        'Here are some example questions to get you started with BiLL-2'
    }
  }

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogContent
        className="sm:max-w-[500px]"
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

          {step === 'examples' && selectedLeague && (
            <ExampleQueries
              league={selectedLeague}
              onQuerySelect={handleQuerySelect}
              onComplete={handleComplete}
            />
          )}
        </div>
      </DialogContent>
    </Dialog>
  )
}
