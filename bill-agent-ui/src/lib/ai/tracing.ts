import { NodeTracerProvider } from '@opentelemetry/sdk-trace-node'
import { OpenInferenceSimpleSpanProcessor } from '@arizeai/openinference-vercel'
import { OTLPTraceExporter } from '@opentelemetry/exporter-trace-otlp-proto'

const PHOENIX_ENDPOINT = process.env.PHOENIX_COLLECTOR_ENDPOINT

let provider: NodeTracerProvider | null = null

/**
 * Initialize OpenTelemetry tracing with Arize Phoenix as the backend.
 * No-op if PHOENIX_COLLECTOR_ENDPOINT is not configured.
 */
export function initTracing() {
  if (!PHOENIX_ENDPOINT) {
    console.log(
      '[Tracing] PHOENIX_COLLECTOR_ENDPOINT not set — tracing disabled'
    )
    return
  }

  provider = new NodeTracerProvider({
    spanProcessors: [
      new OpenInferenceSimpleSpanProcessor({
        exporter: new OTLPTraceExporter({ url: PHOENIX_ENDPOINT })
      })
    ]
  })
  provider.register()

  console.log(`[Tracing] Phoenix tracing initialized → ${PHOENIX_ENDPOINT}`)
}

/**
 * Flush pending traces. Call before serverless function returns
 * to ensure all spans are exported to Phoenix.
 */
export async function flushTraces() {
  if (provider) {
    await provider.forceFlush()
  }
}

/**
 * Feature keyword map for segmenting traces in Phoenix.
 * Maps tool-call patterns and user message keywords to feature categories.
 */
const FEATURE_KEYWORDS: Record<string, string[]> = {
  trade: [
    'trade',
    'trading',
    'get_trade_context',
    'dynasty_trade',
    'sell',
    'buy',
    'package'
  ],
  waiver: [
    'waiver',
    'waivers',
    'pickup',
    'pick up',
    'free agent',
    'get_waiver_context',
    'trending'
  ],
  startsit: [
    'start',
    'sit',
    'start/sit',
    'lineup',
    'bench',
    'get_start_sit_context',
    'flex'
  ],
  roster: ['roster', 'rosters', 'drop', 'add', 'stash', 'ir', 'taxi'],
  rankings: [
    'rank',
    'ranks',
    'ranking',
    'rankings',
    'get_fantasy_ranks',
    'tier'
  ],
  stats: [
    'stats',
    'statistics',
    'numbers',
    'advanced',
    'get_advanced',
    'profile',
    'deep dive'
  ],
  matchup: ['matchup', 'matchups', 'opponent', 'vs', 'against', 'week'],
  league: ['league', 'leagues', 'sleeper', 'settings', 'scoring']
}

/**
 * Detect the feature category from a user message for trace segmentation.
 * Returns the first matching feature, or 'general' if no match.
 */
export function detectFeature(message: string): string {
  const lower = message.toLowerCase()
  for (const [feature, keywords] of Object.entries(FEATURE_KEYWORDS)) {
    if (keywords.some((kw) => lower.includes(kw))) {
      return feature
    }
  }
  return 'general'
}
