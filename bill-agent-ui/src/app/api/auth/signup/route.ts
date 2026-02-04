import { NextResponse, type NextRequest } from 'next/server'
import { createServerSupabaseClient } from '@/lib/supabase/server'

export async function POST(request: NextRequest) {
  const form = await request.formData()
  const email = String(form.get('email') ?? '')
  const password = String(form.get('password') ?? '')
  const confirm = String(form.get('confirm') ?? '')

  const errors: Record<string, string> = {}

  if (!email) errors.email = 'Email is required'
  // very small validation to keep things simple
  if (!password || password.length < 6)
    errors.password = 'Password must be at least 6 characters'
  if (password !== confirm) errors.confirm = "Passwords don't match"

  if (Object.keys(errors).length > 0) {
    return NextResponse.json({ success: false, errors }, { status: 400 })
  }

  const supabase = await createServerSupabaseClient()

  const { error } = await supabase.auth.signUp({ email, password })

  if (error) {
    return NextResponse.json(
      { success: false, errors: { server: error.message } },
      { status: 400 }
    )
  }

  return NextResponse.json({ success: true })
}
