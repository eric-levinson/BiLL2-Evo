'use client'

import { ComposerPrimitive } from '@assistant-ui/react'
import { Button } from '@/components/ui/button'
import { usePlaygroundStore } from '@/store'
import Icon from '@/components/ui/icon'

const ChatInput = () => {
  const { chatInputRef } = usePlaygroundStore()

  return (
    <ComposerPrimitive.Root className="relative mx-auto mb-1 flex w-full max-w-2xl items-end justify-center gap-x-2 font-geist">
      <ComposerPrimitive.Input
        asChild
        autoFocus
        placeholder="Ask anything"
        className="w-full border border-accent bg-primaryAccent px-4 text-sm text-primary focus:border-accent"
        ref={chatInputRef}
      />
      <ComposerPrimitive.Send asChild>
        <Button
          size="icon"
          className="rounded-xl bg-primary p-5 text-primaryAccent"
        >
          <Icon type="send" color="primaryAccent" />
        </Button>
      </ComposerPrimitive.Send>
    </ComposerPrimitive.Root>
  )
}

export default ChatInput
