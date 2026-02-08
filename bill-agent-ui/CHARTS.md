# CHARTS.md - BiLL-2 Evo Chart Format Specification

## Overview

BiLL-2 Evo supports interactive data visualization through JSON-formatted chart blocks in chat responses. Charts are rendered client-side using Recharts, providing rich visual analytics for fantasy football data.

**Supported Chart Types:**
- **Bar Charts** — Compare categorical data (e.g., player stats, team rankings)
- **Line Charts** — Show trends over time (e.g., weekly performance, seasonal progression)

**Key Features:**
- Responsive design with automatic scaling
- Interactive tooltips with formatted values
- Support for multiple data series
- Customizable colors and labels
- Automatic value formatting (numbers, percentages, decimals)

## Chart Format Specification

### JSON Schema

Charts are embedded in chat responses as JSON code blocks with the language identifier `chart`:

````markdown
```chart
{
  "type": "bar" | "line",
  "title": "Chart Title",
  "data": [...],
  "config": {...}
}
```
````

### Bar Chart Schema

```typescript
interface BarChart {
  type: "bar";
  title: string;                    // Chart title (displayed above chart)
  data: DataPoint[];                // Array of data points
  config: {
    xAxisKey: string;               // Key for X-axis values (e.g., "player", "week")
    yAxisKey: string | string[];    // Key(s) for Y-axis values (single or multiple bars)
    xAxisLabel?: string;            // Optional X-axis label
    yAxisLabel?: string;            // Optional Y-axis label
    colors?: string[];              // Optional hex colors for bars (defaults to theme colors)
    valueFormat?: "number" | "percentage" | "decimal";  // Number formatting
  };
}

interface DataPoint {
  [key: string]: string | number;   // Dynamic keys based on xAxisKey and yAxisKey
}
```

### Line Chart Schema

```typescript
interface LineChart {
  type: "line";
  title: string;                    // Chart title (displayed above chart)
  data: DataPoint[];                // Array of data points (must be sorted by X-axis)
  config: {
    xAxisKey: string;               // Key for X-axis values (e.g., "week", "season")
    yAxisKey: string | string[];    // Key(s) for Y-axis values (single or multiple lines)
    xAxisLabel?: string;            // Optional X-axis label
    yAxisLabel?: string;            // Optional Y-axis label
    colors?: string[];              // Optional hex colors for lines (defaults to theme colors)
    valueFormat?: "number" | "percentage" | "decimal";  // Number formatting
  };
}

interface DataPoint {
  [key: string]: string | number;   // Dynamic keys based on xAxisKey and yAxisKey
}
```

## Examples

### Example 1: Simple Bar Chart (Single Series)

Compare receiving yards for top 5 wide receivers:

````markdown
```chart
{
  "type": "bar",
  "title": "Top 5 WRs by Receiving Yards (2024)",
  "data": [
    { "player": "CeeDee Lamb", "yards": 1749 },
    { "player": "Tyreek Hill", "yards": 1502 },
    { "player": "Amon-Ra St. Brown", "yards": 1515 },
    { "player": "Puka Nacua", "yards": 1486 },
    { "player": "Brandon Aiyuk", "yards": 1342 }
  ],
  "config": {
    "xAxisKey": "player",
    "yAxisKey": "yards",
    "xAxisLabel": "Player",
    "yAxisLabel": "Receiving Yards",
    "valueFormat": "number"
  }
}
```
````

### Example 2: Grouped Bar Chart (Multiple Series)

Compare rushing and receiving yards for dual-threat RBs:

````markdown
```chart
{
  "type": "bar",
  "title": "Dual-Threat RBs: Rush vs Receiving Yards (2024)",
  "data": [
    { "player": "Christian McCaffrey", "rushing": 1459, "receiving": 564 },
    { "player": "Alvin Kamara", "rushing": 1158, "receiving": 466 },
    { "player": "Austin Ekeler", "rushing": 628, "receiving": 436 },
    { "player": "Bijan Robinson", "rushing": 976, "receiving": 487 }
  ],
  "config": {
    "xAxisKey": "player",
    "yAxisKey": ["rushing", "receiving"],
    "xAxisLabel": "Player",
    "yAxisLabel": "Yards",
    "colors": ["#3b82f6", "#10b981"],
    "valueFormat": "number"
  }
}
```
````

### Example 3: Line Chart (Single Series)

Show a player's weekly receiving yards progression:

````markdown
```chart
{
  "type": "line",
  "title": "CeeDee Lamb Weekly Receiving Yards (2024)",
  "data": [
    { "week": 1, "yards": 96 },
    { "week": 2, "yards": 149 },
    { "week": 3, "yards": 100 },
    { "week": 4, "yards": 87 },
    { "week": 5, "yards": 94 },
    { "week": 6, "yards": 67 },
    { "week": 7, "yards": 113 },
    { "week": 8, "yards": 71 }
  ],
  "config": {
    "xAxisKey": "week",
    "yAxisKey": "yards",
    "xAxisLabel": "Week",
    "yAxisLabel": "Receiving Yards",
    "valueFormat": "number"
  }
}
```
````

### Example 4: Multi-Line Chart

Compare weekly fantasy points for multiple players:

````markdown
```chart
{
  "type": "line",
  "title": "Weekly Fantasy Points Comparison (PPR, 2024)",
  "data": [
    { "week": 1, "CMC": 24.5, "Tyreek": 18.3, "Jefferson": 12.1 },
    { "week": 2, "CMC": 31.2, "Tyreek": 22.7, "Jefferson": 15.8 },
    { "week": 3, "CMC": 28.6, "Tyreek": 19.4, "Jefferson": 21.3 },
    { "week": 4, "CMC": 22.1, "Tyreek": 16.2, "Jefferson": 18.9 },
    { "week": 5, "CMC": 27.8, "Tyreek": 24.1, "Jefferson": 14.5 }
  ],
  "config": {
    "xAxisKey": "week",
    "yAxisKey": ["CMC", "Tyreek", "Jefferson"],
    "xAxisLabel": "Week",
    "yAxisLabel": "Fantasy Points (PPR)",
    "colors": ["#ef4444", "#f59e0b", "#8b5cf6"],
    "valueFormat": "decimal"
  }
}
```
````

### Example 5: Percentage Bar Chart

Show target share percentages for WRs on a team:

````markdown
```chart
{
  "type": "bar",
  "title": "Dallas Cowboys WR Target Share (2024)",
  "data": [
    { "player": "CeeDee Lamb", "targetShare": 28.5 },
    { "player": "Brandin Cooks", "targetShare": 15.2 },
    { "player": "Michael Gallup", "targetShare": 12.8 },
    { "player": "Jake Ferguson", "targetShare": 14.1 }
  ],
  "config": {
    "xAxisKey": "player",
    "yAxisKey": "targetShare",
    "xAxisLabel": "Player",
    "yAxisLabel": "Target Share (%)",
    "valueFormat": "percentage"
  }
}
```
````

## Guidelines: When to Use Charts vs Tables

### Use Charts When:

✅ **Comparing values** — Bar charts excel at showing relative magnitudes
- Example: "Compare receiving yards for top 10 WRs"
- Example: "Show rushing TDs by RB"

✅ **Showing trends** — Line charts reveal patterns over time
- Example: "Track weekly fantasy points for Player X"
- Example: "Show seasonal progression of completion percentage"

✅ **Highlighting relationships** — Multi-series charts show correlations
- Example: "Compare rushing vs receiving yards for dual-threat RBs"
- Example: "Show weekly points for multiple players in a matchup"

✅ **Visual impact** — Charts make differences more obvious at a glance
- Example: Dynasty rookie rankings (bar chart shows gaps between tiers)
- Example: Weekly boom/bust analysis (line chart shows volatility)

✅ **Limited data points** — Charts work best with 3-20 data points
- Too few (< 3): Data is better shown inline
- Too many (> 20): Chart becomes cluttered; use table with sorting

### Use Tables When:

❌ **Precise values matter** — Users need exact numbers for analysis
- Example: "Show all stats for Player X" (table with 15+ columns)
- Example: "List league rosters with bye weeks"

❌ **Many columns** — Tables handle 5+ dimensions better than charts
- Example: Player comparison with 10+ stat categories
- Example: Weekly matchup grid with projections, actual, and variance

❌ **Large datasets** — Tables support pagination and sorting
- Example: "Show all RBs with 100+ carries" (50+ rows)
- Example: "List trending players" (scrollable table)

❌ **Exact rankings** — Tables preserve precise ordering
- Example: Dynasty rankings with ADP, value, and tier (table maintains rank #)
- Example: Waiver wire priorities (users need exact rank order)

❌ **Categorical data with no clear order** — Tables organize unordered data
- Example: League settings (key-value pairs)
- Example: Player injury status (categorical)

### Hybrid Approach:

🔄 **Use both** — Provide chart for visualization, table for details
- Example: "Here's a chart comparing the top 5 WRs, and below is the full table with all stats"
- Example: Line chart for weekly trend, table for exact weekly values

## Best Practices

### Data Preparation

1. **Sort data appropriately:**
   - Bar charts: Sort by value (descending) or alphabetically
   - Line charts: MUST be sorted by X-axis (e.g., week 1, 2, 3...)

2. **Limit data points:**
   - Bar charts: 3-15 bars (20 max)
   - Line charts: 5-25 points per series (30 max)
   - Multiple series: 2-5 lines/bar groups

3. **Use meaningful labels:**
   - Player names (not IDs)
   - Clear metric names ("Receiving Yards" not "rec_yds")
   - Include units in yAxisLabel ("Fantasy Points (PPR)")

### Value Formatting

Use `valueFormat` to control number display:

- `"number"` — Integer formatting with commas (e.g., 1,234)
- `"decimal"` — One decimal place (e.g., 24.5)
- `"percentage"` — Percentage with % symbol (e.g., 28.5%)

### Color Selection

Default colors are optimized for readability. Override with `colors` array for:
- Team colors (e.g., Chiefs red: `#E31837`)
- Semantic colors (positive/negative: green/red)
- Distinguishing multiple series (use high-contrast colors)

**Color recommendations:**
- Single series: Use default (theme blue)
- 2 series: `["#3b82f6", "#10b981"]` (blue, green)
- 3 series: `["#ef4444", "#f59e0b", "#8b5cf6"]` (red, amber, purple)
- 4+ series: Use distinct hues with similar saturation

### Titles

Write clear, descriptive titles:
- ✅ "Top 5 WRs by Receiving Yards (2024)"
- ✅ "CeeDee Lamb Weekly Fantasy Points (PPR, Weeks 1-8)"
- ❌ "Player Stats" (too vague)
- ❌ "Receiving" (missing context)

## AI Agent Usage Instructions

When the AI agent should create a chart:

1. **Assess the query intent:**
   - Does the user want to compare, rank, or see trends?
   - Are they asking for visual analysis or precise data?

2. **Check data size:**
   - Is the result set 3-20 items? → Consider chart
   - More than 20? → Use table (or top N + table)
   - Less than 3? → Show inline text

3. **Choose chart type:**
   - Comparing categories → Bar chart
   - Showing time-series → Line chart
   - Multiple metrics → Multi-series chart

4. **Format the response:**
   - Provide brief context text before chart
   - Include chart block with proper JSON schema
   - Optionally add table below for exact values
   - Explain key insights after visualization

**Example agent response structure:**

```
Here are the top 5 wide receivers by receiving yards in 2024:

```chart
{
  "type": "bar",
  ...
}
```

CeeDee Lamb leads all receivers with 1,749 yards, 247 yards ahead of second-place Amon-Ra St. Brown. The top 5 WRs are separated by only 407 yards, showing parity at the elite tier.

[Optional table with full stats]
```

## Technical Implementation Notes

Charts are rendered by the `ChartBlock` component in `src/components/playground/ChartBlock.tsx`:

- Uses Recharts library (`recharts` npm package)
- Renders `BarChart` and `LineChart` components
- Applies responsive container with 400px default height
- Validates JSON schema before rendering
- Falls back to error message if schema is invalid

**Error handling:**
- Invalid JSON → Shows parsing error
- Missing required fields → Shows schema error
- Empty data array → Shows "No data to display"
- Unsupported chart type → Shows "Unsupported chart type"

**Performance considerations:**
- Charts render client-side (no SSR)
- Large datasets (100+ points) may cause lag
- Recommend pagination or aggregation for large data

## Examples by Use Case

### Fantasy Football Analytics

**Player Comparison:**
- Bar chart: Compare stats across players (yards, TDs, targets)
- Multi-bar: Show rush + receiving yards for RBs

**Weekly Trends:**
- Line chart: Track fantasy points week-over-week
- Multi-line: Compare 2-3 players' weekly performance

**League Analysis:**
- Bar chart: Team points scored by week
- Line chart: Season-long standings progression

**Dynasty Valuations:**
- Bar chart: Rookie ADP by position
- Bar chart: Player dynasty values by tier

**Matchup Analysis:**
- Multi-bar: Starters vs bench scoring
- Line chart: Points against by week (opponent strength)

### Sleeper League Data

**Roster Analysis:**
- Bar chart: Points per roster position
- Bar chart: Bench depth by team

**Transaction Trends:**
- Line chart: Waiver claims by week
- Bar chart: Most added/dropped players

**Playoff Race:**
- Line chart: Weekly standings for top 6 teams
- Bar chart: Points for vs points against

## Troubleshooting

**Chart not rendering:**
- Check JSON syntax (missing commas, quotes)
- Verify all required fields present (`type`, `title`, `data`, `config`)
- Ensure `xAxisKey` and `yAxisKey` match data point keys

**Data not showing:**
- Verify data array is not empty
- Check that keys in `data` match `xAxisKey`/`yAxisKey`
- Ensure numeric values are numbers, not strings

**Unexpected appearance:**
- Check `colors` array length matches number of series
- Verify `valueFormat` is valid option
- Ensure data is sorted correctly (especially line charts)

**Performance issues:**
- Reduce data points (< 25 per series)
- Use fewer series (< 5 lines/bars)
- Consider aggregating or sampling large datasets

## Future Enhancements

Potential chart features for future development:

- Scatter plots (correlations, player clustering)
- Stacked bar charts (compositional data)
- Area charts (cumulative trends)
- Combo charts (bar + line)
- Custom tooltips with player headshots
- Export chart as PNG/SVG
- Interactive filters (date range, player selection)
- Drill-down to detailed stats on click

---

For implementation details, see:
- `src/components/playground/ChartBlock.tsx` — Chart rendering component
- `src/components/playground/MessageContent.tsx` — Chart block detection and rendering
- `CLAUDE.md` — Overall project architecture
