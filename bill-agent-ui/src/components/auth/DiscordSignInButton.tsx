"use client"

import { Button } from '@/components/ui/button'

export default function DiscordSignInButton() {
  function handleDiscordSignIn() {
    // Navigate the browser directly to the server route so the OAuth redirect
    // can be handled by Supabase and the browser (avoids fetch and form issues).
    window.location.href = '/api/auth/discord'
  }

  return (
    <Button type="button" variant="outline" onClick={handleDiscordSignIn} className="w-full">
      Continue with Discord
    </Button>
  )
}
