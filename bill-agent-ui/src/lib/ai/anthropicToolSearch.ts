/**
 * Anthropic Tool Search integration module
 * Implements native Tool Search for Claude models using deferLoading optimization
 */

import { anthropic } from '@ai-sdk/anthropic'
import type { AITool } from './toolMetadata'

/**
 * Registers Anthropic's native Tool Search and marks all MCP tools for deferred loading
 *
 * This optimization reduces initial token usage by only sending the Tool Search meta-tool
 * to Claude initially. The agent then discovers and loads relevant tools on demand via
 * Anthropic's server-side BM25 indexing.
 *
 * @param tools - Array of MCP tools to optimize
 * @returns Modified tools array with Tool Search registered and deferLoading enabled
 *
 * @example
 * const mcpTools = await mcpClient.tools()
 * const optimizedTools = registerToolSearch(mcpTools)
 * // Only Tool Search meta-tool (~500 tokens) sent initially
 * // Claude discovers relevant tools on demand
 */
export function registerToolSearch(tools: AITool[]): unknown[] {
  // Mark all MCP tools with providerOptions.anthropic.deferLoading = true
  // This tells Anthropic to not send these tool definitions initially
  const deferredTools = tools.map(tool => {
    const existingProviderOptions = (tool.providerOptions || {}) as Record<string, unknown>
    const existingAnthropicOptions = (existingProviderOptions.anthropic || {}) as Record<string, unknown>

    return {
      ...tool,
      providerOptions: {
        ...existingProviderOptions,
        anthropic: {
          ...existingAnthropicOptions,
          deferLoading: true
        }
      }
    }
  })

  // Add Anthropic's native Tool Search meta-tool
  // This allows Claude to search and discover tools via server-side BM25 indexing
  const toolSearchTool = anthropic.tools.toolSearchBm25_20251119()

  // Return array with Tool Search first, followed by all deferred MCP tools
  return [toolSearchTool, ...deferredTools]
}

/**
 * Checks if Tool Search is supported for a given model ID
 *
 * @param modelId - The AI model identifier
 * @returns True if the model supports native Tool Search (Claude models)
 *
 * @example
 * supportsToolSearch('claude-sonnet-4-20250514') // => true
 * supportsToolSearch('gpt-4o') // => false
 */
export function supportsToolSearch(modelId: string): boolean {
  const normalized = modelId.toLowerCase()
  return normalized.includes('claude') || normalized.includes('anthropic')
}
