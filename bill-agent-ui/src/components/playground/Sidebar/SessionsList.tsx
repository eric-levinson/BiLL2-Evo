'use client'
import { useEffect, useState } from 'react'
import { usePlaygroundStore } from '@/store'
import { useAssistantSession } from '@/hooks/useAssistantRuntime'
import { useRouter } from 'next/navigation'
import { motion } from 'framer-motion'
import { Trash } from 'lucide-react'
import dayjs from 'dayjs'
import relativeTime from 'dayjs/plugin/relativeTime'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { deleteSession } from '@/lib/supabase/sessions'
import { toast } from 'sonner'

dayjs.extend(relativeTime)

const SessionsList = () => {
  const { sessionsData, isSessionsLoading } = usePlaygroundStore()
  const { sessionId, refreshSessions } = useAssistantSession()
  const router = useRouter()
  const [isDialogOpen, setIsDialogOpen] = useState(false)
  const [sessionToDelete, setSessionToDelete] = useState<string | null>(null)

  // Load user sessions on component mount
  useEffect(() => {
    refreshSessions()
  }, [refreshSessions])

  const handleSessionClick = (id: string) => {
    router.push(`/app?session=${id}`)
  }

  const handleDeleteClick = (e: React.MouseEvent, sessionId: string) => {
    e.stopPropagation()
    setSessionToDelete(sessionId)
    setIsDialogOpen(true)
  }

  const handleConfirmDelete = async () => {
    if (!sessionToDelete) return

    try {
      const success = await deleteSession(sessionToDelete)

      if (success) {
        toast.success('Conversation deleted successfully')

        // If deleting the currently active session, redirect to /app without session
        if (sessionId === sessionToDelete) {
          router.push('/app')
        }

        // Refresh the sessions list
        await refreshSessions()
      } else {
        toast.error('Failed to delete conversation. Please try again.')
      }
    } catch (error) {
      console.error('Error deleting session:', error)
      toast.error('An error occurred while deleting the conversation.')
    } finally {
      setIsDialogOpen(false)
      setSessionToDelete(null)
    }
  }

  const handleCancelDelete = () => {
    setIsDialogOpen(false)
    setSessionToDelete(null)
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
    <>
      <div className="flex flex-col gap-2">
        {sessionsData.map((session) => {
          const isActive = sessionId === session.session_id
          return (
            <motion.div
              key={session.session_id}
              role="button"
              tabIndex={0}
              onClick={() => handleSessionClick(session.session_id)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                  e.preventDefault()
                  handleSessionClick(session.session_id)
                }
              }}
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
                <Trash className="text-muted-foreground h-3.5 w-3.5 hover:text-destructive" />
              </button>
            </motion.div>
          )
        })}
      </div>

      <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Delete Conversation</DialogTitle>
            <DialogDescription>
              Are you sure you want to delete this conversation? This action
              cannot be undone and all messages will be permanently removed.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={handleCancelDelete}>
              Cancel
            </Button>
            <Button variant="destructive" onClick={handleConfirmDelete}>
              Delete
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  )
}

export default SessionsList
