import { createServerSupabaseClient } from '@/lib/supabase/server'
import { redirect } from 'next/navigation'
import Sidebar from '@/components/playground/Sidebar/Sidebar'
import { ChatArea } from '@/components/playground/ChatArea'
import { AssistantRuntimeProviderWrapper } from '@/hooks/useAssistantRuntime'
import OnboardingWrapper from '@/components/onboarding/OnboardingWrapper'
import { Suspense } from 'react'

export default async function AppPage() {
  const supabase = await createServerSupabaseClient()
  const { data } = await supabase.auth.getUser()

  if (!data?.user) {
    redirect('/login')
  }

  return (
    <Suspense fallback={<div>Loading...</div>}>
      <AssistantRuntimeProviderWrapper>
        <div className="flex h-screen overflow-hidden bg-background/80">
          <Sidebar />
          <ChatArea />
        </div>
        <OnboardingWrapper />
      </AssistantRuntimeProviderWrapper>
    </Suspense>
  )
}
