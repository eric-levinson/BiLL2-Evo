/**
 * Custom AI SDK tools for user preference management
 * Provides tools for updating user preferences, managing connected Sleeper leagues,
 * and maintaining roster notes via the BiLL AI agent
 *
 * Uses jsonSchema() wrapper (matching MCP tool format) instead of Zod schemas
 * to ensure compatibility with Anthropic's Tool Search deferLoading feature
 */

import { jsonSchema } from 'ai'
import { createServerSupabaseClient } from '@/lib/supabase/server'

/**
 * Creates the update_user_preference custom tool for the AI agent
 * Allows the agent to update user preferences when explicitly asked by the user
 * @param userId - The authenticated user's ID
 * @returns Tool definition for updating user preferences
 */
export function createUpdateUserPreferenceTool(userId: string) {
  return {
    description:
      "Update a user's preference. Use this when the user asks you to remember something about their analysis style, favorite players, or general preferences. REQUIRED: You must provide preference_type (one of: analysis_style, favorite_players, preference_tag, custom), value (string), and action (one of: set, add, remove).",
    inputSchema: jsonSchema({
      type: 'object',
      properties: {
        preference_type: {
          type: 'string',
          description:
            'Type of preference: analysis_style, favorite_players, preference_tag, or custom'
        },
        value: { type: 'string', description: 'The preference value to set' },
        action: {
          type: 'string',
          description: 'Action: set, add, or remove. Default is set'
        }
      },
      required: ['preference_type', 'value', 'action'],
      additionalProperties: false
    }),
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    execute: async (args: any) => {
      console.log(
        '[update_user_preference] RAW ARGS:',
        JSON.stringify(args, null, 2)
      )

      // Handle different AI providers sending different parameter names
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const argsObj = args as any
      let preference_type =
        argsObj.preference_type || argsObj.field || argsObj.type
      const value = argsObj.value
      const action = argsObj.action || 'set'
      const key = argsObj.key

      // Convert Gemini-style field names to our schema
      if (
        argsObj.field === 'preferred_analysis_style' ||
        argsObj.field === 'analysis_style'
      ) {
        preference_type = 'analysis_style'
      }

      console.log('[update_user_preference] Normalized params:', {
        preference_type,
        key,
        value,
        action
      })
      const supabase = await createServerSupabaseClient()

      // Ensure user preferences record exists
      let { data: existing } = await supabase
        .from('user_preferences')
        .select('*')
        .eq('user_id', userId)
        .single()

      if (!existing) {
        // Insert new record and refetch it
        const { error: insertError } = await supabase
          .from('user_preferences')
          .insert({ user_id: userId })

        if (insertError) {
          console.error('[update_user_preference] Insert error:', insertError)
          return { success: false, error: insertError.message }
        }

        // Refetch the newly created record
        const { data: refetched } = await supabase
          .from('user_preferences')
          .select('*')
          .eq('user_id', userId)
          .single()

        existing = refetched
      }

      // Build update object based on preference_type
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const update: any = {}

      switch (preference_type) {
        case 'analysis_style':
          update.analysis_style = value
          break

        case 'favorite_players':
          if (action === 'add') {
            update.favorite_players = [
              ...(existing?.favorite_players || []),
              ...(Array.isArray(value) ? value : [value])
            ]
          } else if (action === 'remove') {
            update.favorite_players = (existing?.favorite_players || []).filter(
              (p: string) => {
                const valuesToRemove = Array.isArray(value) ? value : [value]
                return !valuesToRemove.includes(p)
              }
            )
          } else {
            update.favorite_players = Array.isArray(value) ? value : [value]
          }
          break

        case 'preference_tag':
          if (action === 'add') {
            update.preference_tags = [
              ...(existing?.preference_tags || []),
              ...(Array.isArray(value) ? value : [value])
            ]
          } else if (action === 'remove') {
            update.preference_tags = (existing?.preference_tags || []).filter(
              (t: string) => {
                const valuesToRemove = Array.isArray(value) ? value : [value]
                return !valuesToRemove.includes(t)
              }
            )
          } else {
            update.preference_tags = Array.isArray(value) ? value : [value]
          }
          break

        case 'custom':
          if (!key) {
            return {
              success: false,
              error: 'key parameter is required for custom preference type'
            }
          }
          const customPrefs = existing?.custom_preferences || {}
          customPrefs[key] = value
          update.custom_preferences = customPrefs
          break
      }

      console.log('[update_user_preference] Updating with:', update)

      const { error } = await supabase
        .from('user_preferences')
        .update(update)
        .eq('user_id', userId)

      if (error) {
        console.error('[update_user_preference] Update error:', error)
        return { success: false, error: error.message }
      }

      console.log('[update_user_preference] Success! Updated:', update)
      return { success: true, updated: update }
    }
  }
}

/**
 * Creates the add_connected_league custom tool for the AI agent
 * Allows the agent to save a Sleeper league to the user's connected leagues
 * @param userId - The authenticated user's ID
 * @returns Tool definition for adding a connected league
 */
export function createAddConnectedLeagueTool(userId: string) {
  return {
    description:
      "Add a Sleeper league to the user's connected leagues. Use this when the user shares their league ID or you fetch their leagues via Sleeper tools.",
    inputSchema: jsonSchema({
      type: 'object',
      properties: {
        league_id: { type: 'string', description: 'The Sleeper league ID' },
        league_name: {
          type: 'string',
          description: 'The name of the league'
        },
        scoring_format: {
          type: 'string',
          description: "e.g., 'PPR', 'Half-PPR', 'Standard', 'Superflex'"
        },
        season: {
          type: 'number',
          description: 'The season year (e.g., 2025)'
        },
        set_as_primary: {
          type: 'boolean',
          default: false,
          description: "Whether this should be the user's primary league"
        }
      },
      required: [
        'league_id',
        'league_name',
        'scoring_format',
        'season',
        'set_as_primary'
      ],
      additionalProperties: false
    }),
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    execute: async (args: any) => {
      const {
        league_id,
        league_name,
        scoring_format,
        season,
        set_as_primary = false
      } = args
      const supabase = await createServerSupabaseClient()

      // Get existing preferences
      const { data: existing } = await supabase
        .from('user_preferences')
        .select('*')
        .eq('user_id', userId)
        .single()

      const connectedLeagues = existing?.connected_leagues || []

      // Check if league already exists
      const existingIndex = connectedLeagues.findIndex(
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        (l: any) => l.league_id === league_id
      )

      const newLeague = {
        league_id,
        name: league_name,
        scoring_format,
        season,
        is_primary: set_as_primary
      }

      if (existingIndex >= 0) {
        // Update existing league
        connectedLeagues[existingIndex] = newLeague
      } else {
        // Add new league
        connectedLeagues.push(newLeague)
      }

      // If setting as primary, unset is_primary on other leagues
      if (set_as_primary) {
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        connectedLeagues.forEach((l: any) => {
          if (l.league_id !== league_id) {
            l.is_primary = false
          }
        })
      }

      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const update: any = { connected_leagues: connectedLeagues }

      if (set_as_primary) {
        update.primary_league_id = league_id
      }

      // Upsert preferences (insert if not exists, update if exists)
      if (!existing) {
        const { error } = await supabase
          .from('user_preferences')
          .insert({ user_id: userId, ...update })

        if (error) {
          return { success: false, error: error.message }
        }
      } else {
        const { error } = await supabase
          .from('user_preferences')
          .update(update)
          .eq('user_id', userId)

        if (error) {
          return { success: false, error: error.message }
        }
      }

      return { success: true, league_added: newLeague }
    }
  }
}

/**
 * Creates the update_roster_notes custom tool for the AI agent
 * Allows the agent to remember the user's team composition, strengths, and needs per league
 * @param userId - The authenticated user's ID
 * @returns Tool definition for updating roster notes
 */
export function createUpdateRosterNotesTool(userId: string) {
  return {
    description:
      "Update roster notes for a specific league. Use this to remember the user's team composition, strengths, and needs.",
    inputSchema: jsonSchema({
      type: 'object',
      properties: {
        league_id: { type: 'string', description: 'The Sleeper league ID' },
        team_name: {
          type: 'string',
          description: "The name of the user's team"
        },
        key_players: {
          type: 'array',
          items: { type: 'string' },
          description: "Array of key players on the user's roster"
        },
        strengths: {
          type: 'array',
          items: { type: 'string' },
          description:
            'Array of team strengths (e.g., "RB depth", "Elite WR1")'
        },
        needs: {
          type: 'array',
          items: { type: 'string' },
          description: 'Array of team needs (e.g., "WR2", "TE upgrade")'
        }
      },
      required: ['league_id'],
      additionalProperties: false
    }),
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    execute: async (args: any) => {
      const { league_id, team_name, key_players, strengths, needs } = args
      const supabase = await createServerSupabaseClient()

      // Get existing preferences
      const { data: existing } = await supabase
        .from('user_preferences')
        .select('*')
        .eq('user_id', userId)
        .single()

      // Get or initialize roster_notes JSONB field
      const rosterNotes = existing?.roster_notes || {}

      // Update notes for this league (merge with existing if present)
      rosterNotes[league_id] = {
        ...rosterNotes[league_id],
        ...(team_name !== undefined && { team_name }),
        ...(key_players !== undefined && { key_players }),
        ...(strengths !== undefined && { strengths }),
        ...(needs !== undefined && { needs })
      }

      // Upsert preferences (insert if not exists, update if exists)
      if (!existing) {
        const { error } = await supabase
          .from('user_preferences')
          .insert({ user_id: userId, roster_notes: rosterNotes })

        if (error) {
          return { success: false, error: error.message }
        }
      } else {
        const { error } = await supabase
          .from('user_preferences')
          .update({ roster_notes: rosterNotes })
          .eq('user_id', userId)

        if (error) {
          return { success: false, error: error.message }
        }
      }

      return { success: true, updated_notes: rosterNotes[league_id] }
    }
  }
}

/**
 * Creates the update_sleeper_connection custom tool for the AI agent
 * Allows the agent to update the user's Sleeper username and primary league connection
 * @param userId - The authenticated user's ID
 * @returns Tool definition for updating Sleeper connection
 */
export function createUpdateSleeperConnectionTool(userId: string) {
  return {
    description:
      "Update the user's Sleeper account connection (username and primary league). Use this when the user tells you their Sleeper username or wants to set their primary league.",
    inputSchema: jsonSchema({
      type: 'object',
      properties: {
        sleeper_username: {
          type: 'string',
          description: "The user's Sleeper platform username"
        },
        selected_league_id: {
          type: 'string',
          description: "ID of the user's primary Sleeper league"
        },
        league_name: {
          type: 'string',
          description: 'Name of the primary Sleeper league'
        }
      },
      additionalProperties: false
    }),
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    execute: async (args: any) => {
      const { sleeper_username, selected_league_id, league_name } = args
      const supabase = await createServerSupabaseClient()

      // Check if at least one field is provided
      if (!sleeper_username && !selected_league_id && !league_name) {
        return {
          success: false,
          error:
            'At least one field (sleeper_username, selected_league_id, or league_name) must be provided'
        }
      }

      // Build update object with only provided fields
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const update: any = {}
      if (sleeper_username !== undefined)
        update.sleeper_username = sleeper_username
      if (selected_league_id !== undefined)
        update.selected_league_id = selected_league_id
      if (league_name !== undefined) update.league_name = league_name
      update.updated_at = new Date().toISOString()

      // Check if user has an onboarding record
      const { data: existing } = await supabase
        .from('user_onboarding')
        .select('*')
        .eq('user_id', userId)
        .single()

      if (!existing) {
        // Insert new onboarding record
        const { error } = await supabase.from('user_onboarding').insert({
          user_id: userId,
          ...update,
          completed: true // Mark as completed since user is providing connection info
        })

        if (error) {
          console.error('[update_sleeper_connection] Insert error:', error)
          return { success: false, error: error.message }
        }
      } else {
        // Update existing onboarding record
        const { error } = await supabase
          .from('user_onboarding')
          .update(update)
          .eq('user_id', userId)

        if (error) {
          console.error('[update_sleeper_connection] Update error:', error)
          return { success: false, error: error.message }
        }
      }

      console.log('[update_sleeper_connection] Success! Updated:', update)
      return { success: true, updated: update }
    }
  }
}
