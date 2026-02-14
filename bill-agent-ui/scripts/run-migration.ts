import { createClient } from '@supabase/supabase-js'

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL
const supabaseKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY

if (!supabaseUrl || !supabaseKey) {
  throw new Error(
    'Missing required environment variables: NEXT_PUBLIC_SUPABASE_URL, NEXT_PUBLIC_SUPABASE_ANON_KEY'
  )
}

const supabase = createClient(supabaseUrl, supabaseKey)

async function runMigration() {
  console.log('Running migration 004_cleanup_preference_tags...')

  // First, check what we have
  const { data: before, error: beforeError } = await supabase
    .from('user_preferences')
    .select('id, preference_tags')
    .not('preference_tags', 'is', null)

  if (beforeError) {
    console.error('Error fetching before state:', beforeError)
    return
  }

  console.log('\n=== BEFORE MIGRATION ===')
  before?.forEach((row: any) => {
    console.log(`User: ${row.id}`)
    console.log(`Tags: ${JSON.stringify(row.preference_tags)}`)
  })

  // Run the migration (remove Sleeper username entries)
  const { data: updated, error: updateError } = await supabase.rpc(
    'cleanup_sleeper_username_tags'
  )

  if (updateError) {
    console.error('\nMigration RPC not available, running inline update...')

    // Do it manually
    for (const row of before || []) {
      const tags = row.preference_tags || []
      const cleanedTags = tags.filter(
        (tag: string) => !tag.toLowerCase().includes('sleeper username:')
      )

      if (tags.length !== cleanedTags.length) {
        const { error } = await supabase
          .from('user_preferences')
          .update({ preference_tags: cleanedTags })
          .eq('id', row.id)

        if (error) {
          console.error(`Error updating row ${row.id}:`, error)
        } else {
          console.log(
            `✓ Cleaned ${row.id}: removed ${tags.length - cleanedTags.length} tags`
          )
        }
      }
    }
  } else {
    console.log('\nMigration completed via RPC:', updated)
  }

  // Check after
  const { data: after, error: afterError } = await supabase
    .from('user_preferences')
    .select('id, preference_tags')
    .not('preference_tags', 'is', null)

  if (afterError) {
    console.error('Error fetching after state:', afterError)
    return
  }

  console.log('\n=== AFTER MIGRATION ===')
  after?.forEach((row: any) => {
    console.log(`User: ${row.id}`)
    console.log(`Tags: ${JSON.stringify(row.preference_tags)}`)
  })

  console.log('\n✅ Migration complete!')
}

runMigration()
