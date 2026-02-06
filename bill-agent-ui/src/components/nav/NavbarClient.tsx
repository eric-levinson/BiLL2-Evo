'use client'
import Link from 'next/link'
import { Button } from '@/components/ui/button'
import { UserIcon } from '@/components/ui/icon/custom-icons'
import { useEffect, useState } from 'react'
import supabase from '@/lib/supabase/client'
import DropdownMenu, {
  DropdownMenuTrigger,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator
} from '@/components/ui/dropdown-menu'

export default function NavbarClient({
  user: initialUser
}: {
  user?: { email?: string } | null
}) {
  const [user, setUser] = useState(initialUser)

  useEffect(() => {
    // Listen for auth state changes and update local user state so client
    // components reflect sign-in/sign-out immediately after redirect.
    const { data: sub } = supabase.auth.onAuthStateChange((event, session) => {
      if (session?.user) setUser({ email: session.user.email ?? undefined })
      else setUser(null)
    })

    return () => sub?.subscription?.unsubscribe?.()
  }, [])

  async function handleSignOut(e: React.MouseEvent) {
    e.preventDefault()
    try {
      await fetch('/auth/signout', {
        method: 'POST',
        credentials: 'same-origin'
      })
    } catch {
      // ignore - server will handle
    }
    // reload to update session state
    window.location.href = '/'
  }

  return (
    <header className="w-full border-b bg-background/50">
      <div className="mx-auto flex max-w-7xl items-center justify-between gap-4 px-4 py-3">
        <Link href="/" className="flex items-center gap-3">
          <span className="inline-flex items-center">BiLL-2</span>
        </Link>

        <nav className="flex items-center gap-3">
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" size="sm" className="ml-2">
                <span className="flex items-center gap-2">
                  <UserIcon />
                  <span className="hidden sm:inline">
                    {user?.email ?? 'Account'}
                  </span>
                </span>
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuLabel>Account</DropdownMenuLabel>
              {user ? (
                <>
                  <DropdownMenuItem asChild>
                    <Link href="/account">Profile</Link>
                  </DropdownMenuItem>
                  <DropdownMenuSeparator />
                  <DropdownMenuItem
                    onClick={handleSignOut}
                    className="cursor-pointer text-destructive"
                  >
                    Sign out
                  </DropdownMenuItem>
                </>
              ) : (
                <>
                  <DropdownMenuItem asChild>
                    <Link href="/login">Sign in</Link>
                  </DropdownMenuItem>
                  <DropdownMenuItem asChild>
                    <Link href="/signup">Create account</Link>
                  </DropdownMenuItem>
                </>
              )}
            </DropdownMenuContent>
          </DropdownMenu>
        </nav>
      </div>
    </header>
  )
}
