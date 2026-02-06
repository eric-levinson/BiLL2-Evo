import type { UIMessage } from '@ai-sdk/react'
import { supabase } from '@/lib/supabase/client'

export interface ChatSession {
  id: string
  user_id: string
  title: string
  messages: UIMessage[]
  created_at: string
  updated_at: string
}

// Lightweight type for session listings (without messages)
export interface ChatSessionSummary {
  id: string
  title: string
  created_at: string
}

/**
 * Creates a new chat session for a user
 * @param userId - UUID of the user creating the session
 * @param title - Title for the chat session (usually derived from first message)
 * @param messages - Array of AI SDK UIMessage objects
 * @returns The created session or null if failed
 */
export async function createSession(
  userId: string,
  title: string,
  messages: UIMessage[]
): Promise<ChatSession | null> {
  const { data, error } = await supabase
    .from('chat_sessions')
    .insert({
      user_id: userId,
      title,
      messages
    })
    .select()
    .single()

  if (error) {
    console.error('Error creating session:', error)
    return null
  }

  return data
}

/**
 * Updates an existing chat session with new messages
 * @param sessionId - UUID of the session to update
 * @param messages - Updated array of AI SDK UIMessage objects
 * @returns The updated session or null if failed
 */
export async function updateSession(
  sessionId: string,
  messages: UIMessage[]
): Promise<ChatSession | null> {
  const { data, error } = await supabase
    .from('chat_sessions')
    .update({ messages })
    .eq('id', sessionId)
    .select()
    .single()

  if (error) {
    console.error('Error updating session:', error)
    return null
  }

  return data
}

/**
 * Retrieves a single chat session by ID
 * @param sessionId - UUID of the session to retrieve
 * @returns The session or null if not found
 */
export async function getSession(
  sessionId: string
): Promise<ChatSession | null> {
  const { data, error } = await supabase
    .from('chat_sessions')
    .select('*')
    .eq('id', sessionId)
    .single()

  if (error) {
    console.error('Error fetching session:', error)
    return null
  }

  return data
}

/**
 * Retrieves all chat sessions for a user, sorted by most recent first
 * Only fetches id, title, created_at for efficiency (no messages JSONB)
 * @param userId - UUID of the user whose sessions to retrieve
 * @returns Array of session summaries or empty array if none found
 */
export async function getUserSessions(
  userId: string
): Promise<ChatSessionSummary[]> {
  const { data, error } = await supabase
    .from('chat_sessions')
    .select('id, title, created_at')
    .eq('user_id', userId)
    .order('created_at', { ascending: false })

  if (error) {
    console.error('Error fetching user sessions:', error)
    return []
  }

  return data || []
}

/**
 * Deletes a chat session
 * @param sessionId - UUID of the session to delete
 * @returns True if successful, false otherwise
 */
export async function deleteSession(sessionId: string): Promise<boolean> {
  const { error } = await supabase
    .from('chat_sessions')
    .delete()
    .eq('id', sessionId)

  if (error) {
    console.error('Error deleting session:', error)
    return false
  }

  return true
}
