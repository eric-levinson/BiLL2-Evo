import { createServerClient } from '@supabase/ssr'
import { NextResponse, type NextRequest } from 'next/server'

export async function updateSession(request: NextRequest) {
  // Start with a response that will be returned unless we change it below
  let supabaseResponse = NextResponse.next({ request })

  const supabase = createServerClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
    {
      cookies: {
        getAll() {
          return request.cookies.getAll()
        },
        setAll(cookiesToSet) {
          // write cookies into the request (so server components can read them)
          cookiesToSet.forEach(({ name, value }) =>
            request.cookies.set(name, value)
          )

          // create a new response and copy cookies to the response so the browser is updated
          supabaseResponse = NextResponse.next({ request })
          cookiesToSet.forEach(({ name, value, options }) =>
            supabaseResponse.cookies.set(name, value, options)
          )
        }
      }
    }
  )

  // IMPORTANT: don't run other logic between createServerClient and getUser()
  // as the client needs to immediately validate the token.
  const {
    data: { user }
  } = await supabase.auth.getUser()

  // If there's no user, redirect to login for protected paths
  // Redirect signed-in users from root to the protected app
  if (user && request.nextUrl.pathname === '/') {
    const url = request.nextUrl.clone()
    url.pathname = '/app'
    return NextResponse.redirect(url)
  }

  // If there's no user, only redirect to login for protected /app paths
  if (
    !user &&
    request.nextUrl.pathname.startsWith('/app') &&
    !request.nextUrl.pathname.startsWith('/auth')
  ) {
    const url = request.nextUrl.clone()
    url.pathname = '/login'
    return NextResponse.redirect(url)
  }

  return supabaseResponse
}

export default updateSession
