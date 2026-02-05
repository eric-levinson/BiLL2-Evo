'use client'

import { useChat } from '@ai-sdk/react'
import type { UIMessage } from '@ai-sdk/react'
import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState
} from 'react'
import { toast } from 'sonner'
import { useQueryState } from 'nuqs'
import { supabase } from '@/lib/supabase/client'
import { createSession, updateSession } from '@/lib/supabase/sessions'

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
}

const ChatContext = createContext<ChatHandlerValue | null>(null)

/**
 * Provider that creates a single useChat() instance and shares it
 * across all child components via React Context.
 */
export function ChatProvider({ children }: { children: React.ReactNode }) {
  const [sessionId, setSessionId] = useQueryState('session')
  const [input, setInput] = useState('')

  const {
    messages,
    sendMessage: chatSendMessage,
    regenerate,
    stop,
    status,
    error,
    setMessages
  } = useChat({
    // Only pass id when sessionId exists — passing id: undefined causes
    // useChat v3 to recreate the Chat instance on every render
    ...(sessionId ? { id: sessionId } : {}),
    onError: (error: Error) => {
      console.error('Chat error:', error)
      toast.error('Failed to send message. Please try again.')
    },
    onFinish: async ({ message }) => {
      try {
        // Get current user
        const {
          data: { user },
          error: userError
        } = await supabase.auth.getUser()
        if (userError || !user) {
          console.warn('No user found, skipping session save:', userError)
          return
        }

        // Build updated messages array with the new message
        const updatedMessages = [...messages, message]

        // If no session exists, create one
        if (!sessionId) {
          // Generate title from first user message (max 50 chars)
          const firstUserMessage = updatedMessages.find(m => m.role === 'user')
          const title =
            (typeof firstUserMessage?.content === 'string'
              ? firstUserMessage.content
              : String(firstUserMessage?.content || 'New Chat')
            ).substring(0, 50) || 'New Chat'

          const newSession = await createSession(
            user.id,
            title,
            updatedMessages
          )
          if (newSession) {
            setSessionId(newSession.id)
          }
        } else {
          // Update existing session
          await updateSession(sessionId, updatedMessages)
        }
      } catch (error) {
        console.error('Error saving chat session:', error)
      }
    }
  })

  const isLoading = status === 'submitted' || status === 'streaming'

  const sendMessage = useCallback(
    async (content: string) => {
      if (!content.trim()) return
      try {
        await chatSendMessage({ text: content.trim() })
      } catch (err) {
        console.error('Error sending message:', err)
        toast.error('Failed to send message')
      }
    },
    [chatSendMessage]
  )

  const clearChat = useCallback(() => {
    setMessages([])
    setSessionId(null)
    setInput('')
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
        sessionId
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
