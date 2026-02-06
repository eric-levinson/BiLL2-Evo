'use client'

import { useChat, Chat } from '@ai-sdk/react'
import type { UIMessage } from '@ai-sdk/react'
import { DefaultChatTransport } from 'ai'
import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState
} from 'react'
import { toast } from 'sonner'
import { useQueryState } from 'nuqs'
import {
  getSession,
  getUserSessions,
  type ChatSessionSummary
} from '@/lib/supabase/sessions'
import { supabase } from '@/lib/supabase/client'
import { usePlaygroundStore } from '@/store'
import type { SessionEntry } from '@/types/playground'

interface ChatHandlerValue {
  messages: UIMessage[]
  isLoading: boolean
  error: Error | undefined
  input: string
  setInput: (value: string) => void
  sendMessage: (content: string) => Promise<void>
  clearChat: () => void
  retryLastMessage: () => void
  stopStreaming: () => void
  sessionId: string | null
  refreshSessions: () => Promise<void>
}

const ChatContext = createContext<ChatHandlerValue | null>(null)

/**
 * Provider that creates a single useChat() instance and shares it
 * across all child components via React Context.
 */
export function ChatProvider({ children }: { children: React.ReactNode }) {
  const [sessionId, setSessionId] = useQueryState('session')
  const [input, setInput] = useState('')
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

  const {
    messages,
    sendMessage: chatSendMessage,
    regenerate,
    stop,
    status,
    error,
    setMessages
  } = useChat({ chat })

  const isLoading = status === 'submitted' || status === 'streaming'

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

  const sendMessage = useCallback(
    async (content: string) => {
      if (!content.trim()) return
      try {
        await chatSendMessage({ text: content.trim() })
        // Refresh sessions after message completes to pick up new/updated sessions
        // Small delay to allow server-side persistence to complete
        setTimeout(() => {
          refreshSessions()
        }, 1000)
      } catch (err) {
        console.error('Error sending message:', err)
        toast.error('Failed to send message')
      }
    },
    [chatSendMessage, refreshSessions]
  )

  const clearChat = useCallback(() => {
    setMessages([])
    setSessionId(null)
    setInput('')
    lastLoadedSessionId.current = null
  }, [setMessages, setSessionId])

  const retryLastMessage = useCallback(() => {
    regenerate()
  }, [regenerate])

  const stopStreaming = useCallback(() => {
    stop()
  }, [stop])

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

  return (
    <ChatContext.Provider
      value={{
        messages,
        isLoading,
        error,
        input,
        setInput,
        sendMessage,
        clearChat,
        retryLastMessage,
        stopStreaming,
        sessionId,
        refreshSessions
      }}
    >
      {children}
    </ChatContext.Provider>
  )
}

/**
 * Hook to access the shared chat state from ChatProvider.
 * Must be used within a ChatProvider.
 */
export function useChatHandler(): ChatHandlerValue {
  const ctx = useContext(ChatContext)
  if (!ctx) {
    throw new Error('useChatHandler must be used within a ChatProvider')
  }
  return ctx
}

export default useChatHandler
