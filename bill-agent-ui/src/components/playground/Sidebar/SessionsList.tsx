'use client'
import { usePlaygroundStore } from '@/store'
import { useChatHandler } from '@/hooks/useChatHandler'
import { useRouter } from 'next/navigation'
import { motion } from 'framer-motion'
import dayjs from 'dayjs'
import relativeTime from 'dayjs/plugin/relativeTime'

dayjs.extend(relativeTime)

const SessionsList = () => {
  const { sessionsData, isSessionsLoading } = usePlaygroundStore()
  const { sessionId } = useChatHandler()
  const router = useRouter()

  const handleSessionClick = (id: string) => {
    router.push(`/app?session=${id}`)
  }

  if (isSessionsLoading) {
    return (
      <div className="flex items-center justify-center py-4">
        <div className="h-5 w-5 animate-spin rounded-full border-2 border-primary border-t-transparent" />
      </div>
    )
  }

  if (!sessionsData || sessionsData.length === 0) {
    return (
      <div className="py-4 text-center text-xs text-muted-foreground">
        No previous conversations
      </div>
    )
  }

  return (
    <div className="flex flex-col gap-2">
      {sessionsData.map((session) => {
        const isActive = sessionId === session.session_id
        return (
          <motion.button
            key={session.session_id}
            onClick={() => handleSessionClick(session.session_id)}
            className={`group relative flex cursor-pointer flex-col gap-1 rounded-lg border px-3 py-2 text-left transition-colors ${
              isActive
                ? 'border-primary bg-primary/10'
                : 'border-border bg-background hover:border-primary/50 hover:bg-primary/5'
            }`}
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
          >
            <span
              className={`line-clamp-2 text-xs font-medium ${
                isActive ? 'text-primary' : 'text-foreground'
              }`}
            >
              {session.title}
            </span>
            <span className="text-[10px] text-muted-foreground">
              {dayjs(session.created_at).fromNow()}
            </span>
          </motion.button>
        )
      })}
    </div>
  )
}

export default SessionsList
