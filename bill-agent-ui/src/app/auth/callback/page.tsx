"use client"

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import supabase from '@/lib/supabase/client'

export default function AuthCallbackPage() {
  const router = useRouter()

  useEffect(() => {
    async function handle() {
      try {
        // The Supabase browser client normally detects OAuth session info from
        // the URL automatically (detectSessionInUrl defaults to true). To be
        // robust, fetch the current session which will be populated after the
        // redirect handling.
        await supabase.auth.getSession()

        // After session handling, perform a full navigation to the app root so
        // server-rendered UI (server components) update immediately without
        // requiring the user to force-refresh.
        if (typeof window !== 'undefined') {
          // Use location.replace to avoid adding an extra history entry.
          window.location.replace('/')
        } else {
          router.replace('/')
        }
      } catch (err) {
        console.error('Error handling auth callback', err)
        router.replace('/')
      }
    }

    handle()
  }, [router])

  return null
}
