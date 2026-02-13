#!/bin/bash
set -e

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "=== Validating bill-agent-ui ==="
cd "$ROOT_DIR/bill-agent-ui" && pnpm run validate

echo ""
echo "=== Validating fantasy-tools-mcp ==="
cd "$ROOT_DIR/fantasy-tools-mcp" && ruff check . && ruff format --check .

echo ""
echo "=== All validations passed ==="
