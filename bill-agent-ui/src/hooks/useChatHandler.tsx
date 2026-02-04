'use client'

import { useChat } from '@ai-sdk/react'
import { useCallback, useEffect } from 'react'
import { toast } from 'sonner'
import { useQueryState } from 'nuqs'

/**
 * Custom hook that wraps Vercel AI SDK's useChat() to provide
 * chat functionality with the BiLL agent backend.
 *
 * This hook connects to /api/chat endpoint which uses ToolLoopAgent
 * with MCP tools for fantasy football analytics.
 */
export function useChatHandler() {
  const [sessionId, setSessionId] = useQueryState('session')

  // Initialize useChat hook with configuration
  const {
    messages,
    input,
    setInput,
    append,
    reload,
    stop,
    isLoading,
    error,
    setMessages
  } = useChat({
    api: '/api/chat',
    id: sessionId || undefined,
    onError: (error: Error) => {
      console.error('Chat error:', error)
      toast.error('Failed to send message. Please try again.')
    },
    onFinish: (message: { id: string; role: string; content: string }) => {
      // Message completed streaming
      console.log('Message completed:', message.id)
    }
  })

  // Handle sending a new message
  const sendMessage = useCallback(
    async (content: string) => {
      if (!content.trim()) {
        return
      }

      try {
        await append({
          role: 'user',
          content: content.trim()
        })
      } catch (err) {
        console.error('Error sending message:', err)
        toast.error('Failed to send message')
      }
    },
    [append]
  )

  // Clear chat and reset session
  const clearChat = useCallback(() => {
    setMessages([])
    setSessionId(null)
    setInput('')
  }, [setMessages, setSessionId, setInput])

  // Reload last message (retry on error)
  const retryLastMessage = useCallback(() => {
    reload()
  }, [reload])

  // Stop current streaming response
  const stopStreaming = useCallback(() => {
    stop()
  }, [stop])

  // Show error toast if error occurs
  useEffect(() => {
    if (error) {
      toast.error(error.message || 'An error occurred')
    }
  }, [error])

  return {
    // Message state
    messages,
    isLoading,
    error,

    // Input state
    input,
    setInput,

    // Actions
    sendMessage,
    clearChat,
    retryLastMessage,
    stopStreaming,

    // Session management
    sessionId
  }
}

export default useChatHandler
