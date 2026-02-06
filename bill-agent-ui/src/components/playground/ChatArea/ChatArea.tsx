'use client'

import ChatInputNew from './ChatInput/ChatInputNew'
import MessageAreaNew from './MessageAreaNew'
const ChatArea = () => {
  return (
    <main className="relative m-1.5 flex flex-grow flex-col rounded-xl bg-background">
      <MessageAreaNew />
      <div className="sticky bottom-0 ml-9 px-4 pb-2">
        <ChatInputNew />
      </div>
    </main>
  )
}

export default ChatArea
