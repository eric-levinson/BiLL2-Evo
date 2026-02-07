'use client'

import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'

interface SleeperConnectProps {
  onSubmit: (username: string) => Promise<void>
  initialUsername?: string
}

export default function SleeperConnect({
  onSubmit,
  initialUsername = ''
}: SleeperConnectProps) {
  const [username, setUsername] = useState(initialUsername)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault()
    setError(null)

    // Validation
    const trimmedUsername = username.trim()
    if (!trimmedUsername) {
      setError('Please enter your Sleeper username')
      return
    }

    // Basic username validation (alphanumeric, underscore, hyphen)
    const usernameRegex = /^[a-zA-Z0-9_-]+$/
    if (!usernameRegex.test(trimmedUsername)) {
      setError('Username can only contain letters, numbers, underscores, and hyphens')
      return
    }

    setLoading(true)

    try {
      await onSubmit(trimmedUsername)
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : 'Failed to fetch leagues. Please check your username and try again.'
      )
    } finally {
      setLoading(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-4">
      <div className="grid gap-2">
        <Label htmlFor="sleeper-username">Sleeper Username</Label>
        <Input
          id="sleeper-username"
          name="username"
          type="text"
          placeholder="Enter your Sleeper username"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          required
          disabled={loading}
        />
        {error && <p className="text-sm text-red-600">{error}</p>}
      </div>

      <Button type="submit" className="w-full text-black" disabled={loading}>
        {loading ? 'Fetching leagues...' : 'Continue'}
      </Button>
    </form>
  )
}
