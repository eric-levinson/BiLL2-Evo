/**
 * BiLL2 Custom Promptfoo Provider
 *
 * Calls LLM APIs directly with BiLL2's system prompt and MCP tool definitions.
 * Supports single-turn (prompt only) and multi-turn (prompt + mock tool results)
 * message formats for realistic agent loop simulation.
 *
 * Config options (per-provider in promptfooconfig.yaml):
 *   modelId:      Model identifier (e.g. "claude-sonnet-4-5-20250929")
 *   maxTokens:    Max response tokens (default 4096)
 *   temperature:  Sampling temperature (default 0)
 *   includeTools: Whether to include MCP tool definitions (default true)
 *
 * Environment variables (loaded from bill-agent-ui/.env):
 *   ANTHROPIC_API_KEY, OPENAI_API_KEY, GOOGLE_GENERATIVE_AI_API_KEY
 */

const path = require('path');
const fs = require('fs');

// ---------------------------------------------------------------------------
// Env loader (avoids dotenv dependency)
// ---------------------------------------------------------------------------
function loadEnv(filePath) {
  if (!fs.existsSync(filePath)) return;
  const content = fs.readFileSync(filePath, 'utf-8');
  for (const line of content.split('\n')) {
    const trimmed = line.trim();
    if (!trimmed || trimmed.startsWith('#')) continue;
    const eqIdx = trimmed.indexOf('=');
    if (eqIdx === -1) continue;
    const key = trimmed.slice(0, eqIdx).trim();
    const value = trimmed.slice(eqIdx + 1).trim().replace(/^["']|["']$/g, '');
    if (!process.env[key]) process.env[key] = value;
  }
}

// Load API keys from bill-agent-ui/.env
const envPath = path.resolve(__dirname, '../../bill-agent-ui/.env');
loadEnv(envPath);

// ---------------------------------------------------------------------------
// Load system prompt and tool definitions
// ---------------------------------------------------------------------------
const SYSTEM_PROMPT = fs.readFileSync(
  path.resolve(__dirname, '../prompts/system.txt'),
  'utf-8'
);

const TOOL_DEFS = JSON.parse(
  fs.readFileSync(
    path.resolve(__dirname, '../tools/definitions.json'),
    'utf-8'
  )
);

// ---------------------------------------------------------------------------
// Provider detection
// ---------------------------------------------------------------------------
function detectProvider(modelId) {
  if (modelId.startsWith('claude')) return 'anthropic';
  if (modelId.startsWith('gpt') || modelId.startsWith('o1') || modelId.startsWith('o3')) return 'openai';
  if (modelId.startsWith('gemini')) return 'google';
  return 'openai'; // fallback
}

// ---------------------------------------------------------------------------
// Load mock tool results from file:// reference or inline JSON
// ---------------------------------------------------------------------------
function loadToolResults(toolResultsVar) {
  if (!toolResultsVar) return null;

  let data;
  if (typeof toolResultsVar === 'string') {
    // If it looks like JSON (starts with [ or {), parse directly
    const trimmed = toolResultsVar.trim();
    if (trimmed.startsWith('[') || trimmed.startsWith('{')) {
      data = JSON.parse(trimmed);
    } else {
      // Treat as file path (promptfoo resolves file:// refs to content strings)
      data = JSON.parse(trimmed);
    }
  } else {
    data = toolResultsVar;
  }

  // Normalize to array
  return Array.isArray(data) ? data : [data];
}

// ---------------------------------------------------------------------------
// Convert neutral tool definitions to API-specific formats
// ---------------------------------------------------------------------------
function toAnthropicTools(tools) {
  return tools.map((t) => ({
    name: t.name,
    description: t.description,
    input_schema: t.parameters,
  }));
}

function toOpenAITools(tools) {
  return tools.map((t) => ({
    type: 'function',
    function: {
      name: t.name,
      description: t.description,
      parameters: t.parameters,
    },
  }));
}

function toGoogleTools(tools) {
  return tools.map((t) => ({
    name: t.name,
    description: t.description,
    parameters: t.parameters,
  }));
}

// ---------------------------------------------------------------------------
// Build multi-turn messages per provider API format
// ---------------------------------------------------------------------------

/**
 * Build Anthropic messages array with tool_use/tool_result pairs.
 * Format: [user prompt] -> [assistant tool_use] -> [user tool_result] for each tool
 */
function buildAnthropicMessages(prompt, toolResults) {
  if (!toolResults || toolResults.length === 0) {
    return [{ role: 'user', content: prompt }];
  }

  const messages = [];
  // 1. User asks the question
  messages.push({ role: 'user', content: prompt });

  // 2. For each tool result, simulate assistant calling tool then user providing result
  for (let i = 0; i < toolResults.length; i++) {
    const tr = toolResults[i];
    const toolUseId = `toolu_mock_${i}`;

    // Assistant makes the tool call
    messages.push({
      role: 'assistant',
      content: [
        {
          type: 'tool_use',
          id: toolUseId,
          name: tr.tool_name,
          input: tr.tool_input || {},
        },
      ],
    });

    // User provides tool result
    messages.push({
      role: 'user',
      content: [
        {
          type: 'tool_result',
          tool_use_id: toolUseId,
          content: JSON.stringify(tr.tool_output),
        },
      ],
    });
  }

  return messages;
}

/**
 * Build OpenAI messages array with tool_calls/tool responses.
 */
function buildOpenAIMessages(prompt, toolResults) {
  const messages = [
    { role: 'system', content: SYSTEM_PROMPT },
    { role: 'user', content: prompt },
  ];

  if (!toolResults || toolResults.length === 0) {
    return messages;
  }

  // Assistant makes all tool calls in one message
  const toolCalls = toolResults.map((tr, i) => ({
    id: `call_mock_${i}`,
    type: 'function',
    function: {
      name: tr.tool_name,
      arguments: JSON.stringify(tr.tool_input || {}),
    },
  }));

  messages.push({
    role: 'assistant',
    content: null,
    tool_calls: toolCalls,
  });

  // Each tool result is a separate tool message
  for (let i = 0; i < toolResults.length; i++) {
    messages.push({
      role: 'tool',
      tool_call_id: `call_mock_${i}`,
      content: JSON.stringify(toolResults[i].tool_output),
    });
  }

  return messages;
}

/**
 * Build Google messages array with tool data embedded as text.
 *
 * Gemini 3 Flash requires thought_signature in functionCall parts and
 * can't handle arrays as functionResponse protobuf Struct values.
 * Instead of fighting the native tool format, we embed mock tool output
 * as structured text — the model still gets full context for analysis.
 */
function buildGoogleMessages(prompt, toolResults) {
  if (!toolResults || toolResults.length === 0) {
    return [{ role: 'user', parts: [{ text: prompt }] }];
  }

  // Build a text block summarizing the tool calls and their results
  const toolContextParts = toolResults.map((tr) => {
    const input = JSON.stringify(tr.tool_input || {}, null, 2);
    const output = JSON.stringify(tr.tool_output, null, 2);
    return `Tool: ${tr.tool_name}\nInput: ${input}\nResult:\n${output}`;
  });

  const toolContext = toolContextParts.join('\n\n---\n\n');

  // Single user message with the original prompt plus tool context
  const fullPrompt =
    `${prompt}\n\n` +
    `The following tool calls have already been made and returned these results. ` +
    `Use this data to answer the question above.\n\n${toolContext}`;

  return [{ role: 'user', parts: [{ text: fullPrompt }] }];
}

// ---------------------------------------------------------------------------
// Fetch with rate-limit retry (handles 429 + Retry-After)
// ---------------------------------------------------------------------------
async function fetchWithRetry(url, options, providerName, maxRetries = 5) {
  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    const res = await fetch(url, options);
    if (res.status === 429 && attempt < maxRetries) {
      const retryAfter = parseInt(res.headers.get('retry-after') || '0', 10);
      // Exponential backoff: 10s, 20s, 40s, 60s, 60s (capped)
      const backoffMs = Math.min(10000 * Math.pow(2, attempt), 60000);
      const delayMs = retryAfter > 0 ? retryAfter * 1000 : backoffMs;
      console.warn(
        `[bill2-chat][${providerName}] Rate limited (429). Retrying in ${Math.round(delayMs / 1000)}s (attempt ${attempt + 1}/${maxRetries})` +
        (retryAfter > 0 ? ` [Retry-After: ${retryAfter}s]` : '')
      );
      await new Promise((resolve) => setTimeout(resolve, delayMs));
      continue;
    }
    return res;
  }
  throw new Error(`[${providerName}] Rate limit exceeded after ${maxRetries} retries`);
}

function truncateError(text, maxLen = 500) {
  return text.length > maxLen ? text.slice(0, maxLen) + '...[truncated]' : text;
}

// ---------------------------------------------------------------------------
// API callers (updated for multi-turn)
// ---------------------------------------------------------------------------
async function callAnthropic(modelId, prompt, tools, maxTokens, temperature, toolResults) {
  const apiKey = process.env.ANTHROPIC_API_KEY;
  if (!apiKey) throw new Error('ANTHROPIC_API_KEY environment variable is required but not set');

  const messages = buildAnthropicMessages(prompt, toolResults);

  const body = {
    model: modelId,
    max_tokens: maxTokens,
    temperature,
    system: SYSTEM_PROMPT,
    messages,
  };
  if (tools.length > 0) {
    body.tools = toAnthropicTools(tools);
    body.tool_choice = { type: 'auto' };
  }

  const res = await fetchWithRetry('https://api.anthropic.com/v1/messages', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'x-api-key': apiKey,
      'anthropic-version': '2023-06-01',
    },
    body: JSON.stringify(body),
  }, `Anthropic/${modelId}`);

  if (!res.ok) {
    const errText = truncateError(await res.text());
    throw new Error(`Anthropic API ${res.status}: ${errText}`);
  }

  const data = await res.json();
  const textParts = [];
  const toolCalls = [];

  for (const block of data.content || []) {
    if (block.type === 'text') textParts.push(block.text);
    if (block.type === 'tool_use') {
      toolCalls.push({ name: block.name, arguments: block.input });
    }
  }

  return {
    text: textParts.join('\n'),
    toolCalls,
    stopReason: data.stop_reason,
    tokenUsage: {
      prompt: data.usage?.input_tokens || 0,
      completion: data.usage?.output_tokens || 0,
      total: (data.usage?.input_tokens || 0) + (data.usage?.output_tokens || 0),
    },
  };
}

async function callOpenAI(modelId, prompt, tools, maxTokens, temperature, toolResults) {
  const apiKey = process.env.OPENAI_API_KEY;
  if (!apiKey) throw new Error('OPENAI_API_KEY environment variable is required but not set');

  const messages = buildOpenAIMessages(prompt, toolResults);

  const body = {
    model: modelId,
    max_completion_tokens: maxTokens,
    messages,
  };
  // Some OpenAI models (e.g. gpt-5-mini) only support default temperature
  if (temperature > 0) body.temperature = temperature;
  if (tools.length > 0) {
    body.tools = toOpenAITools(tools);
    body.tool_choice = 'auto';
  }

  const res = await fetchWithRetry('https://api.openai.com/v1/chat/completions', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${apiKey}`,
    },
    body: JSON.stringify(body),
  }, `OpenAI/${modelId}`);

  if (!res.ok) {
    const errText = truncateError(await res.text());
    throw new Error(`OpenAI API ${res.status}: ${errText}`);
  }

  const data = await res.json();
  const choice = data.choices?.[0];
  const message = choice?.message || {};
  const toolCalls = (message.tool_calls || []).map((tc) => ({
    name: tc.function?.name,
    arguments: JSON.parse(tc.function?.arguments || '{}'),
  }));

  return {
    text: message.content || '',
    toolCalls,
    stopReason: choice?.finish_reason,
    tokenUsage: {
      prompt: data.usage?.prompt_tokens || 0,
      completion: data.usage?.completion_tokens || 0,
      total: data.usage?.total_tokens || 0,
    },
  };
}

async function callGoogle(modelId, prompt, tools, maxTokens, temperature, toolResults) {
  const apiKey = process.env.GOOGLE_GENERATIVE_AI_API_KEY;
  if (!apiKey) throw new Error('GOOGLE_GENERATIVE_AI_API_KEY environment variable is required but not set');

  const contents = buildGoogleMessages(prompt, toolResults);

  const body = {
    systemInstruction: { parts: [{ text: SYSTEM_PROMPT }] },
    contents,
    generationConfig: { maxOutputTokens: maxTokens, temperature },
  };
  if (tools.length > 0) {
    body.tools = [{ functionDeclarations: toGoogleTools(tools) }];
  }

  const url = `https://generativelanguage.googleapis.com/v1beta/models/${modelId}:generateContent`;
  const res = await fetchWithRetry(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'x-goog-api-key': apiKey,
    },
    body: JSON.stringify(body),
  }, `Google/${modelId}`);

  if (!res.ok) {
    const errText = truncateError(await res.text());
    throw new Error(`Google API ${res.status}: ${errText}`);
  }

  const data = await res.json();
  const parts = data.candidates?.[0]?.content?.parts || [];
  const textParts = [];
  const toolCalls = [];

  for (const part of parts) {
    if (part.text) textParts.push(part.text);
    if (part.functionCall) {
      toolCalls.push({ name: part.functionCall.name, arguments: part.functionCall.args || {} });
    }
  }

  const usage = data.usageMetadata || {};
  return {
    text: textParts.join('\n'),
    toolCalls,
    stopReason: data.candidates?.[0]?.finishReason,
    tokenUsage: {
      prompt: usage.promptTokenCount || 0,
      completion: usage.candidatesTokenCount || 0,
      total: (usage.promptTokenCount || 0) + (usage.candidatesTokenCount || 0),
    },
  };
}

// ---------------------------------------------------------------------------
// Promptfoo Provider class
// ---------------------------------------------------------------------------
class Bill2ChatProvider {
  constructor(options) {
    this.modelId = options.config?.modelId || 'claude-sonnet-4-5-20250929';
    this.maxTokens = options.config?.maxTokens || 4096;
    this.temperature = options.config?.temperature ?? 0;
    this.includeTools = options.config?.includeTools !== false; // default true
    this.label = options.config?.label || this.modelId;
    this._id = `bill2:${this.modelId}`;
  }

  id() {
    return this._id;
  }

  async callApi(prompt, context) {
    const provider = detectProvider(this.modelId);
    const tools = this.includeTools ? TOOL_DEFS : [];

    // Check for multi-turn tool results in test vars
    let toolResults = null;
    try {
      toolResults = loadToolResults(context?.vars?.tool_results);
    } catch (e) {
      console.warn(`[bill2-chat] Failed to parse tool_results: ${e.message}`);
    }

    let result;
    switch (provider) {
      case 'anthropic':
        result = await callAnthropic(this.modelId, prompt, tools, this.maxTokens, this.temperature, toolResults);
        break;
      case 'openai':
        result = await callOpenAI(this.modelId, prompt, tools, this.maxTokens, this.temperature, toolResults);
        break;
      case 'google':
        result = await callGoogle(this.modelId, prompt, tools, this.maxTokens, this.temperature, toolResults);
        break;
      default:
        throw new Error(`Unknown provider for model: ${this.modelId}`);
    }

    // Build structured output: tool calls section + response text
    const outputParts = [];

    if (result.toolCalls.length > 0) {
      outputParts.push('[TOOL_CALLS]');
      for (const tc of result.toolCalls) {
        outputParts.push(`${tc.name}(${JSON.stringify(tc.arguments)})`);
      }
      outputParts.push('[/TOOL_CALLS]');
    }

    if (result.text) {
      outputParts.push('[RESPONSE]');
      outputParts.push(result.text);
      outputParts.push('[/RESPONSE]');
    }

    // If model only made tool calls with no text, add a note
    if (result.toolCalls.length > 0 && !result.text) {
      outputParts.push('[RESPONSE]');
      outputParts.push(`Model selected tool(s): ${result.toolCalls.map((tc) => tc.name).join(', ')}`);
      outputParts.push('[/RESPONSE]');
    }

    return {
      output: outputParts.join('\n'),
      tokenUsage: result.tokenUsage,
    };
  }
}

module.exports = Bill2ChatProvider;
