import Link from 'next/link'
import { Button } from '@/components/ui/button'
import { UserIcon } from '@/components/ui/icon/custom-icons'
import DropdownMenu, {
  DropdownMenuTrigger,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator
} from '@/components/ui/dropdown-menu'

async function handleSignOut(e: React.MouseEvent) {
  e.preventDefault()
  try {
    await fetch('/auth/signout', { method: 'POST', credentials: 'same-origin' })
  } catch {
    // ignore - server will handle
  }
  window.location.href = '/'
}

export default function Navbar() {
  return (
    <header className="w-full border-b bg-background/50">
      <div className="mx-auto flex max-w-7xl items-center justify-between gap-4 px-4 py-3">
        <Link href="/" className="flex items-center gap-3">
          <span className="font-medium">BiLL-2</span>
        </Link>

        <nav className="flex items-center gap-3">
          <Link href="/playground" className="text-muted-foreground text-sm">
            Playground
          </Link>

          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" size="sm" className="ml-2">
                <span className="flex items-center gap-2">
                  <UserIcon />
                  <span className="sr-only">Account</span>
                  <span className="hidden sm:inline">Account</span>
                </span>
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuLabel>Account</DropdownMenuLabel>
              <DropdownMenuItem>
                <Link href="/account">Profile</Link>
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem
                onClick={handleSignOut}
                className="cursor-pointer text-destructive"
              >
                Sign out
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </nav>
      </div>
    </header>
  )
}
