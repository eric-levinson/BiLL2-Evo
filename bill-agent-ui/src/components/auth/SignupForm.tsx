"use client"

import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Label } from '@/components/ui/label'

import { signup } from '@/app/login/actions'

export default function SignupForm() {
    const [errors, setErrors] = useState<Record<string, string> | null>(null)
    const [loading, setLoading] = useState(false)

    async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
        e.preventDefault()
        setErrors(null)
        setLoading(true)

        const fd = new FormData(e.currentTarget)
        // client-side confirm-password validation
        const password = String(fd.get('password') ?? '')
        const confirm = String(fd.get('confirm') ?? '')
        if (password !== confirm) {
            setErrors({ confirm: "Passwords don't match" })
            setLoading(false)
            return
        }

        try {
            const res = await fetch('/api/auth/signup', { method: 'POST', body: fd })
            const json = await res.json()
            if (!res.ok) {
                setErrors(json.errors ?? { server: 'Unknown error' })
            } else {
                // success — you can redirect or show a success message
                alert('Signed up — check your email for confirmation (if enabled)')
                e.currentTarget.reset()
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
                <CardTitle>Create account</CardTitle>
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

                    <div className="grid gap-2">
                        <Label htmlFor="confirm">Confirm password</Label>
                        <Input id="confirm" name="confirm" type="password" required />
                        {errors?.confirm && <p className="text-sm text-red-600">{errors.confirm}</p>}
                    </div>

                    {errors?.server && <p className="text-sm text-red-600">{errors.server}</p>}

                    <Button type="submit" className="w-full text-black" disabled={loading}>
                        {loading ? 'Creating account...' : 'Sign up'}
                    </Button>
                </form>
            </CardContent>
        </Card>
    )
}
