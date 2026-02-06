/**
 * Model factory for provider-agnostic model instantiation
 * Creates the correct AI SDK model instance based on the detected provider
 */

import { anthropic } from '@ai-sdk/anthropic'
import { openai } from '@ai-sdk/openai'
import { google } from '@ai-sdk/google'
import { type AIProvider, detectProvider } from './providerDetection'

/**
 * Creates an AI SDK model instance for the given model ID
 *
 * Automatically detects the provider from the model ID and uses the
 * corresponding AI SDK provider package.
 *
 * @param modelId - The model identifier (e.g., 'claude-sonnet-4-5-20250929', 'gpt-4o', 'gemini-2.0-flash')
 * @returns An AI SDK LanguageModel instance
 *
 * @example
 * createModelInstance('claude-sonnet-4-5-20250929') // uses @ai-sdk/anthropic
 * createModelInstance('gpt-4o')                      // uses @ai-sdk/openai
 * createModelInstance('gemini-2.0-flash')             // uses @ai-sdk/google
 */
export function createModelInstance(modelId: string) {
  const provider = detectProvider(modelId)
  return createModelForProvider(provider, modelId)
}

function createModelForProvider(provider: AIProvider, modelId: string) {
  switch (provider) {
    case 'anthropic':
      return anthropic(modelId)
    case 'openai':
      return openai(modelId)
    case 'google':
      return google(modelId)
    case 'other':
      // Default to OpenAI-compatible API for unknown providers
      console.warn(`[Model Factory] Unknown provider for model '${modelId}', falling back to OpenAI SDK`)
      return openai(modelId)
  }
}
