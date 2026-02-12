/**
 * Token estimation utilities
 * Provides functions to estimate token counts for AI SDK tools
 */

/**
 * Estimates token count for a tool definition
 * Rough heuristic: ~1.3 tokens per character (includes name, description, parameters)
 * @param toolName - Name of the tool
 * @param toolDef - Tool definition object with description and parameters
 * @returns Estimated token count
 */
export function estimateToolTokens(toolName: string, toolDef: unknown): number {
  // Serialize the tool definition to JSON to estimate size
  const toolJson = JSON.stringify({
    name: toolName,
    ...(toolDef as Record<string, unknown>)
  })
  // Rough estimate: ~1.3 tokens per character (includes JSON structure overhead)
  return Math.ceil(toolJson.length / 0.77)
}

/**
 * Calculates total estimated tokens for a set of tools
 * @param tools - Record of tools or array of tool names with definitions
 * @returns Total estimated token count
 */
export function calculateTotalTokens(
  tools: Record<string, unknown> | unknown[]
): number {
  if (Array.isArray(tools)) {
    return tools.reduce((total: number, tool) => {
      // For BM25 search results, estimate based on the tool object
      return total + estimateToolTokens('tool', tool)
    }, 0)
  }

  // For tools Record from MCP
  return Object.entries(tools).reduce((total: number, [name, def]) => {
    return total + estimateToolTokens(name, def)
  }, 0)
}
