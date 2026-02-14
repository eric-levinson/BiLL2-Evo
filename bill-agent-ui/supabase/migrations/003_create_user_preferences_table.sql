-- Migration: Create user_preferences table for cross-session memory
-- Description: Stores user preferences, connected Sleeper leagues, favorite players, and analysis style

-- Create user_preferences table
CREATE TABLE IF NOT EXISTS public.user_preferences (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,

  -- Sleeper Integration
  connected_leagues JSONB NOT NULL DEFAULT '[]'::jsonb,
  -- Structure: [{ league_id: string, name: string, scoring_format: string, season: number, is_primary: boolean }]

  primary_league_id TEXT, -- Most frequently referenced league

  -- User Context
  favorite_players TEXT[] NOT NULL DEFAULT '{}', -- Array of player names or Sleeper IDs
  roster_notes JSONB NOT NULL DEFAULT '{}'::jsonb,
  -- Structure: { [league_id]: { team_name: string, key_players: string[], strengths: string[], needs: string[] } }

  -- Analysis Preferences
  analysis_style TEXT NOT NULL DEFAULT 'balanced', -- 'data-heavy', 'narrative', 'concise', 'balanced'
  preference_tags TEXT[] NOT NULL DEFAULT '{}', -- ['dynasty-focused', 'redraft', 'best-ball', 'dfs', etc.]

  -- Flexible Storage
  custom_preferences JSONB NOT NULL DEFAULT '{}'::jsonb, -- Key-value store for any other preferences

  -- Metadata
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Add indexes for performance
CREATE UNIQUE INDEX IF NOT EXISTS idx_user_preferences_user_id ON public.user_preferences(user_id);

-- Create trigger to auto-update updated_at on row update
-- Note: Reuses the handle_updated_at() function created in 001_create_chat_sessions_table.sql
CREATE TRIGGER set_updated_at
  BEFORE UPDATE ON public.user_preferences
  FOR EACH ROW
  EXECUTE FUNCTION public.handle_updated_at();

-- Enable Row Level Security
ALTER TABLE public.user_preferences ENABLE ROW LEVEL SECURITY;

-- RLS Policy: Users can view only their own preferences
CREATE POLICY "Users can view their own preferences"
  ON public.user_preferences
  FOR SELECT
  USING (auth.uid() = user_id);

-- RLS Policy: Users can insert their own preferences
CREATE POLICY "Users can create their own preferences"
  ON public.user_preferences
  FOR INSERT
  WITH CHECK (auth.uid() = user_id);

-- RLS Policy: Users can update only their own preferences
CREATE POLICY "Users can update their own preferences"
  ON public.user_preferences
  FOR UPDATE
  USING (auth.uid() = user_id)
  WITH CHECK (auth.uid() = user_id);

-- RLS Policy: Users can delete only their own preferences
CREATE POLICY "Users can delete their own preferences"
  ON public.user_preferences
  FOR DELETE
  USING (auth.uid() = user_id);

-- Add comments to table
COMMENT ON TABLE public.user_preferences IS 'Stores user preferences for cross-session memory including connected leagues, favorite players, and analysis style';
COMMENT ON COLUMN public.user_preferences.id IS 'Unique identifier for the preference record';
COMMENT ON COLUMN public.user_preferences.user_id IS 'Foreign key to auth.users - owner of the preferences';
COMMENT ON COLUMN public.user_preferences.connected_leagues IS 'JSONB array of connected Sleeper leagues with scoring format and season info';
COMMENT ON COLUMN public.user_preferences.primary_league_id IS 'ID of the user''s primary/most frequently referenced league';
COMMENT ON COLUMN public.user_preferences.favorite_players IS 'Array of favorite player names or Sleeper IDs';
COMMENT ON COLUMN public.user_preferences.roster_notes IS 'JSONB object keyed by league_id containing roster composition, strengths, and needs';
COMMENT ON COLUMN public.user_preferences.analysis_style IS 'User''s preferred analysis style: data-heavy, narrative, concise, or balanced';
COMMENT ON COLUMN public.user_preferences.preference_tags IS 'Array of preference tags like dynasty-focused, redraft, best-ball, etc.';
COMMENT ON COLUMN public.user_preferences.custom_preferences IS 'JSONB key-value store for flexible preference storage';
COMMENT ON COLUMN public.user_preferences.created_at IS 'Timestamp when the preference record was created';
COMMENT ON COLUMN public.user_preferences.updated_at IS 'Timestamp when the preference record was last updated (auto-updated via trigger)';
