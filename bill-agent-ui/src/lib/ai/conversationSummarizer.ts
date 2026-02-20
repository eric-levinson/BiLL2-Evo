/**
 * Conversation summarization for long chat sessions
 *
 * Compresses older conversation history via a lightweight model (Haiku)
 * while preserving fantasy-specific context (player names, league settings,
 * trade decisions). Triggered when conversation exceeds a configurable
 * turn threshold.
 *
 * Configuration:
 * - SUMMARIZATION_TURN_THRESHOLD: Turn pairs before summarization triggers (default: 10)
 * - SUMMARIZATION_MODEL: Model ID for summarization (default: claude-haiku-4-5-20251001)
 *
 * Layer: @/lib/ai/ — called by the chat route as a pre-processing step.
 */

import { generateText, type UIMessage } from 'ai'
import { createModelInstance } from './modelFactory'

const SUMMARIZATION_PROMPT = `Summarize this fantasy football conversation concisely. Preserve:
- Player names and positions discussed
- League settings (scoring format, roster size, league size)
- Key conclusions or decisions reached
- Trade proposals discussed and outcomes
- Roster moves recommended
- User preferences expressed (risk tolerance, league type)

Be factual. Do not add analysis. Keep under 500 tokens.`

const DEFAULT_TURN_THRESHOLD = 10
const DEFAULT_RECENT_TURNS_TO_KEEP = 4
const DEFAULT_SUMMARIZATION_MODEL = 'claude-haiku-4-5-20251001'

/**
 * Count user-assistant turn pairs in a messages array.
 * A turn pair = one user message followed by assistant response(s).
 * Tool calls are part of the assistant turn, not separate turns.
 */
export function countTurnPairs(messages: UIMessage[]): number {
  let count = 0
  for (const message of messages) {
    if (message.role === 'user') {
      count++
    }
  }
  return count
}

/**
 * Extract text content from a UIMessage.
 * Handles AI SDK v6 parts array format.
 */
function extractMessageText(message: UIMessage): string {
  if (message.parts && message.parts.length > 0) {
    return message.parts
      .filter((p): p is { type: 'text'; text: string } => p.type === 'text')
      .map((p) => p.text)
      .join('\n')
  }
  return ''
}

/**
 * Format messages into a readable transcript for the summarization model.
 * Only includes user and assistant text content — tool calls are omitted.
 */
function formatTranscript(messages: UIMessage[]): string {
  return messages
    .filter((m) => m.role === 'user' || m.role === 'assistant')
    .map((m) => {
      const text = extractMessageText(m)
      if (!text) return null
      const role = m.role === 'user' ? 'User' : 'Assistant'
      return `${role}: ${text}`
    })
    .filter(Boolean)
    .join('\n\n')
}

/**
 * Split messages into older (to summarize) and recent (to keep verbatim).
 * Keeps the last `recentTurnsToKeep` user messages and all messages after them.
 */
function splitMessages(
  messages: UIMessage[],
  recentTurnsToKeep: number
): { older: UIMessage[]; recent: UIMessage[] } | null {
  let userCount = 0
  let splitIndex = messages.length

  for (let i = messages.length - 1; i >= 0; i--) {
    if (messages[i].role === 'user') {
      userCount++
      if (userCount >= recentTurnsToKeep) {
        splitIndex = i
        break
      }
    }
  }

  if (splitIndex <= 0) return null

  return {
    older: messages.slice(0, splitIndex),
    recent: messages.slice(splitIndex)
  }
}

export interface SummarizationResult {
  /** Compressed summary of older conversation turns */
  summary: string
  /** Recent messages kept verbatim for the LLM */
  trimmedMessages: UIMessage[]
}

/**
 * Summarize older conversation turns if the conversation exceeds the turn threshold.
 * Returns null if no summarization is needed.
 */
export async function maybeSummarize(
  messages: UIMessage[]
): Promise<SummarizationResult | null> {
  const threshold = parseInt(
    process.env.SUMMARIZATION_TURN_THRESHOLD || String(DEFAULT_TURN_THRESHOLD),
    10
  )
  const modelId = process.env.SUMMARIZATION_MODEL || DEFAULT_SUMMARIZATION_MODEL

  const turnCount = countTurnPairs(messages)
  if (turnCount <= threshold) return null

  const split = splitMessages(messages, DEFAULT_RECENT_TURNS_TO_KEEP)
  if (!split) return null

  const transcript = formatTranscript(split.older)
  if (!transcript.trim()) return null

  console.log(
    `[Summarization] Compressing ${turnCount} turns (threshold: ${threshold}, keeping last ${DEFAULT_RECENT_TURNS_TO_KEEP} verbatim)`
  )

  const startTime = performance.now()

  const { text: summary } = await generateText({
    model: createModelInstance(modelId),
    maxOutputTokens: 1024,
    messages: [
      {
        role: 'user',
        content: `${SUMMARIZATION_PROMPT}\n\n---\n\n${transcript}`
      }
    ]
  })

  const elapsed = (performance.now() - startTime).toFixed(0)
  console.log(
    `[Summarization] Summary generated in ${elapsed}ms (${summary.length} chars)`
  )

  return {
    summary,
    trimmedMessages: split.recent
  }
}
