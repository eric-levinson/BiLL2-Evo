-- Migration: Create user_onboarding table for tracking user onboarding flow
-- Description: Stores user onboarding progress including Sleeper league connection with RLS policies

-- Create user_onboarding table
CREATE TABLE IF NOT EXISTS public.user_onboarding (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  completed BOOLEAN NOT NULL DEFAULT false,
  sleeper_username TEXT,
  selected_league_id TEXT,
  league_name TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Add indexes for performance
CREATE INDEX IF NOT EXISTS idx_user_onboarding_user_id ON public.user_onboarding(user_id);

-- Create trigger to auto-update updated_at on row update
-- Note: Reuses the handle_updated_at() function created in 001_create_chat_sessions_table.sql
CREATE TRIGGER set_updated_at
  BEFORE UPDATE ON public.user_onboarding
  FOR EACH ROW
  EXECUTE FUNCTION public.handle_updated_at();

-- Enable Row Level Security
ALTER TABLE public.user_onboarding ENABLE ROW LEVEL SECURITY;

-- RLS Policy: Users can view only their own onboarding data
CREATE POLICY "Users can view their own onboarding data"
  ON public.user_onboarding
  FOR SELECT
  USING (auth.uid() = user_id);

-- RLS Policy: Users can insert their own onboarding data
CREATE POLICY "Users can create their own onboarding data"
  ON public.user_onboarding
  FOR INSERT
  WITH CHECK (auth.uid() = user_id);

-- RLS Policy: Users can update only their own onboarding data
CREATE POLICY "Users can update their own onboarding data"
  ON public.user_onboarding
  FOR UPDATE
  USING (auth.uid() = user_id)
  WITH CHECK (auth.uid() = user_id);

-- RLS Policy: Users can delete only their own onboarding data
CREATE POLICY "Users can delete their own onboarding data"
  ON public.user_onboarding
  FOR DELETE
  USING (auth.uid() = user_id);

-- Add comment to table
COMMENT ON TABLE public.user_onboarding IS 'Stores user onboarding progress and Sleeper league connection details';
COMMENT ON COLUMN public.user_onboarding.id IS 'Unique identifier for the onboarding record';
COMMENT ON COLUMN public.user_onboarding.user_id IS 'Foreign key to auth.users - owner of the onboarding record';
COMMENT ON COLUMN public.user_onboarding.completed IS 'Boolean flag indicating if onboarding is complete';
COMMENT ON COLUMN public.user_onboarding.sleeper_username IS 'User''s Sleeper platform username';
COMMENT ON COLUMN public.user_onboarding.selected_league_id IS 'ID of the selected Sleeper league';
COMMENT ON COLUMN public.user_onboarding.league_name IS 'Name of the selected Sleeper league';
COMMENT ON COLUMN public.user_onboarding.created_at IS 'Timestamp when the onboarding record was created';
COMMENT ON COLUMN public.user_onboarding.updated_at IS 'Timestamp when the onboarding record was last updated (auto-updated via trigger)';
