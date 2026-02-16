/**
 * Step Efficiency Scorer
 *
 * Counts the number of tool calls (steps) in the model's response and compares
 * against the expected range defined in test vars.
 *
 * Scoring:
 *   pass = true  if step count is within [expected_min_steps, expected_max_steps]
 *   score = 1.0 if within range, scaled down proportionally if over
 *
 * Expected test vars:
 *   expected_min_steps: minimum acceptable tool calls (default 1)
 *   expected_max_steps: maximum acceptable tool calls (default 10)
 */
module.exports = (output, context) => {
  const { vars } = context;
  const minSteps = parseInt(vars?.expected_min_steps, 10) || 1;
  const maxSteps = parseInt(vars?.expected_max_steps, 10) || 10;

  // Parse tool calls from structured output
  const toolCallMatch = output.match(/\[TOOL_CALLS\]([\s\S]*?)\[\/TOOL_CALLS\]/);

  let stepCount = 0;
  if (toolCallMatch) {
    const toolCallBlock = toolCallMatch[1];
    // Count lines that look like tool calls: tool_name({...})
    const toolLines = toolCallBlock
      .split('\n')
      .filter((line) => /^\w+\(/.test(line.trim()));
    stepCount = toolLines.length;
  }

  // Determine pass/fail
  const withinRange = stepCount >= minSteps && stepCount <= maxSteps;
  const tooFew = stepCount < minSteps;
  const tooMany = stepCount > maxSteps;

  // Calculate score
  let score;
  if (withinRange) {
    // Perfect score if within range; slightly favor fewer steps
    score = 1.0 - (stepCount - minSteps) / (maxSteps - minSteps + 1) * 0.2;
  } else if (tooMany) {
    // Penalize proportionally for excess steps
    const excessRatio = (stepCount - maxSteps) / maxSteps;
    score = Math.max(0, 1.0 - excessRatio);
  } else {
    // Too few steps (possibly no tool calls at all)
    score = stepCount === 0 ? 0 : stepCount / minSteps;
  }

  const parts = [
    `Steps: ${stepCount}`,
    `Expected range: ${minSteps}-${maxSteps}`,
  ];

  if (withinRange) {
    parts.push('Within expected range');
  } else if (tooMany) {
    parts.push(`Exceeded maximum by ${stepCount - maxSteps} steps`);
  } else if (tooFew) {
    parts.push(
      stepCount === 0
        ? 'No tool calls detected (model may have answered from memory)'
        : `Below minimum (${stepCount} < ${minSteps})`
    );
  }

  return {
    pass: withinRange,
    score: Math.round(score * 100) / 100,
    reason: parts.join(' | '),
  };
};
