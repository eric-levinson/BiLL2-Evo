/**
 * Next.js instrumentation hook — called once on server startup.
 * Initializes OpenTelemetry tracing for Arize Phoenix observability.
 */
export async function register() {
  // Only initialize on the Node.js runtime (not edge)
  if (process.env.NEXT_RUNTIME === 'nodejs') {
    const { initTracing } = await import('@/lib/ai/tracing')
    initTracing()
  }
}
