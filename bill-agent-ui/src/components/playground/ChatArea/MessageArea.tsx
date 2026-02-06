'use client'

import { ThreadPrimitive, useThreadViewport } from '@assistant-ui/react'
import ChatBlankState from './Messages/ChatBlankState'
import { Button } from '@/components/ui/button'
import Icon from '@/components/ui/icon'
import { motion, AnimatePresence } from 'framer-motion'
import AssistantMessage from './AssistantMessage'
import UserMessage from './UserMessage'

const MessageArea = () => {
  return (
    <ThreadPrimitive.Root className="relative mb-4 flex max-h-[calc(100vh-64px)] min-h-0 flex-grow flex-col">
      <ThreadPrimitive.Viewport className="flex min-h-full flex-col justify-center">
        <div className="mx-auto w-full max-w-2xl space-y-9 px-4 pb-4">
          <ThreadPrimitive.Empty>
            <ChatBlankState />
          </ThreadPrimitive.Empty>
          <ThreadPrimitive.Messages
            components={{
              UserMessage: UserMessage,
              AssistantMessage: AssistantMessage
            }}
          />
        </div>
      </ThreadPrimitive.Viewport>
      <ScrollToBottomButton />
    </ThreadPrimitive.Root>
  )
}

const ScrollToBottomButton = () => {
  const isAtBottom = useThreadViewport((s) => s.isAtBottom)

  return (
    <AnimatePresence>
      {!isAtBottom && (
        <ThreadPrimitive.ScrollToBottom asChild>
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 20 }}
            transition={{ duration: 0.3, ease: 'easeInOut' }}
            className="absolute bottom-4 left-1/2 -translate-x-1/2"
          >
            <Button
              type="button"
              size="icon"
              variant="secondary"
              className="border border-border bg-background text-primary shadow-md transition-shadow duration-300 hover:bg-background-secondary"
            >
              <Icon type="arrow-down" size="xs" />
            </Button>
          </motion.div>
        </ThreadPrimitive.ScrollToBottom>
      )}
    </AnimatePresence>
  )
}

export default MessageArea
