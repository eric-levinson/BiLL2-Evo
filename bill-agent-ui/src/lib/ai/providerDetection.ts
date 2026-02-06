/**
 * Provider detection utility for AI model ID parsing
 * Determines the AI provider from a model ID string
 */

export type AIProvider = 'anthropic' | 'openai' | 'google' | 'other'

/**
 * Provider detection patterns
 * Maps provider identifiers to their provider type
 */
const PROVIDER_PATTERNS: Record<AIProvider, string[]> = {
  anthropic: ['claude', 'anthropic'],
  openai: ['gpt', 'openai', 'o1', 'o3'],
  google: ['gemini', 'google'],
  other: []
}

/**
 * Detects the AI provider from a model ID string
 *
 * @param modelId - The AI model identifier (e.g., 'claude-sonnet-4', 'gpt-4o', 'gemini-pro')
 * @returns The detected provider type: 'anthropic', 'openai', 'google', or 'other'
 *
 * @example
 * detectProvider('claude-sonnet-4-20250514') // => 'anthropic'
 * detectProvider('gpt-4o') // => 'openai'
 * detectProvider('gemini-pro') // => 'google'
 * detectProvider('unknown-model') // => 'other'
 */
export const detectProvider = (modelId: string): AIProvider => {
  const normalizedModelId = modelId.toLowerCase()

  // Check each provider's patterns
  for (const [provider, patterns] of Object.entries(PROVIDER_PATTERNS)) {
    if (provider === 'other') continue

    for (const pattern of patterns) {
      if (normalizedModelId.includes(pattern)) {
        return provider as AIProvider
      }
    }
  }

  // Default to 'other' if no match found
  return 'other'
}
