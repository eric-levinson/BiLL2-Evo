# CHARTS.md - BiLL-2 Evo Chart Format Specification

## Overview

BiLL-2 Evo supports interactive data visualization through JSON-formatted chart blocks in chat responses. Charts are rendered client-side using Recharts, providing rich visual analytics for fantasy football data.

**Supported Chart Types:**
- **Bar Charts** — Compare categorical data (e.g., player stats, team rankings)
- **Line Charts** — Show trends over time (e.g., weekly performance, seasonal progression)

**Key Features:**
- Responsive design with automatic scaling
- Interactive tooltips
- Support for multiple data series
- Customizable colors and labels

## Chart Format Specification

### JSON Schema

Charts are embedded in chat responses as JSON code blocks with the language identifier `chart`:

````markdown
```chart
{
  "type": "bar" | "line",
  "data": [...],
  "config": {
    "title": "Chart Title",
    "xKey": "...",
    "yKeys": ["..."]
  }
}
```
````

### Required Fields

| Field | Type | Description |
|-------|------|-------------|
| `type` | `"bar"` or `"line"` | Chart type |
| `data` | `Array<object>` | Array of data point objects |

### Config Fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `xKey` | `string` | `"x"` | Key in each data object for x-axis labels |
| `yKeys` | `string[]` | `["y"]` | Array of keys for y-axis values. Multiple = multi-series |
| `title` | `string` | — | Chart title displayed above the chart |
| `xAxisLabel` | `string` | — | Label for x-axis |
| `yAxisLabel` | `string` | — | Label for y-axis |
| `colors` | `string[]` | theme defaults | Hex color codes for each series |
| `height` | `number` | `400` | Chart height in pixels |
| `showLegend` | `boolean` | `true` | Show/hide legend |
| `showGrid` | `boolean` | `true` | Show/hide grid lines |
| `stacked` | `boolean` | `false` | Stack bars (bar chart only) |
| `showDots` | `boolean` | `true` | Show data point dots (line chart only) |
| `curved` | `boolean` | `true` | Use smooth curves vs straight lines (line chart only) |

## Examples

### Example 1: Simple Bar Chart

````markdown
```chart
{"type":"bar","data":[{"player":"CeeDee Lamb","yards":1749},{"player":"Tyreek Hill","yards":1502},{"player":"Amon-Ra St. Brown","yards":1515},{"player":"Puka Nacua","yards":1486},{"player":"Brandon Aiyuk","yards":1342}],"config":{"xKey":"player","yKeys":["yards"],"title":"Top 5 WRs by Receiving Yards (2024)","xAxisLabel":"Player","yAxisLabel":"Receiving Yards"}}
```
````

### Example 2: Grouped Bar Chart (Multiple Series)

````markdown
```chart
{"type":"bar","data":[{"player":"Christian McCaffrey","rushing":1459,"receiving":564},{"player":"Alvin Kamara","rushing":1158,"receiving":466},{"player":"Austin Ekeler","rushing":628,"receiving":436},{"player":"Bijan Robinson","rushing":976,"receiving":487}],"config":{"xKey":"player","yKeys":["rushing","receiving"],"title":"Dual-Threat RBs: Rush vs Receiving Yards","xAxisLabel":"Player","yAxisLabel":"Yards","colors":["#3b82f6","#10b981"]}}
```
````

### Example 3: Line Chart (Single Series)

````markdown
```chart
{"type":"line","data":[{"week":1,"yards":96},{"week":2,"yards":149},{"week":3,"yards":100},{"week":4,"yards":87},{"week":5,"yards":94},{"week":6,"yards":67},{"week":7,"yards":113},{"week":8,"yards":71}],"config":{"xKey":"week","yKeys":["yards"],"title":"CeeDee Lamb Weekly Receiving Yards (2024)","xAxisLabel":"Week","yAxisLabel":"Receiving Yards","showDots":true,"curved":true}}
```
````

### Example 4: Multi-Line Chart

````markdown
```chart
{"type":"line","data":[{"week":1,"CMC":24.5,"Tyreek":18.3,"Jefferson":12.1},{"week":2,"CMC":31.2,"Tyreek":22.7,"Jefferson":15.8},{"week":3,"CMC":28.6,"Tyreek":19.4,"Jefferson":21.3},{"week":4,"CMC":22.1,"Tyreek":16.2,"Jefferson":18.9},{"week":5,"CMC":27.8,"Tyreek":24.1,"Jefferson":14.5}],"config":{"xKey":"week","yKeys":["CMC","Tyreek","Jefferson"],"title":"Weekly Fantasy Points Comparison (PPR, 2024)","xAxisLabel":"Week","yAxisLabel":"Fantasy Points (PPR)","colors":["#ef4444","#f59e0b","#8b5cf6"]}}
```
````

## Guidelines: When to Use Charts vs Tables

### Use Charts When:
- **Comparing values** — Bar charts show relative magnitudes (e.g., top 10 WRs by yards)
- **Showing trends** — Line charts reveal patterns over time (e.g., weekly fantasy points)
- **Highlighting relationships** — Multi-series charts show correlations (e.g., rush vs receiving)
- **3-20 data points** — Charts work best in this range

### Use Tables When:
- **Precise values matter** — Users need exact numbers
- **Many columns** — 5+ stat categories per item
- **Large datasets** — 20+ rows
- **Exact rankings** — Users need precise rank order

### Hybrid Approach:
- Provide chart for visualization, table below for exact values

## Technical Implementation

Charts are rendered by the `ChartRenderer` component in `src/components/ui/charts/ChartRenderer.tsx`:

- Integration: `CodeBlock` in `src/components/ui/typography/MarkdownRenderer/styles.tsx` detects `language === 'chart'` and delegates to `ChartRenderer`
- Uses Recharts library (`recharts` npm package)
- Renders `BarChart` or `LineChart` based on `type` field
- Validates JSON schema before rendering
- Shows error card with message if schema is invalid

---

For implementation details, see:
- `src/components/ui/charts/` — Chart component directory (types, BarChart, LineChart, ChartRenderer)
- `src/components/ui/typography/MarkdownRenderer/styles.tsx` — Chart detection in CodeBlock
- `CLAUDE.md` — Overall project architecture
