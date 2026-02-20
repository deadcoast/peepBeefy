# Rich UI Overhaul for peepBeefy

## Context

The current src/main.py UI is bare minimum Rich usage — plain text dumps for diffs, zero sampling feedback (app looks frozen), no section dividers, hardcoded colors everywhere, and flat text blocks for process
details. All changes are display-only in the single file src/main.py.

## Changes (in implementation order)

1. New imports + Theme

- Add Rule, Status, Theme imports
- Create PEEP_THEME with semantic style names (peep.error, peep.success, peep.accent, peep.metric.hot/warn/ok, peep.diff.added/removed, etc.)
- Pass theme to Console()
- Replace ~30 hardcoded color strings with theme tokens (mechanical find-replace, zero visual change)

1. Error/success helpers

- Add _error(msg) and_success(msg) — print messages inside colored bordered Panels instead of bare Text
- Replace 6 call sites (baseline not found, save confirmation, unknown command, no matches)

1. Sampling spinner

- Add _sampled() wrapper around collect_samples() that shows console.status() spinner during the 1+ second sampling delay
- Replace ~11 collect_samples() call sites (skip the 2 inside Live watch mode — they conflict)

1. Diff output tables

- Replace plain f-string loops (+ process_name  path) with proper Rich Tables
- Columns: +/- indicator (colored), Process name (bold), Path (dim)
- Apply to both interactive loop diff AND CLI baseline_diff command
- "No new processes" gets a green rounded Panel instead of bare text

1. Rule dividers

- Add Rule() horizontal dividers before: scan results, diff output, process info, menu
- Move table title to Rule for render_rows() to get full-width section headers

1. Menu polish

- Add icon column to MENU_ITEMS (emoji per command type)
- Upgrade table box style from SIMPLE to SIMPLE_HEAVY
- Use theme colors for headers

1. Process info detail layout

- Replace Text.join() wall in dev_info with a two-column Table(box=None) — Field | Value
- Fixed-width label column, proper alignment

### Files modified

- src/main.py — all changes in this single file

### Verification

- beefy peep all — should show spinner during sampling, then table with Rule header
- beefy peep cpu / beefy peep io / beefy peep mem — same spinner behavior
- beefy baseline save test.json && beefy baseline diff test.json — should show success Panel, then diff Tables
- beefy dev info chrome — should show structured detail grid
- Interactive mode (double-click bat) — menu should have icons, spinner should appear
- Watch mode (beefy peep watch --loops 3) — should NOT have spinner (unchanged)

---

peepBeefy: `FATBOI_PROCESSES_DESTROYER_5000`

---
