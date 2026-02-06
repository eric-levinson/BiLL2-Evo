'use client'

import {
  MessagePrimitive,
  useMessage,
  ActionBarPrimitive
} from '@assistant-ui/react'
import Icon from '@/components/ui/icon'
import MarkdownRenderer from '@/components/ui/typography/MarkdownRenderer'
import { usePlaygroundStore } from '@/store'
import AgentThinkingLoader from './Messages/AgentThinkingLoader'
import Tooltip from '@/components/ui/tooltip'
import { memo } from 'react'
import type { ToolCallMessagePartProps } from '@assistant-ui/react'

// Tool call badge component - preserves styling from original ToolComponent
const ToolCallBadge = memo(({ toolName, status }: ToolCallMessagePartProps) => {
  // Determine badge styling based on tool call status
  const isComplete = status?.type === 'complete'
  const isRunning = status?.type === 'running'
  const isIncomplete = status?.type === 'incomplete'

  return (
    <div
      className={`cursor-default rounded-full px-2 py-1.5 text-xs ${
        isIncomplete
          ? 'bg-destructive/20'
          : isComplete
            ? 'bg-accent'
            : isRunning
              ? 'bg-accent/50'
              : 'bg-accent'
      }`}
    >
      <p className="font-dmmono uppercase text-primary/80">{toolName}</p>
    </div>
  )
})
ToolCallBadge.displayName = 'ToolCallBadge'

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

          {/* Render message parts with tool call rendering */}
          <MessagePrimitive.Parts
            components={{
              Text: ({ text }) => <MarkdownRenderer>{text}</MarkdownRenderer>,
              tools: {
                Fallback: ToolCallBadge
              }
            }}
          />

          {/* Action bar for copy and regenerate functionality */}
          <ActionBarPrimitive.Root
            hideWhenRunning
            autohide="not-last"
            className="flex items-center gap-2"
          >
            <Tooltip content="Copy message">
              <ActionBarPrimitive.Copy className="flex items-center justify-center rounded-lg border border-primaryAccent bg-background p-2 transition-colors hover:bg-primaryAccent">
                <Icon type="copy" size="xs" />
              </ActionBarPrimitive.Copy>
            </Tooltip>
            <Tooltip content="Regenerate response">
              <ActionBarPrimitive.Reload className="flex items-center justify-center rounded-lg border border-primaryAccent bg-background p-2 transition-colors hover:bg-primaryAccent">
                <Icon type="refresh" size="xs" />
              </ActionBarPrimitive.Reload>
            </Tooltip>
          </ActionBarPrimitive.Root>
        </div>
      </div>
    </MessagePrimitive.Root>
  )
}

AssistantMessage.displayName = 'AssistantMessage'

export default AssistantMessage
