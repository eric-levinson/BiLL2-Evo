#!/bin/bash
# Quality check script — lightweight "garbage collection" for code health.
# Output is formatted for AI agent consumption: file path, line number, description, fix.
# Run manually or at the start of a refactoring session.

set -e
ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
ISSUES=0

echo "=== BiLL-2 Quality Check ==="
echo ""

# --- File size check ---
echo "--- File Size (>300 lines) ---"
for f in $(find "$ROOT_DIR/bill-agent-ui/src" -name "*.ts" -o -name "*.tsx" 2>/dev/null); do
  lines=$(wc -l < "$f")
  if [ "$lines" -gt 300 ]; then
    relpath="${f#$ROOT_DIR/}"
    echo "  WARNING: $relpath is $lines lines (limit: 300). Consider splitting into smaller modules."
    ISSUES=$((ISSUES + 1))
  fi
done
for f in $(find "$ROOT_DIR/fantasy-tools-mcp/tools" -name "*.py" 2>/dev/null); do
  lines=$(wc -l < "$f")
  if [ "$lines" -gt 300 ]; then
    relpath="${f#$ROOT_DIR/}"
    echo "  WARNING: $relpath is $lines lines (limit: 300). Consider splitting into smaller modules."
    ISSUES=$((ISSUES + 1))
  fi
done
echo ""

# --- console.log in production TypeScript (excluding route.ts which uses structured logging) ---
echo "--- console.log in non-API TypeScript ---"
CONSOLE_HITS=$(grep -rn "console\.log" "$ROOT_DIR/bill-agent-ui/src/components" "$ROOT_DIR/bill-agent-ui/src/lib" "$ROOT_DIR/bill-agent-ui/src/hooks" 2>/dev/null || true)
if [ -n "$CONSOLE_HITS" ]; then
  echo "$CONSOLE_HITS" | while IFS= read -r line; do
    relpath="${line#$ROOT_DIR/}"
    echo "  INFO: $relpath — Consider removing or converting to structured logging."
  done
  ISSUES=$((ISSUES + $(echo "$CONSOLE_HITS" | wc -l)))
fi
echo ""

# --- @ts-ignore / @ts-expect-error ---
echo "--- TypeScript Suppressions ---"
TS_IGNORE=$(grep -rn "@ts-ignore\|@ts-expect-error" "$ROOT_DIR/bill-agent-ui/src" 2>/dev/null || true)
if [ -n "$TS_IGNORE" ]; then
  echo "$TS_IGNORE" | while IFS= read -r line; do
    relpath="${line#$ROOT_DIR/}"
    echo "  INFO: $relpath — Review if suppression is still needed."
  done
  ISSUES=$((ISSUES + $(echo "$TS_IGNORE" | wc -l)))
fi
echo ""

# --- Python type: ignore ---
echo "--- Python Type Suppressions ---"
PY_IGNORE=$(grep -rn "# type: ignore" "$ROOT_DIR/fantasy-tools-mcp" --include="*.py" 2>/dev/null || true)
if [ -n "$PY_IGNORE" ]; then
  echo "$PY_IGNORE" | while IFS= read -r line; do
    relpath="${line#$ROOT_DIR/}"
    echo "  INFO: $relpath — Review if type suppression is still needed."
  done
  ISSUES=$((ISSUES + $(echo "$PY_IGNORE" | wc -l)))
fi
echo ""

# --- Summary ---
echo "=== Quality Check Complete ==="
if [ "$ISSUES" -gt 0 ]; then
  echo "Found $ISSUES items to review."
else
  echo "No issues found."
fi
