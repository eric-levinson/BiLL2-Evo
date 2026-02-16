/**
 * Chart Validity Scorer
 *
 * Validates chart JSON in the model's response. Checks:
 *   1. Presence of a ```chart code block
 *   2. Valid JSON structure
 *   3. Required fields (type, data, config)
 *   4. Appropriate chart type selection
 *   5. Scale separation (no mixing vastly different metric scales)
 *
 * Scoring:
 *   pass = true if valid chart JSON with all required fields
 *   score = checks_passed / total_checks
 */
module.exports = (output, context) => {
  const checks = [];
  let totalChecks = 0;
  let passedChecks = 0;

  function check(name, passed, detail) {
    totalChecks++;
    if (passed) passedChecks++;
    checks.push({ name, passed, detail });
  }

  // Get the full response text (could be in [RESPONSE] block or raw)
  const responseMatch = output.match(/\[RESPONSE\]([\s\S]*?)\[\/RESPONSE\]/);
  const responseText = responseMatch ? responseMatch[1] : output;

  // 1. Check for chart code block
  const chartBlockRegex = /```chart\s*\n([\s\S]*?)```/;
  const chartMatch = responseText.match(chartBlockRegex);

  check(
    'chart_block_present',
    !!chartMatch,
    chartMatch ? 'Found ```chart code block' : 'No ```chart code block found in response'
  );

  if (!chartMatch) {
    // Also check if there's chart-like JSON without the code fence
    const jsonLikeMatch = responseText.match(/\{\s*"type"\s*:\s*"(bar|line)"/);
    if (jsonLikeMatch) {
      check(
        'chart_json_unfenced',
        false,
        'Found chart-like JSON but not in a ```chart code fence'
      );
    }

    return {
      pass: false,
      score: passedChecks / Math.max(totalChecks, 1),
      reason: checks.map((c) => `${c.passed ? 'PASS' : 'FAIL'}: ${c.name} — ${c.detail}`).join('\n'),
    };
  }

  const chartJson = chartMatch[1].trim();

  // 2. Check valid JSON
  let chartData;
  try {
    chartData = JSON.parse(chartJson);
    check('valid_json', true, 'Chart JSON parses successfully');
  } catch (e) {
    check('valid_json', false, `JSON parse error: ${e.message}`);
    return {
      pass: false,
      score: passedChecks / totalChecks,
      reason: checks.map((c) => `${c.passed ? 'PASS' : 'FAIL'}: ${c.name} — ${c.detail}`).join('\n'),
    };
  }

  // 3. Check required fields
  check(
    'has_type',
    typeof chartData.type === 'string' && ['bar', 'line'].includes(chartData.type),
    chartData.type ? `type: "${chartData.type}"` : 'Missing or invalid "type" field'
  );

  check(
    'has_data',
    Array.isArray(chartData.data) && chartData.data.length > 0,
    Array.isArray(chartData.data) ? `${chartData.data.length} data points` : 'Missing or empty "data" array'
  );

  check(
    'has_config',
    typeof chartData.config === 'object' && chartData.config !== null,
    chartData.config ? 'Config object present' : 'Missing "config" object'
  );

  // 4. Check config fields
  if (chartData.config) {
    check(
      'has_title',
      typeof chartData.config.title === 'string' && chartData.config.title.length > 0,
      chartData.config?.title ? `title: "${chartData.config.title}"` : 'Missing chart title'
    );

    check(
      'has_axis_keys',
      typeof chartData.config.xKey === 'string' && Array.isArray(chartData.config.yKeys),
      `xKey: "${chartData.config?.xKey || 'missing'}", yKeys: ${JSON.stringify(chartData.config?.yKeys || 'missing')}`
    );
  }

  // 5. Scale separation check — only if we have data and multiple yKeys
  if (
    Array.isArray(chartData.data) &&
    chartData.data.length > 0 &&
    chartData.config?.yKeys?.length > 1
  ) {
    const yKeys = chartData.config.yKeys;
    const ranges = {};

    for (const key of yKeys) {
      const values = chartData.data
        .map((d) => d[key])
        .filter((v) => typeof v === 'number');
      if (values.length > 0) {
        ranges[key] = {
          min: Math.min(...values),
          max: Math.max(...values),
          range: Math.max(...values) - Math.min(...values),
        };
      }
    }

    const rangeValues = Object.values(ranges);
    if (rangeValues.length >= 2) {
      const maxRange = Math.max(...rangeValues.map((r) => r.max));
      const minRange = Math.min(...rangeValues.map((r) => r.max));

      // If the largest max is >10x the smallest max, scales are incompatible
      const scaleRatio = maxRange / Math.max(minRange, 1);
      const scalesCompatible = scaleRatio < 10;

      check(
        'scale_separation',
        scalesCompatible,
        scalesCompatible
          ? `Scale ratio ${scaleRatio.toFixed(1)}x — acceptable`
          : `Scale ratio ${scaleRatio.toFixed(1)}x — INCOMPATIBLE SCALES (e.g., mixing yards and TDs). Should use separate charts or normalize.`
      );
    }
  }

  const allPassed = checks.every((c) => c.passed);

  return {
    pass: allPassed,
    score: Math.round((passedChecks / totalChecks) * 100) / 100,
    reason: checks.map((c) => `${c.passed ? 'PASS' : 'FAIL'}: ${c.name} — ${c.detail}`).join('\n'),
  };
};
