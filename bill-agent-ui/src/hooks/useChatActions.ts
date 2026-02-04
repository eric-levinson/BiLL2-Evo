import { useCallback } from 'react'

import { usePlaygroundStore } from '../store'
import { useChatHandler } from './useChatHandler'

const useChatActions = () => {
  const { chatInputRef } = usePlaygroundStore()
  const chatHandler = useChatHandler()

  const focusChatInput = useCallback(() => {
    setTimeout(() => {
      requestAnimationFrame(() => chatInputRef?.current?.focus())
    }, 0)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  // Pass through all chat handler methods and add focusChatInput
  return {
    ...chatHandler,
    focusChatInput
  }
}

export default useChatActions
