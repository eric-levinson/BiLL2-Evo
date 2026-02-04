import { NextResponse } from 'next/server'
import { createServerSupabaseClient } from '@/lib/supabase/server'

export async function POST(req: Request, context: any) {
  const params = context && context.params ? await context.params : undefined
  const agentId = params?.agentId

  const supabase = await createServerSupabaseClient()
  const { data } = await supabase.auth.getUser()
  const user = data?.user ?? null

  if (!user) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
  }

  const playgroundBase = process.env.PLAYGROUND_API_URL || 'http://localhost:7777'
  const url = `${playgroundBase}/v1/playground/agents/${encodeURIComponent(agentId)}/runs`

  try {
    const contentType = req.headers.get('content-type') || ''
    if (contentType.includes('multipart/form-data') || contentType.includes('application/x-www-form-urlencoded')) {
      const formData = await req.formData()
      formData.set('user_id', user.id)
      const resp = await fetch(url, { method: 'POST', body: formData })
      return new NextResponse(resp.body, { status: resp.status, headers: { 'content-type': resp.headers.get('content-type') || 'text/event-stream' } })
    }

    const body = await req.text()
    const forwardUrl = new URL(url)
    forwardUrl.searchParams.set('user_id', user.id)
    const resp = await fetch(forwardUrl.toString(), { method: 'POST', body })
    return new NextResponse(resp.body, { status: resp.status, headers: { 'content-type': resp.headers.get('content-type') || 'application/json' } })
  } catch (err) {
    return NextResponse.json({ error: 'Proxy error' }, { status: 502 })
  }
}
