const fs = require('fs');
const path = process.argv[2] || 'results/latest.json';
const data = JSON.parse(fs.readFileSync(path, 'utf8'));
const results = data.results;

// Group by provider
const byProvider = {};
for (const r of results.results) {
  const label = r.provider.label || r.provider.id;
  if (byProvider[label] === undefined) byProvider[label] = { pass: 0, fail: 0, total: 0 };
  byProvider[label].total++;
  if (r.success) byProvider[label].pass++;
  else byProvider[label].fail++;
}

console.log('=== RESULTS BY MODEL ===');
for (const [label, stats] of Object.entries(byProvider)) {
  const pct = ((stats.pass / stats.total) * 100).toFixed(1);
  console.log(`  ${label}: ${stats.pass}/${stats.total} passed (${pct}%)`);
}

// Group by category per model
console.log('\n=== RESULTS BY CATEGORY x MODEL ===');
const matrix = {};
const categories = new Set();
const models = new Set();

for (const r of results.results) {
  const label = r.provider.label || r.provider.id;
  models.add(label);

  let cat = 'Other';
  if (r.vars && r.vars.expected_tools) cat = 'Tool Selection';
  else if (r.vars && r.vars.expected_min_steps) cat = 'Step Efficiency';
  else {
    const prompt = (r.vars && r.vars.prompt) || '';
    if (prompt.toLowerCase().includes('chart') || prompt.toLowerCase().includes('bar chart') || prompt.toLowerCase().includes('visualiz')) cat = 'Chart Generation';
    else {
      // Check assertions for icontains
      const hasIcontains = (r.gradingResult && r.gradingResult.componentResults || []).some(c => c.assertion && c.assertion.type === 'icontains');
      if (hasIcontains) cat = 'Instruction Following';
      else cat = 'Response Quality';
    }
  }
  categories.add(cat);

  const key = cat + '|||' + label;
  if (matrix[key] === undefined) matrix[key] = { pass: 0, total: 0 };
  matrix[key].total++;
  if (r.success) matrix[key].pass++;
}

for (const cat of [...categories].sort()) {
  console.log(`\n${cat}:`);
  for (const model of [...models]) {
    const key = cat + '|||' + model;
    const stats = matrix[key] || { pass: 0, total: 0 };
    if (stats.total > 0) {
      const pct = ((stats.pass / stats.total) * 100).toFixed(0);
      console.log(`  ${model}: ${stats.pass}/${stats.total} (${pct}%)`);
    }
  }
}

// Show failed tests
console.log('\n=== FAILED TESTS (sample) ===');
let failCount = 0;
for (const r of results.results) {
  if (r.success) continue;
  if (failCount >= 10) { console.log('  ... and more'); break; }
  const label = r.provider.label || r.provider.id;
  const prompt = ((r.vars && r.vars.prompt) || '').substring(0, 60);
  const reason = (r.gradingResult && r.gradingResult.reason) || 'unknown';
  console.log(`  [${label}] "${prompt}..."`);
  console.log(`    Reason: ${reason.substring(0, 120)}`);
  failCount++;
}
