import SignupForm from '@/components/auth/SignupForm'

export const metadata = {
    title: 'Sign up',
}

export default function Page() {
    return (
        <div className="min-h-screen flex items-center justify-center bg-background p-4">
            <div className="w-full max-w-md">
                <SignupForm />
            </div>
        </div>
    )
}
