'use server'

import { revalidatePath } from 'next/cache'
import { redirect } from 'next/navigation'

import { createServerSupabaseClient } from '@/lib/supabase/server'

export async function login(formData: FormData) {
  const supabase = await createServerSupabaseClient()

  const data = {
    email: formData.get('email') as string,
    password: formData.get('password') as string
  }

  const { error } = await supabase.auth.signInWithPassword(data)

  if (error) {
    // On error, send the user to a simple error page — the UI can be improved later.
    redirect('/error')
  }

  // Invalidate any layout data that depends on the auth state and send the user home
  revalidatePath('/')
  redirect('/')
}

export async function signup(formData: FormData) {
  const supabase = await createServerSupabaseClient()

  const data = {
    email: formData.get('email') as string,
    password: formData.get('password') as string
  }

  const { error } = await supabase.auth.signUp(data)

  if (error) {
    redirect('/error')
  }

  revalidatePath('/')
  redirect('/')
}
