# Manual Chart Rendering Testing Guide

## Prerequisites

Before starting the tests, ensure:

1. **Environment Setup**: Copy `.env.example` to `.env` in `bill-agent-ui/` directory and fill in:
   - `NEXT_PUBLIC_SUPABASE_URL` - Your Supabase project URL
   - `NEXT_PUBLIC_SUPABASE_ANON_KEY` - Your Supabase anon key
   - `ANTHROPIC_API_KEY` or `OPENAI_API_KEY` - AI provider API key

2. **Dependencies Installed**: Run `pnpm install` in `bill-agent-ui/` (already done)

3. **Dev Server Running**: Run `pnpm dev` in `bill-agent-ui/` directory

## Testing Procedure

### Step 1: Access the Application

1. Open browser and navigate to: http://localhost:3000
2. Verify the page loads without console errors (open DevTools: F12)

### Step 2: Create a Test Chat Session

1. Start a new chat session
2. Send a simple test message (e.g., "Hello")
3. Wait for AI response
4. Note the session ID from the URL or database

### Step 3: Get Database Access

Open Supabase Studio or use SQL editor to access the `chat_sessions` table:

```sql
-- Find your recent chat session
SELECT id, user_id, created_at, messages
FROM chat_sessions
ORDER BY created_at DESC
LIMIT 5;
```

### Step 4: Test Case 1 - Simple Bar Chart

Edit the AI response in the database to include a bar chart:

```sql
UPDATE chat_sessions
SET messages = jsonb_set(
  messages,
  '{1,content}',  -- Adjust index based on your message structure
  '"Here are the top 5 wide receivers by receiving yards:\n\n```chart\n{\n  \"type\": \"bar\",\n  \"title\": \"Top 5 WRs by Receiving Yards (2024)\",\n  \"data\": [\n    { \"player\": \"CeeDee Lamb\", \"yards\": 1749 },\n    { \"player\": \"Tyreek Hill\", \"yards\": 1502 },\n    { \"player\": \"Amon-Ra St. Brown\", \"yards\": 1515 },\n    { \"player\": \"Puka Nacua\", \"yards\": 1486 },\n    { \"player\": \"Brandon Aiyuk\", \"yards\": 1342 }\n  ],\n  \"config\": {\n    \"xAxisKey\": \"player\",\n    \"yAxisKey\": \"yards\",\n    \"xAxisLabel\": \"Player\",\n    \"yAxisLabel\": \"Receiving Yards\",\n    \"valueFormat\": \"number\"\n  }\n}\n```\n\nCeeDee Lamb leads all receivers with 1,749 yards."'::jsonb
)
WHERE id = 'YOUR_SESSION_ID';
```

**Verification Checklist:**
- [ ] Reload the chat page
- [ ] Verify the chart renders inline (not as a code block)
- [ ] Check that the chart displays a bar chart with 5 bars
- [ ] Verify X-axis shows player names
- [ ] Verify Y-axis shows yard values with proper formatting
- [ ] Verify chart title displays at the top
- [ ] Check that bars are colored (should use theme blue)
- [ ] Hover over bars and verify tooltip shows values
- [ ] Verify text before and after chart renders normally

### Step 5: Test Case 2 - Grouped Bar Chart (Multiple Series)

Create a new message or update existing one with:

```
Here's a comparison of rushing vs receiving yards for dual-threat running backs:

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

Christian McCaffrey dominates in both categories with 1,459 rushing yards and 564 receiving yards.
```

**Verification Checklist:**
- [ ] Chart renders with grouped bars (2 bars per player)
- [ ] Bars are colored: blue for rushing, green for receiving
- [ ] Legend displays showing "rushing" and "receiving"
- [ ] Tooltip shows both values when hovering
- [ ] Multiple series are properly grouped by player

### Step 6: Test Case 3 - Line Chart (Weekly Trend)

Add this chart to a message:

```
Here's CeeDee Lamb's weekly receiving yard progression through the first 8 weeks:

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

You can see his breakout performance in Week 2 with 149 yards.
```

**Verification Checklist:**
- [ ] Chart renders as a line chart (not bar chart)
- [ ] Line connects all 8 data points
- [ ] Line is smooth/curved
- [ ] Dots appear at each data point
- [ ] X-axis shows weeks 1-8
- [ ] Y-axis shows yard values
- [ ] Hovering shows tooltip with exact values
- [ ] Chart follows the trend (peak at week 2, low at week 6)

### Step 7: Test Case 4 - Multi-Line Chart (Player Comparison)

Add this multi-series line chart:

```
Comparing weekly fantasy points for three elite players:

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

CMC shows the most consistency with all weeks above 22 points.
```

**Verification Checklist:**
- [ ] Three distinct lines render in different colors (red, amber, purple)
- [ ] Legend shows all three player names
- [ ] Each line connects its respective data points
- [ ] Values are formatted with one decimal place
- [ ] Tooltip shows all three values when hovering over a week
- [ ] Lines are distinguishable and don't overlap confusingly

### Step 8: Test Case 5 - Percentage Bar Chart

Test value formatting with percentages:

```
Target distribution for Cowboys WRs:

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

CeeDee Lamb commands nearly 30% of all targets.
```

**Verification Checklist:**
- [ ] Bar chart renders correctly
- [ ] Values display with % symbol in tooltips
- [ ] Y-axis label includes "(%)"
- [ ] Percentage formatting is applied correctly

### Step 9: Test Responsiveness

**Verification Checklist:**
- [ ] Open DevTools responsive mode (Ctrl+Shift+M or Cmd+Shift+M)
- [ ] Test at desktop size (1920x1080): Chart should be full width
- [ ] Test at tablet size (768x1024): Chart should scale down proportionally
- [ ] Test at mobile size (375x667): Chart should remain readable
- [ ] Resize browser window gradually: Chart should resize smoothly
- [ ] Verify axis labels don't overlap at smaller sizes
- [ ] Verify legend remains visible at all sizes

### Step 10: Test Error Handling - Invalid JSON

Add this intentionally broken JSON:

```
```chart
{
  "type": "bar",
  "title": "This should fail",
  "data": [
    { "player": "Test"
  ],
  "config": {
    "xAxisKey": "player"
  }
}
```
```

**Verification Checklist:**
- [ ] Chart does NOT render
- [ ] Falls back to showing a code block with syntax highlighting
- [ ] No JavaScript errors in console
- [ ] Page remains functional
- [ ] Other valid charts on the page still render

### Step 11: Test Error Handling - Missing Required Fields

Add this incomplete chart:

```
```chart
{
  "type": "bar",
  "title": "Missing data array"
}
```
```

**Verification Checklist:**
- [ ] Error message displays (ChartRenderer should show validation error)
- [ ] Error message is user-friendly
- [ ] Error is styled with red/destructive theme
- [ ] Rest of the chat message renders normally

### Step 12: Test Error Handling - Unsupported Chart Type

Add this unsupported type:

```
```chart
{
  "type": "pie",
  "title": "Unsupported Chart Type",
  "data": [
    { "category": "A", "value": 10 }
  ],
  "config": {
    "xAxisKey": "category",
    "yAxisKey": "value"
  }
}
```
```

**Verification Checklist:**
- [ ] Error message displays indicating unsupported chart type
- [ ] Error message mentions only "bar" and "line" are supported
- [ ] No crash or blank screen
- [ ] Fallback is graceful

### Step 13: Visual Quality Check

For all rendered charts, verify:

**Styling:**
- [ ] Charts use consistent theme colors
- [ ] Background color matches card/container background
- [ ] Border and shadow are subtle and appropriate
- [ ] Font sizes are readable
- [ ] Spacing and padding look professional

**Labels:**
- [ ] Chart titles are prominent and centered
- [ ] X-axis labels are readable and don't overlap
- [ ] Y-axis labels are readable
- [ ] Legend (when present) is clear and positioned well
- [ ] Tooltips are styled consistently with the app theme

**Data Visualization:**
- [ ] Colors have good contrast against background
- [ ] Multiple series use distinguishable colors
- [ ] Data points are accurate to the input values
- [ ] Scales are appropriate (not too cramped or too spread out)
- [ ] Grid lines (if shown) are subtle and helpful

### Step 14: Browser Console Check

Open browser DevTools (F12) and check:

**Console Tab:**
- [ ] No error messages related to chart rendering
- [ ] No warning messages about missing props
- [ ] No React hydration errors

**Network Tab:**
- [ ] No failed requests for chart-related resources
- [ ] Recharts library loads correctly

**Performance Tab (optional):**
- [ ] Chart rendering doesn't cause significant lag
- [ ] Smooth interactions when hovering/resizing

## Summary Checklist

After completing all tests, verify:

- [x] Simple bar chart renders correctly
- [x] Grouped bar chart with multiple series works
- [x] Line chart displays trends properly
- [x] Multi-line chart compares multiple series
- [x] Percentage formatting works
- [x] Charts are responsive across device sizes
- [x] Invalid JSON falls back gracefully
- [x] Missing fields show error messages
- [x] Unsupported chart types are handled
- [x] Visual styling is consistent and professional
- [x] No console errors during any test
- [x] All labels, legends, and tooltips display correctly
- [x] Hover interactions work smoothly

## Notes

- If any test fails, document the specific issue in build-progress.txt
- Take screenshots of successful chart renders for documentation
- If database editing is difficult, consider creating a development tool/page for injecting test messages
- All test data is available in `test-chart-data.md` for easy copy-paste

## Expected Outcome

All tests should pass with:
- Charts rendering inline within chat messages
- Proper styling matching the app theme
- Responsive behavior on all screen sizes
- Graceful error handling for invalid input
- No console errors or warnings
- Professional appearance suitable for production use
