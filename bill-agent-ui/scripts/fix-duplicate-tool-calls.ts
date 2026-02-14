import { createClient } from '@supabase/supabase-js'

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL
const supabaseKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY

if (!supabaseUrl || !supabaseKey) {
  throw new Error(
    'Missing required environment variables: NEXT_PUBLIC_SUPABASE_URL, NEXT_PUBLIC_SUPABASE_ANON_KEY'
  )
}

const supabase = createClient(supabaseUrl, supabaseKey)

interface UIMessage {
  role: string
  parts?: Array<{
    type: string
    toolCallId?: string
    [key: string]: any
  }>
  [key: string]: any
}

function deduplicateToolCalls(messages: UIMessage[]): UIMessage[] {
  const seenToolCallIds = new Set<string>()
  const seenToolResultIds = new Set<string>()

  return messages.map((message) => {
    if (!message.parts) {
      return message
    }

    const deduplicatedParts = message.parts.filter((part) => {
      if (part.type === 'tool-call' && 'toolCallId' in part) {
        const toolCallId = part.toolCallId!
        if (seenToolCallIds.has(toolCallId)) {
          console.log(`  ❌ Removing duplicate tool-call: ${toolCallId}`)
          return false
        }
        seenToolCallIds.add(toolCallId)
      }

      if (part.type === 'tool-result' && 'toolCallId' in part) {
        const toolCallId = part.toolCallId!
        if (seenToolResultIds.has(toolCallId)) {
          console.log(`  ❌ Removing duplicate tool-result: ${toolCallId}`)
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

async function fixAllSessions() {
  console.log('🔍 Fetching all chat sessions...\n')

  const { data: sessions, error } = await supabase
    .from('chat_sessions')
    .select('id, title, messages')
    .not('messages', 'is', null)

  if (error) {
    console.error('❌ Error fetching sessions:', error)
    return
  }

  console.log(`Found ${sessions?.length || 0} sessions\n`)

  let fixedCount = 0

  for (const session of sessions || []) {
    const messages = session.messages as UIMessage[]
    const originalLength = JSON.stringify(messages).length

    // Check if there are any duplicates
    const toolCallIds = new Set<string>()
    const toolResultIds = new Set<string>()
    let hasDuplicates = false

    for (const msg of messages) {
      if (!msg.parts) continue
      for (const part of msg.parts) {
        if (part.type === 'tool-call' && part.toolCallId) {
          if (toolCallIds.has(part.toolCallId)) {
            hasDuplicates = true
            break
          }
          toolCallIds.add(part.toolCallId)
        }
        if (part.type === 'tool-result' && part.toolCallId) {
          if (toolResultIds.has(part.toolCallId)) {
            hasDuplicates = true
            break
          }
          toolResultIds.add(part.toolCallId)
        }
      }
      if (hasDuplicates) break
    }

    if (!hasDuplicates) {
      console.log(`✓ Session "${session.title}" - No duplicates found`)
      continue
    }

    console.log(`🔧 Fixing session: "${session.title}" (${session.id})`)
    const deduplicated = deduplicateToolCalls(messages)
    const newLength = JSON.stringify(deduplicated).length

    const { error: updateError } = await supabase
      .from('chat_sessions')
      .update({ messages: deduplicated })
      .eq('id', session.id)

    if (updateError) {
      console.error(`  ❌ Error updating session ${session.id}:`, updateError)
    } else {
      fixedCount++
      console.log(
        `  ✅ Fixed! Reduced size: ${originalLength} → ${newLength} bytes\n`
      )
    }
  }

  console.log(
    `\n✅ Done! Fixed ${fixedCount} sessions with duplicate tool calls`
  )
}

fixAllSessions()
