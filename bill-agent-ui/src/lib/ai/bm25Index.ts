/**
 * BM25 index builder for tool filtering
 * Builds and queries a BM25 index from tool metadata for client-side tool search
 */

import BM25, { type BMDocument } from 'okapibm25'
import { extractAllToolMetadata, getSearchableTexts, type ToolMetadata, type AITool } from './toolMetadata'

/**
 * BM25 index for tool search
 * Stores searchable documents and metadata for ranking tools by relevance
 */
export interface BM25Index {
  /** Array of searchable text documents (one per tool) */
  documents: string[]
  /** Tool metadata corresponding to each document */
  metadata: ToolMetadata[]
}

/**
 * Result from a BM25 search with tool metadata
 */
export interface BM25SearchResult {
  /** The tool object */
  tool: AITool
  /** The tool's name */
  name: string
  /** BM25 relevance score */
  score: number
}

/**
 * Builds a BM25 index from an array of AI tools
 * @param tools - Array of AI SDK tools
 * @returns BM25Index containing searchable documents and metadata
 */
export function buildBM25Index(tools: AITool[]): BM25Index {
  const metadata = extractAllToolMetadata(tools)
  const documents = getSearchableTexts(metadata)

  return {
    documents,
    metadata
  }
}

/**
 * Tokenizes a search query into keywords
 * Splits on whitespace and converts to lowercase
 * @param query - The search query string
 * @returns Array of lowercase keywords
 */
function tokenizeQuery(query: string): string[] {
  return query
    .toLowerCase()
    .split(/\s+/)
    .filter(word => word.length > 0)
}

/**
 * Searches the BM25 index and returns top-k ranked tools
 * @param index - The BM25 index to search
 * @param query - The search query (user message)
 * @param topK - Number of top results to return (default: 7)
 * @returns Array of top-k tools with scores, sorted by relevance (highest first)
 */
export function searchBM25Index(
  index: BM25Index,
  query: string,
  topK: number = 7
): BM25SearchResult[] {
  // Tokenize the query into keywords
  const keywords = tokenizeQuery(query)

  // If no keywords, return empty results
  if (keywords.length === 0) {
    return []
  }

  // Score documents using BM25 with default constants (k1=1.2, b=0.75)
  // Use sorter to get BMDocument[] with scores
  const sorter = (a: BMDocument, b: BMDocument) => b.score - a.score
  const results = BM25(index.documents, keywords, undefined, sorter) as BMDocument[]

  // Map results to tool objects and take top-k
  return results
    .slice(0, topK)
    .map((result) => ({
      tool: index.metadata[results.indexOf(result)].originalTool,
      name: index.metadata[results.indexOf(result)].name,
      score: result.score
    }))
    .filter(result => result.score > 0) // Filter out zero-score results
}

/**
 * Gets the tool names from search results
 * Useful for creating the activeTools list for prepareStep
 * @param results - Array of BM25 search results
 * @returns Array of tool names
 */
export function getToolNames(results: BM25SearchResult[]): string[] {
  return results.map(r => r.name)
}

/**
 * Gets the original tools from search results
 * @param results - Array of BM25 search results
 * @returns Array of AI tools
 */
export function getTools(results: BM25SearchResult[]): AITool[] {
  return results.map(r => r.tool)
}
