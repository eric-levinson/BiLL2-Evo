import { describe, it, expect, vi } from 'vitest'
import type { UIMessage } from 'ai'
import { countTurnPairs, maybeSummarize } from './conversationSummarizer'

// Mock generateText so maybeSummarize never calls the real API
vi.mock('ai', async (importOriginal) => {
  const actual = await importOriginal<typeof import('ai')>()
  return {
    ...actual,
    generateText: vi
      .fn()
      .mockResolvedValue({ text: 'Mock summary of conversation.' })
  }
})

// Mock the model factory since it requires provider SDK packages
vi.mock('./modelFactory', () => ({
  createModelInstance: vi.fn().mockReturnValue({})
}))

/** Helper to create a minimal UIMessage for testing. */
function msg(role: 'user' | 'assistant' | 'tool', text: string): UIMessage {
  return {
    id: crypto.randomUUID(),
    role,
    parts: [{ type: 'text', text }]
  } as UIMessage
}

/** Build a conversation with N user-assistant turn pairs. */
function buildConversation(turnCount: number): UIMessage[] {
  const messages: UIMessage[] = []
  for (let i = 1; i <= turnCount; i++) {
    messages.push(msg('user', `Question ${i}`))
    messages.push(msg('assistant', `Answer ${i}`))
  }
  return messages
}

// ---------------------------------------------------------------------------
// countTurnPairs
// ---------------------------------------------------------------------------
describe('countTurnPairs', () => {
  it('returns 0 for empty array', () => {
    expect(countTurnPairs([])).toBe(0)
  })

  it('counts user messages only', () => {
    const messages = [
      msg('user', 'Hello'),
      msg('assistant', 'Hi there'),
      msg('user', 'Who should I start?'),
      msg('assistant', 'Start Player A')
    ]
    expect(countTurnPairs(messages)).toBe(2)
  })

  it('ignores tool messages', () => {
    const messages = [
      msg('user', 'Trade advice?'),
      msg('assistant', 'Let me check...'),
      msg('tool', '{"result": "data"}'),
      msg('assistant', 'Here is my analysis'),
      msg('user', 'Thanks')
    ]
    expect(countTurnPairs(messages)).toBe(2)
  })

  it('handles consecutive user messages', () => {
    const messages = [
      msg('user', 'First'),
      msg('user', 'Second'),
      msg('assistant', 'Response')
    ]
    expect(countTurnPairs(messages)).toBe(2)
  })

  it('handles assistant-only messages', () => {
    const messages = [msg('assistant', 'Welcome')]
    expect(countTurnPairs(messages)).toBe(0)
  })
})

// ---------------------------------------------------------------------------
// maybeSummarize (tests split logic + threshold gating)
// ---------------------------------------------------------------------------
describe('maybeSummarize', () => {
  it('returns null when under threshold', async () => {
    const messages = buildConversation(5)
    const result = await maybeSummarize(messages)
    expect(result).toBeNull()
  })

  it('returns null at exactly the threshold', async () => {
    const messages = buildConversation(10)
    const result = await maybeSummarize(messages)
    expect(result).toBeNull()
  })

  it('summarizes when over threshold', async () => {
    const messages = buildConversation(11)
    const result = await maybeSummarize(messages)
    expect(result).not.toBeNull()
    expect(result!.summary).toBe('Mock summary of conversation.')
  })

  it('keeps last 4 user turns verbatim in trimmedMessages', async () => {
    const messages = buildConversation(12) // 24 messages total
    const result = await maybeSummarize(messages)
    expect(result).not.toBeNull()

    // Count user messages in trimmedMessages — should be 4
    const recentUserCount = result!.trimmedMessages.filter(
      (m) => m.role === 'user'
    ).length
    expect(recentUserCount).toBe(4)

    // The first recent user message should be "Question 9" (12 - 4 + 1)
    const firstRecentUser = result!.trimmedMessages.find(
      (m) => m.role === 'user'
    )
    expect(firstRecentUser!.parts![0]).toEqual({
      type: 'text',
      text: 'Question 9'
    })
  })

  it('trimmedMessages + older messages equal original count', async () => {
    const messages = buildConversation(15) // 30 messages total
    const result = await maybeSummarize(messages)
    expect(result).not.toBeNull()

    // older count = total - trimmed
    const olderCount = messages.length - result!.trimmedMessages.length
    expect(olderCount + result!.trimmedMessages.length).toBe(messages.length)
    expect(olderCount).toBeGreaterThan(0)
  })
})
