/**
 * Tool Accuracy Scorer
 *
 * Checks whether the model selected the correct MCP tool(s) for a given prompt.
 * Parses the [TOOL_CALLS] section from the provider output and compares against
 * the expected_tools variable defined in each test case.
 *
 * Scoring:
 *   pass = true  if ANY expected tool appears in the model's tool calls
 *   score = (matched tools / expected tools)
 *
 * Expected test vars:
 *   expected_tools: comma-separated list of acceptable tool names
 *                   e.g. "get_player_info_tool,get_player_profile"
 */
module.exports = (output, context) => {
  const { vars } = context;
  const expectedToolsRaw = vars?.expected_tools || '';
  const expectedTools = expectedToolsRaw
    .split(',')
    .map((t) => t.trim().toLowerCase())
    .filter(Boolean);

  if (expectedTools.length === 0) {
    return { pass: true, score: 1, reason: 'No expected_tools defined — skipping tool accuracy check' };
  }

  // Parse tool calls from structured output
  const toolCallMatch = output.match(/\[TOOL_CALLS\]([\s\S]*?)\[\/TOOL_CALLS\]/);
  if (!toolCallMatch) {
    return {
      pass: false,
      score: 0,
      reason: `No tool calls detected. Expected one of: ${expectedTools.join(', ')}`,
    };
  }

  const toolCallBlock = toolCallMatch[1];

  // Extract tool names from lines like: get_player_info_tool({"player_names":["Patrick Mahomes"]})
  const calledTools = [];
  const toolLineRegex = /^(\w+)\(/gm;
  let match;
  while ((match = toolLineRegex.exec(toolCallBlock)) !== null) {
    calledTools.push(match[1].toLowerCase());
  }

  if (calledTools.length === 0) {
    return {
      pass: false,
      score: 0,
      reason: `Could not parse tool names from output. Expected one of: ${expectedTools.join(', ')}`,
    };
  }

  // Check if any expected tool was called
  const matchedTools = expectedTools.filter((et) => calledTools.includes(et));
  const anyMatch = matchedTools.length > 0;
  const score = matchedTools.length / expectedTools.length;

  // Also check for unexpected tool calls (informational, doesn't fail)
  const unexpectedTools = calledTools.filter(
    (ct) => !expectedTools.includes(ct)
  );

  const parts = [
    `Called: ${calledTools.join(', ')}`,
    `Expected (any of): ${expectedTools.join(', ')}`,
    `Matched: ${matchedTools.length > 0 ? matchedTools.join(', ') : 'none'}`,
  ];

  if (unexpectedTools.length > 0) {
    parts.push(`Additional tools called: ${unexpectedTools.join(', ')}`);
  }

  return {
    pass: anyMatch,
    score,
    reason: parts.join(' | '),
  };
};
