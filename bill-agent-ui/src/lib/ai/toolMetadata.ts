/**
 * Tool metadata extraction utility
 * Extracts name, description, and parameter schemas from MCP tools for search and filtering
 */

/**
 * Represents a tool from the AI SDK / MCP client
 * This is a minimal interface based on the AI SDK tool structure
 */
export interface AITool {
  name: string
  description?: string
  parameters?: {
    type?: string
    properties?: Record<string, unknown>
    required?: string[]
    [key: string]: unknown
  }
  [key: string]: unknown
}

/**
 * Extracted metadata for a tool, optimized for search and filtering
 */
export interface ToolMetadata {
  name: string
  description: string
  parameterNames: string[]
  searchableText: string
  originalTool: AITool
}

/**
 * Extracts parameter names from a JSON schema object
 * @param parameters - The tool's parameter schema
 * @returns Array of parameter names
 */
function extractParameterNames(parameters?: AITool['parameters']): string[] {
  if (!parameters?.properties) return []
  return Object.keys(parameters.properties)
}

/**
 * Creates searchable text from tool metadata
 * Combines name, description, and parameter names into a single searchable string
 * @param name - Tool name
 * @param description - Tool description
 * @param parameterNames - Array of parameter names
 * @returns Combined searchable text
 */
function createSearchableText(
  name: string,
  description: string,
  parameterNames: string[]
): string {
  const parts = [name, description, ...parameterNames].filter(Boolean)

  return parts.join(' ')
}

/**
 * Extracts metadata from a single tool
 * @param tool - The AI SDK tool object
 * @returns Extracted metadata
 */
export function extractToolMetadata(tool: AITool): ToolMetadata {
  const name = tool.name
  const description = tool.description || ''
  const parameterNames = extractParameterNames(tool.parameters)
  const searchableText = createSearchableText(name, description, parameterNames)

  return {
    name,
    description,
    parameterNames,
    searchableText,
    originalTool: tool
  }
}

/**
 * Extracts metadata from an array of tools
 * @param tools - Array of AI SDK tools
 * @returns Array of extracted metadata
 */
export function extractAllToolMetadata(tools: AITool[]): ToolMetadata[] {
  return tools.map(extractToolMetadata)
}

/**
 * Finds tools by name from metadata array
 * @param metadata - Array of tool metadata
 * @param names - Tool names to find
 * @returns Array of matching tools
 */
export function findToolsByName(
  metadata: ToolMetadata[],
  names: string[]
): AITool[] {
  const nameSet = new Set(names)
  return metadata.filter((m) => nameSet.has(m.name)).map((m) => m.originalTool)
}

/**
 * Gets searchable text for all tools
 * Useful for building search indices (e.g., BM25)
 * @param metadata - Array of tool metadata
 * @returns Array of searchable text strings, one per tool
 */
export function getSearchableTexts(metadata: ToolMetadata[]): string[] {
  return metadata.map((m) => m.searchableText)
}
