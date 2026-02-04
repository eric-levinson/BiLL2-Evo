import { createServerSupabaseClient } from '@/lib/supabase/server'
import { revalidatePath } from 'next/cache'
import { NextResponse, type NextRequest } from 'next/server'

export async function POST(req: NextRequest) {
  const supabase = await createServerSupabaseClient()

  const {
    data: { user }
  } = await supabase.auth.getUser()

  if (user) {
    await supabase.auth.signOut()
  }

  // Revalidate any layout paths that depend on auth state
  revalidatePath('/')

  return NextResponse.redirect(new URL('/login', req.url), { status: 302 })
}
