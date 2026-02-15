# Technical Debt

## Active Items

| Severity | Item | Notes |
|----------|------|-------|
| Medium | MCP tool responses return too much data | Need `columns` parameter and lower default limits |
| Medium | No automated test suite for MCP tools or UI components | Ad-hoc test files exist but not integrated |
| Low | `_archived-services/bill-agno/` still in repo | Can remove once team confirms no longer needed for reference |
| Low | `bill-agent-ui/package-lock.json` coexists with `pnpm-lock.yaml` | Should remove package-lock.json |
| Low | No CI/CD pipeline at monorepo level | bill-agent-ui has standalone validate workflow |
| Low | No Docker containerization | Not a priority for current team size |
| Low | Fantasy knowledge module annual review | `billSystemPrompt.ts` `<fantasy_knowledge>` section (age curves, scoring adjustments, scarcity tiers) needs review each offseason. Version tracked by `FANTASY_KNOWLEDGE_VERSION` constant. Next review: 2026 offseason. |
