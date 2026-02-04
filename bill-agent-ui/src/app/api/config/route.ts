import { NextResponse } from 'next/server'

export async function GET() {
  // Prefer NEXT_PUBLIC_ prefixed var for client visibility, but fall back to
  // server-only DISPLAY_ENDPOINT_MODE if present. Interpret truthy strings.
  const raw =
    process.env.NEXT_PUBLIC_DISPLAY_ENDPOINT_MODE ??
    process.env.DISPLAY_ENDPOINT_MODE
  const val =
    typeof raw === 'string' ? raw.toLowerCase() === 'true' : Boolean(raw)
  return NextResponse.json({ displayEndpointMode: val })
}
