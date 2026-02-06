'use client'

import { MessagePrimitive, useMessage } from '@assistant-ui/react'
import Icon from '@/components/ui/icon'
import MarkdownRenderer from '@/components/ui/typography/MarkdownRenderer'
import { usePlaygroundStore } from '@/store'
import AgentThinkingLoader from './Messages/AgentThinkingLoader'

const AssistantMessage = () => {
  const { streamingErrorMessage } = usePlaygroundStore()
  const message = useMessage({ optional: true })
  const hasContent = message?.content && message.content.length > 0
  const isRunning = message?.status?.type === 'running'

  return (
    <MessagePrimitive.Root>
      <div className="flex flex-row items-start gap-4 font-geist">
        <div className="flex-shrink-0">
          <Icon type="agent" size="sm" />
        </div>
        <div className="flex w-full flex-col gap-4">
          {/* Show error state */}
          <MessagePrimitive.Error>
            <p className="text-destructive">
              Oops! Something went wrong while streaming.{' '}
              {streamingErrorMessage ? (
                <>{streamingErrorMessage}</>
              ) : (
                'Please try refreshing the page or try again later.'
              )}
            </p>
          </MessagePrimitive.Error>

          {/* Show thinking loader when streaming but no content yet */}
          {!hasContent && isRunning && (
            <div className="mt-2">
              <AgentThinkingLoader />
            </div>
          )}

          {/* Render text content with markdown */}
          <MessagePrimitive.Parts
            components={{
              Text: ({ text }) => <MarkdownRenderer>{text}</MarkdownRenderer>
            }}
          />
        </div>
      </div>
    </MessagePrimitive.Root>
  )
}

AssistantMessage.displayName = 'AssistantMessage'

export default AssistantMessage
