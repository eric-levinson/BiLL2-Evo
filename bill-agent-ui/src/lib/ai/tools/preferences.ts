/**
 * Custom AI SDK tools for user preference management
 * Provides tools for updating user preferences, managing connected Sleeper leagues,
 * and maintaining roster notes via the BiLL AI agent
 */

import { tool } from 'ai'
import { z } from 'zod'
import { createServerSupabaseClient } from '@/lib/supabase/server'

/**
 * Creates the update_user_preference custom tool for the AI agent
 * Allows the agent to update user preferences when explicitly asked by the user
 * @param userId - The authenticated user's ID
 * @returns Tool definition for updating user preferences
 */
export function createUpdateUserPreferenceTool(userId: string) {
  const parametersSchema = z.object({
    preference_type: z
      .string()
      .describe('Type of preference: analysis_style, favorite_players, preference_tag, or custom'),
    value: z
      .string()
      .describe('The preference value to set'),
    action: z
      .string()
      .describe('Action: set, add, or remove. Default is set')
  })

  return tool({
    description:
      "Update a user's preference. Use this when the user asks you to remember something about their analysis style, favorite players, or general preferences. REQUIRED: You must provide preference_type (one of: analysis_style, favorite_players, preference_tag, custom), value (string), and action (one of: set, add, remove).",
    parameters: parametersSchema,
    // @ts-expect-error - AI SDK tool() typing issue with execute function inference
    execute: async (args: z.infer<typeof parametersSchema>) => {
      console.log('[update_user_preference] RAW ARGS:', JSON.stringify(args, null, 2))

      // Handle different AI providers sending different parameter names
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const argsObj = args as any
      let preference_type = argsObj.preference_type || argsObj.field || argsObj.type
      let value = argsObj.value
      let action = argsObj.action || 'set'
      let key = argsObj.key

      // Convert Gemini-style field names to our schema
      if (argsObj.field === 'preferred_analysis_style' || argsObj.field === 'analysis_style') {
        preference_type = 'analysis_style'
      }

      console.log('[update_user_preference] Normalized params:', { preference_type, key, value, action })
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
      let update: any = {}

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
            update.favorite_players = (
              existing?.favorite_players || []
            ).filter((p: string) => {
              const valuesToRemove = Array.isArray(value) ? value : [value]
              return !valuesToRemove.includes(p)
            })
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
  })
}

/**
 * Creates the add_connected_league custom tool for the AI agent
 * Allows the agent to save a Sleeper league to the user's connected leagues
 * @param userId - The authenticated user's ID
 * @returns Tool definition for adding a connected league
 */
export function createAddConnectedLeagueTool(userId: string) {
  const parametersSchema = z.object({
    league_id: z.string().describe('The Sleeper league ID'),
    league_name: z.string().describe('The name of the league'),
    scoring_format: z
      .string()
      .describe("e.g., 'PPR', 'Half-PPR', 'Standard', 'Superflex'"),
    season: z.number().describe('The season year (e.g., 2025)'),
    set_as_primary: z
      .boolean()
      .default(false)
      .describe("Whether this should be the user's primary league")
  })

  return tool({
    description:
      "Add a Sleeper league to the user's connected leagues. Use this when the user shares their league ID or you fetch their leagues via Sleeper tools.",
    parameters: parametersSchema,
    // @ts-expect-error - AI SDK tool() typing issue with execute function inference
    execute: async ({
      league_id,
      league_name,
      scoring_format,
      season,
      set_as_primary
    }: z.infer<typeof parametersSchema>) => {
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
  })
}

/**
 * Creates the update_roster_notes custom tool for the AI agent
 * Allows the agent to remember the user's team composition, strengths, and needs per league
 * @param userId - The authenticated user's ID
 * @returns Tool definition for updating roster notes
 */
export function createUpdateRosterNotesTool(userId: string) {
  const parametersSchema = z.object({
    league_id: z.string().describe('The Sleeper league ID'),
    team_name: z.string().optional().describe('The name of the user\'s team'),
    key_players: z
      .array(z.string())
      .optional()
      .describe('Array of key players on the user\'s roster'),
    strengths: z
      .array(z.string())
      .optional()
      .describe('Array of team strengths (e.g., "RB depth", "Elite WR1")'),
    needs: z
      .array(z.string())
      .optional()
      .describe('Array of team needs (e.g., "WR2", "TE upgrade")')
  })

  return tool({
    description:
      "Update roster notes for a specific league. Use this to remember the user's team composition, strengths, and needs.",
    parameters: parametersSchema,
    // @ts-expect-error - AI SDK tool() typing issue with execute function inference
    execute: async ({
      league_id,
      team_name,
      key_players,
      strengths,
      needs
    }: z.infer<typeof parametersSchema>) => {
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
  })
}

/**
 * Creates the update_sleeper_connection custom tool for the AI agent
 * Allows the agent to update the user's Sleeper username and primary league connection
 * @param userId - The authenticated user's ID
 * @returns Tool definition for updating Sleeper connection
 */
export function createUpdateSleeperConnectionTool(userId: string) {
  const parametersSchema = z.object({
    sleeper_username: z
      .string()
      .optional()
      .describe('The user\'s Sleeper platform username'),
    selected_league_id: z
      .string()
      .optional()
      .describe('ID of the user\'s primary Sleeper league'),
    league_name: z
      .string()
      .optional()
      .describe('Name of the primary Sleeper league')
  })

  return tool({
    description:
      "Update the user's Sleeper account connection (username and primary league). Use this when the user tells you their Sleeper username or wants to set their primary league.",
    parameters: parametersSchema,
    // @ts-expect-error - AI SDK tool() typing issue with execute function inference
    execute: async ({
      sleeper_username,
      selected_league_id,
      league_name
    }: z.infer<typeof parametersSchema>) => {
      const supabase = await createServerSupabaseClient()

      // Check if at least one field is provided
      if (!sleeper_username && !selected_league_id && !league_name) {
        return {
          success: false,
          error: 'At least one field (sleeper_username, selected_league_id, or league_name) must be provided'
        }
      }

      // Build update object with only provided fields
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const update: any = {}
      if (sleeper_username !== undefined) update.sleeper_username = sleeper_username
      if (selected_league_id !== undefined) update.selected_league_id = selected_league_id
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
        const { error } = await supabase
          .from('user_onboarding')
          .insert({
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
  })
}
