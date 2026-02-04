import { NextResponse } from 'next/server'
import { createServerSupabaseClient } from '@/lib/supabase/server'

// Use a looser signature to avoid mismatches with Next's generated types
export async function GET(req: Request, context: any) {
  // Next.js may provide `params` as a promise for dynamic routes — await it.
  const params = context && context.params ? await context.params : undefined
  // Create server supabase client to get authenticated user
  const supabase = await createServerSupabaseClient()
  const { data } = await supabase.auth.getUser()
  const user = data?.user ?? null

  if (!user) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
  }

  const teamId = params.teamId

  // Build playground URL from query params if present
  const playgroundBase = process.env.PLAYGROUND_API_URL || 'http://localhost:7777'
  const url = new URL(`${playgroundBase}/v1/playground/teams/${encodeURIComponent(teamId)}/sessions`)

  // Preserve other query params if any (but override user_id with authenticated user's id)
  const incoming = new URL(req.url)
  incoming.searchParams.forEach((value, key) => {
    if (key !== 'user_id') url.searchParams.append(key, value)
  })
  url.searchParams.set('user_id', user.id)

  try {
    const resp = await fetch(url.toString(), { method: 'GET' })
    const body = await resp.text()
    return new NextResponse(body, { status: resp.status, headers: { 'content-type': resp.headers.get('content-type') || 'application/json' } })
  } catch (err) {
    return NextResponse.json({ error: 'Proxy error' }, { status: 502 })
  }
}
