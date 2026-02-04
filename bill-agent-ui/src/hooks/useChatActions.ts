import { useCallback } from 'react'

import { usePlaygroundStore } from '../store'

import { type PlaygroundChatMessage } from '@/types/playground'
// TODO: Remove in cleanup phase - Agno API client deleted
// import {
//   getPlaygroundAgentsAPI,
//   getPlaygroundStatusAPI,
//   getPlaygroundTeamsAPI
// } from '@/api/playground'
import { useQueryState } from 'nuqs'

const useChatActions = () => {
  const { chatInputRef } = usePlaygroundStore()
  const [, setSessionId] = useQueryState('session')
  const setMessages = usePlaygroundStore((state) => state.setMessages)

  const getAgents = useCallback(async () => {
    // TODO: Remove - Agno API deleted
    // try {
    //   const agents = await getPlaygroundAgentsAPI(selectedEndpoint)
    //   return agents
    // } catch {
    //   toast.error('Error fetching agents')
    //   return []
    // }
    return []
  }, [])

  const getTeams = useCallback(async () => {
    // TODO: Remove - Agno API deleted
    // try {
    //   const teams = await getPlaygroundTeamsAPI(selectedEndpoint)
    //   return teams
    // } catch {
    //   toast.error('Error fetching teams')
    //   return []
    // }
    return []
  }, [])

  const clearChat = useCallback(() => {
    setMessages([])
    setSessionId(null)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const focusChatInput = useCallback(() => {
    setTimeout(() => {
      requestAnimationFrame(() => chatInputRef?.current?.focus())
    }, 0)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const addMessage = useCallback(
    (message: PlaygroundChatMessage) => {
      setMessages((prevMessages) => [...prevMessages, message])
    },
    [setMessages]
  )

  const initializePlayground = useCallback(async () => {
    // TODO: Remove - Agno Playground initialization no longer needed with new useChat system
    // This function was used to initialize Agno agents/teams and endpoint status
    // New system uses a single /api/chat endpoint - no initialization required
    return { agents: [], teams: [] }
  }, [])

  return {
    clearChat,
    addMessage,
    getAgents,
    focusChatInput,
    getTeams,
    initializePlayground
  }
}

export default useChatActions
