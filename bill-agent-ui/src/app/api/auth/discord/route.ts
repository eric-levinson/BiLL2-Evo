import { NextResponse } from 'next/server'
import { createServerSupabaseClient } from '@/lib/supabase/server'

export async function GET() {
  const supabase = await createServerSupabaseClient()

  // Build a redirectTo URL for the final callback page in the app. Use an
  // environment variable when available so this works in production.
  const appUrl = process.env.NEXT_PUBLIC_APP_URL ?? 'http://localhost:3000'
  const redirectTo = `${appUrl}/auth/callback`

  // Initiate OAuth sign-in via Supabase hosted flow. The hosted project stores
  // Discord client id/secret in the dashboard, so we don't need to pass them here.
  const { data, error } = await supabase.auth.signInWithOAuth({
    provider: 'discord',
    options: { redirectTo }
  })

  if (error) {
    return NextResponse.json({ error: error.message }, { status: 500 })
  }

  // If Supabase returned a redirect URL, redirect the user there.
  if (data?.url) return NextResponse.redirect(data.url)

  // Fallback: return the URL in JSON
  return NextResponse.json({ url: data?.url ?? null })
}
