import { createServerSupabaseClient } from '@/lib/supabase/server'
import NavbarClient from './NavbarClient'

export default async function NavbarServer() {
  const supabase = await createServerSupabaseClient()
  const { data } = await supabase.auth.getUser()
  const user = data?.user ?? null

  return <NavbarClient user={user} />
}
