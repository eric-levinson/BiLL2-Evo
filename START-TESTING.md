# 🧪 START MANUAL TESTING - Action Required

## ⚠️ Action Required Before Testing

The automated testing cannot proceed because this requires **manual browser interaction** and **database editing**. Here's what you need to do:

## Step 1: Configure Environment

The dev server needs valid environment variables. Edit `bill-agent-ui/.env`:

```bash
cd bill-agent-ui
# Edit .env file with your actual credentials:
# - NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
# - NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key
# - ANTHROPIC_API_KEY=your-anthropic-key (or OPENAI_API_KEY)
```

## Step 2: Start Development Server

```bash
cd bill-agent-ui
pnpm dev
```

The server should start on http://localhost:3000

## Step 3: Perform Manual Tests

Open your browser and follow the comprehensive guide in **`MANUAL-TESTING-GUIDE.md`**

### Quick Testing Path (Minimum Required)

If you want to do a quick verification instead of the full test suite:

1. **Open** http://localhost:3000
2. **Create** a new chat session (click "New Chat")
3. **Send** a test message: "Hello, test message"
4. **Get the session ID** from the URL or database
5. **Open Supabase Studio** → SQL Editor
6. **Run this SQL** to inject a test bar chart:

```sql
-- First, find your session
SELECT id, created_at, messages
FROM chat_sessions
ORDER BY created_at DESC
LIMIT 5;

-- Then update the assistant's response (adjust the index if needed)
UPDATE chat_sessions
SET messages = jsonb_set(
  messages,
  '{1,content}',  -- Index of assistant message, may need to adjust
  '"Here are the top 5 wide receivers:\n\n```chart\n{\n  \"type\": \"bar\",\n  \"title\": \"Top 5 WRs by Receiving Yards (2024)\",\n  \"data\": [\n    { \"player\": \"CeeDee Lamb\", \"yards\": 1749 },\n    { \"player\": \"Tyreek Hill\", \"yards\": 1502 },\n    { \"player\": \"Amon-Ra St. Brown\", \"yards\": 1515 },\n    { \"player\": \"Puka Nacua\", \"yards\": 1486 },\n    { \"player\": \"Brandon Aiyuk\", \"yards\": 1342 }\n  ],\n  \"config\": {\n    \"xAxisKey\": \"player\",\n    \"yAxisKey\": \"yards\",\n    \"xAxisLabel\": \"Player\",\n    \"yAxisLabel\": \"Receiving Yards\",\n    \"valueFormat\": \"number\"\n  }\n}\n```"'::jsonb
)
WHERE id = 'YOUR_SESSION_ID';  -- Replace with actual session ID
```

7. **Reload** the chat page in your browser
8. **Verify** the bar chart renders inline (not as a code block)
9. **Check** that it has:
   - 5 colored bars
   - Player names on X-axis
   - Yard values on Y-axis
   - Title at the top
   - Interactive tooltips on hover
10. **Resize** browser window and verify chart is responsive

### Quick Line Chart Test

Run this SQL to add a line chart:

```sql
UPDATE chat_sessions
SET messages = jsonb_set(
  messages,
  '{1,content}',
  '"Weekly performance:\n\n```chart\n{\n  \"type\": \"line\",\n  \"title\": \"CeeDee Lamb Weekly Yards\",\n  \"data\": [\n    { \"week\": 1, \"yards\": 96 },\n    { \"week\": 2, \"yards\": 149 },\n    { \"week\": 3, \"yards\": 100 },\n    { \"week\": 4, \"yards\": 87 },\n    { \"week\": 5, \"yards\": 94 }\n  ],\n  \"config\": {\n    \"xAxisKey\": \"week\",\n    \"yAxisKey\": \"yards\",\n    \"xAxisLabel\": \"Week\",\n    \"yAxisLabel\": \"Yards\"\n  }\n}\n```"'::jsonb
)
WHERE id = 'YOUR_SESSION_ID';
```

Reload and verify line chart displays with connected dots.

### Quick Error Handling Test

Test that invalid JSON falls back gracefully:

```sql
UPDATE chat_sessions
SET messages = jsonb_set(
  messages,
  '{1,content}',
  '"This should show an error:\n\n```chart\n{\n  \"type\": \"invalid\"\n}\n```"'::jsonb
)
WHERE id = 'YOUR_SESSION_ID';
```

Reload and verify an error message displays (not a crash).

## Step 4: Report Results

After testing, create/update a file called `TESTING-RESULTS.md` with your findings:

```markdown
# Manual Testing Results - Subtask 5-1

Date: [DATE]
Tester: [YOUR NAME]

## Tests Performed

- [ ] Bar chart renders correctly
- [ ] Line chart renders correctly
- [ ] Charts are responsive
- [ ] Error handling works
- [ ] No console errors

## Issues Found

[List any issues or note "None"]

## Screenshots

[Optional: attach screenshots of working charts]

## Conclusion

[ ] All tests passed - ready to mark subtask complete
[ ] Issues found - need fixes before completion
```

## Step 5: Mark Subtask Complete

Once testing is successful, run:

```bash
# Update implementation plan
# (This will be done by the automation after you confirm)

# Commit the results
git add TESTING-RESULTS.md
git commit -m "auto-claude: subtask-5-1 - Manual browser testing completed"
```

## Available Documentation

- **MANUAL-TESTING-GUIDE.md** - Comprehensive step-by-step testing (all 14 test cases)
- **test-chart-data.md** - Copy-paste ready chart JSON for all scenarios
- **TESTING-SUMMARY.md** - Overview of what's been implemented
- **CHARTS.md** (in bill-agent-ui/) - Complete chart format specification

## Minimum Acceptance Criteria

For subtask completion, verify at minimum:

✅ Bar chart renders inline in chat message
✅ Line chart renders inline in chat message
✅ Charts are responsive (resize window)
✅ Charts have labels, legends, tooltips
✅ Invalid JSON doesn't crash (shows error or code block)
✅ No console errors in browser DevTools

## Need Help?

If you encounter issues:

1. Check `bill-agent-ui/.env` has valid Supabase credentials
2. Check browser console (F12) for error messages
3. Verify `pnpm dev` shows no startup errors
4. Try `pnpm install` again if missing dependencies
5. Check that Supabase project is accessible

## Why Manual Testing?

This is a manual test because:
- Browser interaction required (visual verification of charts)
- Database editing required (inject test chart data)
- No automated E2E test infrastructure exists yet
- Responsiveness testing requires window resizing
- Visual quality assessment is subjective

Automated testing could be added in a future phase with Playwright or Cypress.
