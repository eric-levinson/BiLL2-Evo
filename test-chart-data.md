# Chart Testing Data

Use these test JSON blocks to manually test chart rendering in the chat UI.

## Test 1: Simple Bar Chart (Receiving Yards)

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

## Test 2: Grouped Bar Chart (Dual-Threat RBs)

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

## Test 3: Line Chart (Weekly Performance)

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

## Test 4: Multi-Line Chart (Player Comparison)

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

## Test 5: Percentage Bar Chart

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

## Test 6: Invalid JSON (Error Handling Test)

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

## Test 7: Missing Required Fields (Error Handling Test)

```chart
{
  "type": "bar",
  "title": "Missing data array"
}
```

## Test 8: Unsupported Chart Type (Error Handling Test)

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
