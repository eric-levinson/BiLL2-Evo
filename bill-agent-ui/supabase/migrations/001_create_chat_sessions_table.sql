-- Migration: Create chat_sessions table for persisting AI chat conversations
-- Description: Stores chat messages as JSONB with RLS policies to ensure user data isolation

-- Create chat_sessions table
CREATE TABLE IF NOT EXISTS public.chat_sessions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  title TEXT NOT NULL,
  messages JSONB NOT NULL DEFAULT '[]'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Add indexes for performance
CREATE INDEX IF NOT EXISTS idx_chat_sessions_user_id ON public.chat_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_chat_sessions_created_at ON public.chat_sessions(created_at DESC);

-- Create function to auto-update updated_at timestamp
CREATE OR REPLACE FUNCTION public.handle_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger to auto-update updated_at on row update
CREATE TRIGGER set_updated_at
  BEFORE UPDATE ON public.chat_sessions
  FOR EACH ROW
  EXECUTE FUNCTION public.handle_updated_at();

-- Enable Row Level Security
ALTER TABLE public.chat_sessions ENABLE ROW LEVEL SECURITY;

-- RLS Policy: Users can view only their own chat sessions
CREATE POLICY "Users can view their own chat sessions"
  ON public.chat_sessions
  FOR SELECT
  USING (auth.uid() = user_id);

-- RLS Policy: Users can insert their own chat sessions
CREATE POLICY "Users can create their own chat sessions"
  ON public.chat_sessions
  FOR INSERT
  WITH CHECK (auth.uid() = user_id);

-- RLS Policy: Users can update only their own chat sessions
CREATE POLICY "Users can update their own chat sessions"
  ON public.chat_sessions
  FOR UPDATE
  USING (auth.uid() = user_id)
  WITH CHECK (auth.uid() = user_id);

-- RLS Policy: Users can delete only their own chat sessions
CREATE POLICY "Users can delete their own chat sessions"
  ON public.chat_sessions
  FOR DELETE
  USING (auth.uid() = user_id);

-- Add comment to table
COMMENT ON TABLE public.chat_sessions IS 'Stores AI chat conversation sessions with messages in JSONB format';
COMMENT ON COLUMN public.chat_sessions.id IS 'Unique identifier for the chat session';
COMMENT ON COLUMN public.chat_sessions.user_id IS 'Foreign key to auth.users - owner of the chat session';
COMMENT ON COLUMN public.chat_sessions.title IS 'Chat session title (derived from first message)';
COMMENT ON COLUMN public.chat_sessions.messages IS 'Array of chat messages stored as JSONB (AI SDK format)';
COMMENT ON COLUMN public.chat_sessions.created_at IS 'Timestamp when the session was created';
COMMENT ON COLUMN public.chat_sessions.updated_at IS 'Timestamp when the session was last updated (auto-updated via trigger)';
