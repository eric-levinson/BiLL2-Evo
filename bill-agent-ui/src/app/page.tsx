'use client'
import Link from 'next/link'

export default function Landing() {
  return (
    <main className="mx-auto max-w-3xl px-6 py-24 text-center">
      <h1 className="text-4xl font-bold">Welcome to BiLL-2</h1>
      <p className="text-muted-foreground mt-4">
        AI-powered fantasy football analytics. Sign in or create an account to
        get started.
      </p>

      <div className="mt-8 flex items-center justify-center gap-4">
        <Link href="/login">
          <button className="rounded-md bg-primary px-4 py-2 text-black">
            Sign in
          </button>
        </Link>

        <Link href="/signup">
          <button className="rounded-md border px-4 py-2">
            Create account
          </button>
        </Link>
      </div>

      <div className="mt-12">
        <Link href="/app" className="text-muted-foreground text-sm underline">
          Go to the app (protected)
        </Link>
      </div>
    </main>
  )
}
