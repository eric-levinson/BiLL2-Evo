'use client'
import { useEffect } from 'react'
import { usePlaygroundStore } from '@/store'
import { useChatHandler } from '@/hooks/useChatHandler'
import { useRouter } from 'next/navigation'
import { motion } from 'framer-motion'
import dayjs from 'dayjs'
import relativeTime from 'dayjs/plugin/relativeTime'
import { supabase } from '@/lib/supabase/client'
import { getUserSessions } from '@/lib/supabase/sessions'
import type { SessionEntry } from '@/types/playground'

dayjs.extend(relativeTime)

const SessionsList = () => {
  const { sessionsData, isSessionsLoading, setSessionsData, setIsSessionsLoading } = usePlaygroundStore()
  const { sessionId } = useChatHandler()
  const router = useRouter()

  // Load user sessions on component mount
  useEffect(() => {
    const loadSessions = async () => {
      setIsSessionsLoading(true)
      try {
        // Get current user
        const {
          data: { user },
          error: userError
        } = await supabase.auth.getUser()

        if (userError || !user) {
          console.warn('No user found, skipping session load:', userError)
          setSessionsData([])
          return
        }

        // Fetch user's sessions
        const sessions = await getUserSessions(user.id)

        // Map ChatSession[] to SessionEntry[]
        const sessionEntries: SessionEntry[] = sessions.map((session) => ({
          session_id: session.id,
          title: session.title,
          created_at: new Date(session.created_at).getTime()
        }))

        setSessionsData(sessionEntries)
      } catch (error) {
        console.error('Error loading sessions:', error)
        setSessionsData([])
      } finally {
        setIsSessionsLoading(false)
      }
    }

    loadSessions()
  }, [setSessionsData, setIsSessionsLoading])

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
