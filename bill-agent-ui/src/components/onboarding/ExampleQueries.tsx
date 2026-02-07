'use client'

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import type { SleeperLeague } from './LeagueSelector'

interface ExampleQueriesProps {
  league: SleeperLeague
  onQuerySelect: (query: string) => void
  onComplete: () => void
}

export default function ExampleQueries({
  league,
  onQuerySelect,
  onComplete
}: ExampleQueriesProps) {
  // Generate example queries tailored to the selected league
  const exampleQueries = [
    `Show me my roster in ${league.name}`,
    `What's my Week 1 matchup in ${league.name}?`,
    `Compare my running backs to the league average`,
    `Show me the top available free agents for my team`,
    `Analyze my team's strengths and weaknesses`,
    `Who should I start this week?`,
    `Show me recent trades in ${league.name}`,
    `What are the best waiver wire pickups right now?`
  ]

  const handleQueryClick = (query: string) => {
    onQuerySelect(query)
  }

  return (
    <div className="flex flex-col gap-6">
      <Card>
        <CardHeader>
          <CardTitle>Try These Questions</CardTitle>
          <CardDescription>
            Click any question below to see what BiLL-2 can do with your {league.name} data
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-2">
            {exampleQueries.map((query, index) => (
              <Button
                key={index}
                variant="outline"
                className="justify-start text-left h-auto py-3 px-4"
                onClick={() => handleQueryClick(query)}
              >
                <span className="text-sm">{query}</span>
              </Button>
            ))}
          </div>
        </CardContent>
      </Card>

      <div className="flex flex-col gap-2">
        <Button onClick={onComplete} className="w-full text-black">
          Get Started
        </Button>
        <p className="text-xs text-muted-foreground text-center">
          You can ask any of these questions (or anything else!) once you complete setup
        </p>
      </div>
    </div>
  )
}
