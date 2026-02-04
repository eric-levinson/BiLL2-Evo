"use client"

import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Label } from '@/components/ui/label'
import DiscordSignInButton from './DiscordSignInButton'

export default function LoginForm() {
    const [errors, setErrors] = useState<Record<string, string> | null>(null)
    const [loading, setLoading] = useState(false)

    async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
        e.preventDefault()
        setErrors(null)
        setLoading(true)

        const fd = new FormData(e.currentTarget)

        try {
            const res = await fetch('/api/auth/login', { method: 'POST', body: fd })
            const json = await res.json()
            if (!res.ok) {
                setErrors(json.errors ?? { server: 'Unknown error' })
            } else {
                // success — reload to pick up session or redirect
                window.location.href = '/'
            }
        } catch (err) {
            setErrors({ server: 'Network error' })
        } finally {
            setLoading(false)
        }
    }

    return (
        <Card className="shadow">
            <CardHeader className="p-6">
                <CardTitle>Sign in</CardTitle>
            </CardHeader>
            <CardContent className="p-6">
                <form onSubmit={handleSubmit} className="flex flex-col gap-4">
                    <div className="grid gap-2">
                        <Label htmlFor="email">Email</Label>
                        <Input id="email" name="email" type="email" required />
                        {errors?.email && <p className="text-sm text-red-600">{errors.email}</p>}
                    </div>

                    <div className="grid gap-2">
                        <Label htmlFor="password">Password</Label>
                        <Input id="password" name="password" type="password" required />
                        {errors?.password && <p className="text-sm text-red-600">{errors.password}</p>}
                    </div>

                    {errors?.server && <p className="text-sm text-red-600">{errors.server}</p>}

                    <Button type="submit" className="w-full text-black" disabled={loading}>
                        {loading ? 'Signing in...' : 'Sign in'}
                    </Button>

                    <div className="pt-2">
                        <DiscordSignInButton />
                    </div>
                </form>
            </CardContent>
        </Card>
    )
}
