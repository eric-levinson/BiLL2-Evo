'use client'

import { useState } from 'react'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue
} from '@/components/ui/select'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle
} from '@/components/ui/card'
import { Button } from '@/components/ui/button'

/**
 * Sleeper League object structure
 * Based on Sleeper API response format
 */
export interface SleeperLeague {
  league_id: string
  name: string
  settings: {
    type: number // 0 = redraft, 1 = keeper, 2 = dynasty
  }
  total_rosters: number
  season?: string
  sport?: string
}

interface LeagueSelectorProps {
  leagues: SleeperLeague[]
  onSelect: (league: SleeperLeague) => void
  selectedLeagueId?: string
}

export default function LeagueSelector({
  leagues,
  onSelect,
  selectedLeagueId
}: LeagueSelectorProps) {
  const [selected, setSelected] = useState<string>(selectedLeagueId || '')

  // Helper function to format league type
  const getLeagueType = (type: number): string => {
    switch (type) {
      case 0:
        return 'Redraft'
      case 1:
        return 'Keeper'
      case 2:
        return 'Dynasty'
      default:
        return 'Unknown'
    }
  }

  // Find the currently selected league object
  const selectedLeague = leagues.find((league) => league.league_id === selected)

  const handleSelectChange = (leagueId: string) => {
    setSelected(leagueId)
  }

  const handleContinue = () => {
    if (selectedLeague) {
      onSelect(selectedLeague)
    }
  }

  if (leagues.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>No Leagues Found</CardTitle>
          <CardDescription>
            We couldn&apos;t find any leagues for this Sleeper username. Please
            check your username and try again.
          </CardDescription>
        </CardHeader>
      </Card>
    )
  }

  return (
    <div className="flex flex-col gap-4">
      <div className="grid gap-2">
        <label htmlFor="league-select" className="text-sm font-medium">
          Select a League
        </label>
        <Select value={selected} onValueChange={handleSelectChange}>
          <SelectTrigger id="league-select">
            <SelectValue placeholder="Choose a league..." />
          </SelectTrigger>
          <SelectContent>
            {leagues.map((league) => (
              <SelectItem key={league.league_id} value={league.league_id}>
                {league.name} ({getLeagueType(league.settings.type)} •{' '}
                {league.total_rosters} teams)
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {selectedLeague && (
        <Card>
          <CardHeader>
            <CardTitle>{selectedLeague.name}</CardTitle>
            <CardDescription>League Details</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid gap-2 text-sm">
              <div className="flex justify-between">
                <span className="text-muted-foreground">League Type:</span>
                <span className="font-medium">
                  {getLeagueType(selectedLeague.settings.type)}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Total Teams:</span>
                <span className="font-medium">
                  {selectedLeague.total_rosters}
                </span>
              </div>
              {selectedLeague.season && (
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Season:</span>
                  <span className="font-medium">{selectedLeague.season}</span>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      )}

      <Button
        onClick={handleContinue}
        disabled={!selectedLeague}
        className="w-full text-black"
      >
        Continue
      </Button>
    </div>
  )
}
