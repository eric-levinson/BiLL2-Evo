import { createClient } from '@supabase/supabase-js'

// Hardcode credentials for now (from .env file)
const supabaseUrl = 'https://amkdylmcqwqpjpuwjsxv.supabase.co'
const supabaseKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImFta2R5bG1jcXdxcGpwdXdqc3h2Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3MzY3MTI4NjksImV4cCI6MjA1MjI4ODg2OX0.Hs5LoQlJ9SWcwovbj3FuwbZfDZaLvHuxQk2DsKMq9LM'

if (!supabaseUrl || !supabaseKey) {
  console.error('Missing Supabase credentials')
  process.exit(1)
}

const supabase = createClient(supabaseUrl, supabaseKey)

async function inspectSession(sessionId: string) {
  const { data, error } = await supabase
    .from('chat_sessions')
    .select('id, title, created_at, messages')
    .eq('id', sessionId)
    .single()

  if (error) {
    console.error('Error fetching session:', error)
    return
  }

  console.log('Session ID:', data.id)
  console.log('Title:', data.title)
  console.log('Created:', data.created_at)
  console.log('\n=== MESSAGES ===\n')

  const messages = data.messages as any[]

  // Track tool call IDs
  const toolCallIds = new Set<string>()
  const duplicates = new Set<string>()

  messages.forEach((msg, index) => {
    console.log(`\n--- Message ${index + 1} (${msg.role}) ---`)

    if (msg.parts) {
      msg.parts.forEach((part: any, partIndex: number) => {
        console.log(`  Part ${partIndex + 1}: ${part.type}`)

        if (part.type === 'tool-call') {
          const toolCallId = part.toolCallId
          console.log(`    Tool: ${part.toolName}`)
          console.log(`    Tool Call ID: ${toolCallId}`)

          if (toolCallIds.has(toolCallId)) {
            console.log(`    ⚠️  DUPLICATE TOOL CALL ID!`)
            duplicates.add(toolCallId)
          } else {
            toolCallIds.add(toolCallId)
          }
        }

        if (part.type === 'tool-result') {
          const toolCallId = part.toolCallId
          console.log(`    Tool: ${part.toolName}`)
          console.log(`    Tool Call ID: ${toolCallId}`)

          if (toolCallIds.has(toolCallId)) {
            console.log(`    ⚠️  DUPLICATE TOOL CALL ID!`)
            duplicates.add(toolCallId)
          } else {
            toolCallIds.add(toolCallId)
          }
        }

        if (part.type === 'text') {
          const preview = part.text.substring(0, 100)
          console.log(`    Text: ${preview}${part.text.length > 100 ? '...' : ''}`)
        }
      })
    } else if (msg.content) {
      // Old format
      console.log(`  Content: ${msg.content.substring(0, 100)}`)
    }
  })

  if (duplicates.size > 0) {
    console.log('\n\n⚠️  DUPLICATE TOOL CALL IDS FOUND:')
    duplicates.forEach(id => console.log(`  - ${id}`))
  } else {
    console.log('\n\n✅ No duplicate tool call IDs found')
  }

  console.log(`\nTotal unique tool call IDs: ${toolCallIds.size}`)
}

// Get session ID from command line or use default
const sessionId = process.argv[2] || '44dc6830-9145-4047-be71-323a683d8603'
inspectSession(sessionId)
