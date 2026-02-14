import { NextResponse } from 'next/server'
import { createServerSupabaseClient } from '@/lib/supabase/server'
import type { UIMessage } from 'ai'

function deduplicateToolCalls(messages: UIMessage[]): UIMessage[] {
  const seenToolCallIds = new Set<string>()
  const seenToolResultIds = new Set<string>()

  return messages.map((message) => {
    if (!message.parts) {
      return message
    }

    const deduplicatedParts = message.parts.filter((part) => {
      if (part.type === 'tool-call' && 'toolCallId' in part) {
        const toolCallId = (part as { toolCallId: string }).toolCallId
        if (seenToolCallIds.has(toolCallId)) {
          console.log(`[Fix] Removing duplicate tool-call: ${toolCallId}`)
          return false
        }
        seenToolCallIds.add(toolCallId)
      }

      if (part.type === 'tool-result' && 'toolCallId' in part) {
        const toolCallId = (part as { toolCallId: string }).toolCallId
        if (seenToolResultIds.has(toolCallId)) {
          console.log(`[Fix] Removing duplicate tool-result: ${toolCallId}`)
          return false
        }
        seenToolResultIds.add(toolCallId)
      }

      return true
    })

    return {
      ...message,
      parts: deduplicatedParts
    }
  })
}

export async function POST() {
  const supabase = await createServerSupabaseClient()

  // Verify authentication
  const { data } = await supabase.auth.getUser()
  const user = data?.user ?? null

  if (!user) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
  }

  console.log('[Fix Sessions] Starting fix for user:', user.id)

  // Get all sessions for this user
  const { data: sessions, error } = await supabase
    .from('chat_sessions')
    .select('id, title, messages')
    .eq('user_id', user.id)
    .not('messages', 'is', null)

  if (error) {
    console.error('[Fix Sessions] Error fetching sessions:', error)
    return NextResponse.json({ error: error.message }, { status: 500 })
  }

  let fixedCount = 0
  const results = []

  for (const session of sessions || []) {
    const messages = session.messages as UIMessage[]

    // Check for duplicates
    const toolCallIds = new Set<string>()
    const toolResultIds = new Set<string>()
    let hasDuplicates = false

    for (const msg of messages) {
      if (!msg.parts) continue
      for (const part of msg.parts) {
        // Check any part with a toolCallId
        if ('toolCallId' in part && part.toolCallId) {
          const id = (part as { toolCallId: string }).toolCallId
          const isToolResult = part.type === 'tool-result'

          if (isToolResult) {
            if (toolResultIds.has(id)) {
              hasDuplicates = true
              break
            }
            toolResultIds.add(id)
          } else {
            if (toolCallIds.has(id)) {
              hasDuplicates = true
              break
            }
            toolCallIds.add(id)
          }
        }
      }
      if (hasDuplicates) break
    }

    if (!hasDuplicates) {
      results.push({ id: session.id, title: session.title, status: 'ok' })
      continue
    }

    console.log(
      `[Fix Sessions] Fixing session: ${session.title} (${session.id})`
    )
    const deduplicated = deduplicateToolCalls(messages)

    const { error: updateError } = await supabase
      .from('chat_sessions')
      .update({ messages: deduplicated })
      .eq('id', session.id)

    if (updateError) {
      console.error(
        `[Fix Sessions] Error updating session ${session.id}:`,
        updateError
      )
      results.push({
        id: session.id,
        title: session.title,
        status: 'error',
        error: updateError.message
      })
    } else {
      fixedCount++
      results.push({ id: session.id, title: session.title, status: 'fixed' })
    }
  }

  console.log(
    `[Fix Sessions] Done! Fixed ${fixedCount}/${sessions?.length || 0} sessions`
  )

  return NextResponse.json({
    success: true,
    totalSessions: sessions?.length || 0,
    fixedCount,
    results
  })
}
