'use client'
import { useEffect } from 'react'
import { usePlaygroundStore } from '@/store'
import { useAssistantSession } from '@/hooks/useAssistantRuntime'
import { useRouter } from 'next/navigation'
import { motion } from 'framer-motion'
import { Trash } from 'lucide-react'
import dayjs from 'dayjs'
import relativeTime from 'dayjs/plugin/relativeTime'

dayjs.extend(relativeTime)

const SessionsList = () => {
  const { sessionsData, isSessionsLoading } = usePlaygroundStore()
  const { sessionId, refreshSessions } = useAssistantSession()
  const router = useRouter()

  // Load user sessions on component mount
  useEffect(() => {
    refreshSessions()
  }, [refreshSessions])

  const handleSessionClick = (id: string) => {
    router.push(`/app?session=${id}`)
  }

  const handleDeleteClick = (
    e: React.MouseEvent,
    sessionId: string
  ) => {
    e.stopPropagation()
    // TODO: Open confirmation dialog (will be implemented in next subtask)
    console.log('Delete session:', sessionId)
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
      <div className="text-muted-foreground py-4 text-center text-xs">
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
            <span className="text-muted-foreground text-[10px]">
              {dayjs(session.created_at).fromNow()}
            </span>

            {/* Delete button - appears on hover */}
            <button
              onClick={(e) => handleDeleteClick(e, session.session_id)}
              className="absolute right-2 top-2 rounded-md p-1 opacity-0 transition-opacity hover:bg-destructive/10 group-hover:opacity-100"
              aria-label="Delete conversation"
            >
              <Trash className="h-3.5 w-3.5 text-muted-foreground hover:text-destructive" />
            </button>
          </motion.button>
        )
      })}
    </div>
  )
}

export default SessionsList
