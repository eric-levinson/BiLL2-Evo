import { createServerSupabaseClient } from '@/lib/supabase/server'
import { redirect } from 'next/navigation'
import { Button } from '@/components/ui/button'
import SleeperConnectionSettings from '@/components/account/SleeperConnectionSettings'

export default async function AccountPage() {
  const supabase = await createServerSupabaseClient()
  const { data: { user } = {} } = await supabase.auth.getUser()

  if (!user) {
    // Not signed in — redirect to login
    redirect('/login')
  }

  return (
    <main className="mx-auto max-w-3xl px-4 py-8">
      <h1 className="text-2xl font-semibold">Account</h1>

      <section className="mt-6 space-y-4">
        <div>
          <p className="text-muted-foreground text-sm">Email</p>
          <p className="mt-1 font-medium">{user?.email}</p>
        </div>
      </section>

      <section className="mt-6">
        <SleeperConnectionSettings />
      </section>

      <section className="mt-6">
        <form action="/auth/signout" method="post">
          <Button type="submit" variant="destructive">
            Sign out
          </Button>
        </form>
      </section>
    </main>
  )
}
