'use client'

import { MessagePrimitive } from '@assistant-ui/react'
import Icon from '@/components/ui/icon'
import { memo } from 'react'

const UserMessage = memo(() => {
  return (
    <MessagePrimitive.Root>
      <div className="flex items-start pt-4 text-start max-md:break-words">
        <div className="flex flex-row gap-x-3">
          <p className="flex items-center gap-x-2 text-sm font-medium text-muted">
            <Icon type="user" size="sm" />
          </p>
          <MessagePrimitive.Parts
            components={{
              Text: ({ text }) => (
                <div className="text-md rounded-lg py-1 font-geist text-secondary">
                  {text}
                </div>
              )
            }}
          />
        </div>
      </div>
    </MessagePrimitive.Root>
  )
})

UserMessage.displayName = 'UserMessage'

export default UserMessage
