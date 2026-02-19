'use client'

import { useUserPreferences } from '@/hooks/useUserPreferences'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle
} from '@/components/ui/card'

/**
 * UserPreferencesSettings component displays the user's stored preferences
 * including connected leagues, favorite players, analysis style, and preference tags.
 *
 * Shows:
 * - Connected Sleeper leagues with primary indicator
 * - Favorite players list
 * - Preferred analysis style
 * - User focus areas (preference tags)
 */
export default function UserPreferencesSettings() {
  const { preferencesData, isLoading } = useUserPreferences()

  return (
    <Card>
      <CardHeader>
        <CardTitle>User Preferences</CardTitle>
        <CardDescription>
          Your stored preferences and settings that the AI remembers across
          conversations
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        {isLoading ? (
          <div className="text-muted-foreground text-sm">
            Loading preferences...
          </div>
        ) : !preferencesData ? (
          <div className="text-muted-foreground text-sm">
            No preferences stored yet. The AI will remember your preferences as
            you interact with it.
          </div>
        ) : (
          <>
            {/* Connected Leagues */}
            {preferencesData.connected_leagues &&
              preferencesData.connected_leagues.length > 0 && (
                <div className="space-y-2">
                  <div className="text-sm font-medium">Connected Leagues</div>
                  <div className="space-y-2">
                    {preferencesData.connected_leagues.map((league) => (
                      <div
                        key={league.league_id}
                        className="rounded-lg border p-3 text-sm"
                      >
                        <div className="flex items-start justify-between gap-2">
                          <div className="space-y-1">
                            <div className="font-medium">{league.name}</div>
                            {(league.season || league.scoring_format) && (
                              <div className="text-muted-foreground text-xs">
                                {[league.season, league.scoring_format]
                                  .filter(Boolean)
                                  .join(' • ')}
                              </div>
                            )}
                          </div>
                          {league.is_primary && (
                            <span className="text-secondary-foreground rounded-md bg-secondary px-2 py-1 text-xs font-medium">
                              Primary
                            </span>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

            {/* Favorite Players */}
            {preferencesData.favorite_players &&
              preferencesData.favorite_players.length > 0 && (
                <div className="space-y-2">
                  <div className="text-sm font-medium">Favorite Players</div>
                  <div className="flex flex-wrap gap-2">
                    {preferencesData.favorite_players.map((player) => (
                      <span
                        key={player}
                        className="rounded-md border border-border bg-background px-2 py-1 text-xs"
                      >
                        {player}
                      </span>
                    ))}
                  </div>
                </div>
              )}

            {/* Analysis Style */}
            {preferencesData.analysis_style &&
              preferencesData.analysis_style !== 'balanced' && (
                <div className="space-y-2">
                  <div className="text-sm font-medium">
                    Preferred Analysis Style
                  </div>
                  <div className="text-muted-foreground text-sm capitalize">
                    {preferencesData.analysis_style}
                  </div>
                </div>
              )}

            {/* Preference Tags */}
            {preferencesData.preference_tags &&
              preferencesData.preference_tags.length > 0 && (
                <div className="space-y-2">
                  <div className="text-sm font-medium">Focus Areas</div>
                  <div className="flex flex-wrap gap-2">
                    {preferencesData.preference_tags.map((tag) => (
                      <span
                        key={tag}
                        className="rounded-md border border-border bg-background px-2 py-1 text-xs font-medium"
                      >
                        {tag}
                      </span>
                    ))}
                  </div>
                </div>
              )}
          </>
        )}

        <div className="text-muted-foreground rounded-lg bg-muted p-3 text-xs">
          <strong>Tip:</strong> You can update these preferences by asking the
          AI to remember things. For example: &quot;Remember that I prefer
          data-heavy analysis&quot; or &quot;Add Brock Purdy to my favorite
          players&quot;
        </div>
      </CardContent>
    </Card>
  )
}
