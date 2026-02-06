import { useCallback } from 'react'

import { usePlaygroundStore } from '../store'
import { useAssistantSession } from './useAssistantRuntime'

const useChatActions = () => {
  const { chatInputRef } = usePlaygroundStore()
  const { sessionId, refreshSessions, messages, clearChat } =
    useAssistantSession()

  const focusChatInput = useCallback(() => {
    setTimeout(() => {
      requestAnimationFrame(() => chatInputRef?.current?.focus())
    }, 0)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  // Provide session-related methods and add focusChatInput
  return {
    sessionId,
    refreshSessions,
    messages,
    clearChat,
    focusChatInput
  }
}

export default useChatActions
