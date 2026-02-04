import LoginForm from '@/components/auth/LoginForm'

export const metadata = {
  title: 'Login'
}

export default function Page() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-background p-4">
      <div className="w-full max-w-md">
        <LoginForm />
      </div>
    </div>
  )
}
