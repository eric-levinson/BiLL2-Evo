# BiLL2 Service Level Objectives (SLOs)

Measured via Arize Phoenix traces. All targets assume normal operating conditions (MCP server healthy, Anthropic API available).

## Response Latency

| Query Type | Target | Measurement |
|---|---|---|
| Simple queries (single tool call or no tools) | p95 < 3s | Phoenix span duration on root LLM span |
| Multi-tool queries (2+ tool calls) | p95 < 8s | Phoenix trace duration (root to last child) |

## Reliability

| Metric | Target | Measurement |
|---|---|---|
| Tool call success rate | > 99% | Phoenix child span `status = OK` / total tool spans |
| Chat API availability | > 99.5% | HTTP 2xx responses / total requests |

## Cost Efficiency

| Metric | Target | Measurement |
|---|---|---|
| Cost per conversation turn | < $0.15 | Phoenix token counts x model pricing |
| Prompt cache hit rate | > 80% | Anthropic `cache_read_input_tokens` / total input tokens |

## How to Measure

1. **Phoenix UI**: Open `http://<phoenix-host>:6006` and filter by `feature` attribute
2. **Structured logs**: Parse JSON stdout lines for `total_duration_ms` and `input_tokens`
3. **Alerting**: Set Phoenix monitors on p95 latency and tool error rate thresholds

## Review Cadence

- **Weekly**: Check p95 latency and tool success rate trends in Phoenix
- **Monthly**: Review cost per conversation against budget targets
- **Quarterly**: Re-evaluate SLO targets based on usage patterns and model pricing changes
