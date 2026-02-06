'use client'

import { useChat, Chat } from '@ai-sdk/react'
import { DefaultChatTransport } from 'ai'
import { useMemo, useEffect, useCallback, useRef } from 'react'
import { toast } from 'sonner'
import { useQueryState } from 'nuqs'
import { useAISDKRuntime } from '@assistant-ui/react-ai-sdk'
import { AssistantRuntimeProvider } from '@assistant-ui/react'
import {
  getSession,
  getUserSessions,
  type ChatSessionSummary
} from '@/lib/supabase/sessions'
import { supabase } from '@/lib/supabase/client'
import { usePlaygroundStore } from '@/store'
import type { SessionEntry } from '@/types/playground'

/**
 * Hook that creates an AssistantRuntime from the existing AI SDK chat instance.
 * Preserves all session management and Supabase persistence logic.
 */
export function useAssistantRuntime() {
  const [sessionId] = useQueryState('session')
  const lastLoadedSessionId = useRef<string | null>(null)
  const { setSessionsData, setIsSessionsLoading } = usePlaygroundStore()

  // Create a Chat instance with transport that includes sessionId in body
  // This is memoized to prevent recreating on every render
  const chat = useMemo(() => {
    const transport = new DefaultChatTransport({
      api: '/api/chat',
      // Pass sessionId in the body for server-side persistence
      // This is separate from the SDK's `id` which is auto-generated
      body: {
        sessionId: sessionId || undefined
      }
    })

    return new Chat({
      // Only pass id when sessionId exists — passing id: undefined causes
      // useChat v3 to recreate the Chat instance on every render
      ...(sessionId ? { id: sessionId } : {}),
      transport,
      onError: (error: Error) => {
        console.error('Chat error:', error)
        toast.error('Failed to send message. Please try again.')
      }
      // NO onFinish callback here - server handles persistence via consumeStream
    })
  }, [sessionId])

  const chatHelpers = useChat({ chat })

  const { messages, error, setMessages } = chatHelpers

  // Function to refresh sessions list from Supabase
  const refreshSessions = useCallback(async () => {
    try {
      const {
        data: { user },
        error: userError
      } = await supabase.auth.getUser()

      if (userError || !user) {
        console.warn('No user found, skipping session refresh')
        return
      }

      const sessions: ChatSessionSummary[] = await getUserSessions(user.id)
      const sessionEntries: SessionEntry[] = sessions.map((session) => ({
        session_id: session.id,
        title: session.title,
        created_at: new Date(session.created_at).getTime()
      }))

      setSessionsData(sessionEntries)
    } catch (error) {
      console.error('Error refreshing sessions:', error)
    }
  }, [setSessionsData])

  // Show error toast on error
  useEffect(() => {
    if (error) {
      toast.error(error.message || 'An error occurred')
    }
  }, [error])

  // Load session messages when sessionId changes
  useEffect(() => {
    // Skip if no sessionId or if we already loaded this session
    if (!sessionId || sessionId === lastLoadedSessionId.current) {
      return
    }

    const loadSession = async () => {
      setIsSessionsLoading(true)
      try {
        const session = await getSession(sessionId)
        if (session && session.messages) {
          // Update messages from loaded session
          setMessages(session.messages)
          // Track that we loaded this session to prevent duplicate loads
          lastLoadedSessionId.current = sessionId
        }
      } catch (err) {
        console.error('Error loading session:', err)
        toast.error('Failed to load chat session')
      } finally {
        setIsSessionsLoading(false)
      }
    }

    loadSession()
  }, [sessionId, setMessages, setIsSessionsLoading])

  // Wrap the AI SDK chat with assistant-ui runtime adapter
  const runtime = useAISDKRuntime(chatHelpers)

  return {
    runtime,
    sessionId,
    refreshSessions,
    messages
  }
}

/**
 * Provider that creates an AssistantRuntime from the AI SDK chat instance
 * and makes it available to all assistant-ui components.
 */
export function AssistantRuntimeProviderWrapper({
  children
}: {
  children: React.ReactNode
}) {
  const { runtime } = useAssistantRuntime()

  return (
    <AssistantRuntimeProvider runtime={runtime}>
      {children}
    </AssistantRuntimeProvider>
  )
}

export default useAssistantRuntime
