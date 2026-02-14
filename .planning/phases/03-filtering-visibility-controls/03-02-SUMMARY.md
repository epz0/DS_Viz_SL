---
phase: 03-filtering-visibility-controls
plan: 02
subsystem: visualization
tags: [bugfix, scatter-plot, filtering, gap-closure]
dependency_graph:
  requires: [03-01]
  provides: [scatter-always-visible]
  affects: [click-handling, participant-filter]
tech_stack:
  added: []
  patterns: [full-df-rendering]
key_files:
  created: []
  modified: [streamlit_app/streamlit_app.py]
decisions:
  - Scatter points always show all 563 solutions (participant filter for Phase 5 arrows/areas only)
  - Removed show_points checkbox (points are core feature, always visible)
  - Simplified click handling (no filtered_to_original mapping needed)
metrics:
  duration_min: 2
  completed_date: 2026-02-14
  tasks_completed: 1
  files_modified: 1
  lines_changed: 82
---

# Phase 03 Plan 02: Scatter Plot Always Shows All Solutions

**One-liner:** Fixed scatter plot to display all 563 solutions regardless of participant filter selection - participant filter now only affects future arrows/areas (Phase 5).

## Objective

Fix scatter plot to always show all participants. The participant filter should only affect arrows/areas (future Phase 5 features), not the scatter points.

## Context

**Gap identified during UAT:** User clarified that scatter plot should display all 563 solutions at all times. The participant filter is for controlling arrows and areas visibility, not for filtering scatter points. Previous implementation (03-01) incorrectly filtered scatter trace from `df_filtered` instead of full `df`.

**Root cause:** Lines 99-166 filtered df into df_filtered, then built scatter trace from df_filtered. This made participant filter remove points from scatter plot.

## Tasks Completed

### Task 1: Fix scatter trace to always use full df and simplify participant filter logic

**Status:** Complete
**Commit:** 288c3243
**Duration:** 2 minutes

**Changes made:**

1. **Line 99:** Added comment explaining df_filtered is for Phase 5 arrows/areas only
2. **Lines 102-104:** Deleted empty filter guard (no longer needed)
3. **Lines 106-109:** Deleted clear selection logic (all points always visible)
4. **Lines 77-82:** Deleted show_points checkbox widget (points always visible)
5. **Lines 115-127:** Changed iteration from `df_filtered.iterrows()` to `df.iterrows()`
6. **Line 128:** Renamed `filtered_to_original` to `original_indices` (more accurate)
7. **Lines 131-147:** Changed scatter trace to use full df instead of df_filtered
   - `x=df['x_emb']` (was `df_filtered['x_emb']`)
   - `y=df['y_emb']` (was `df_filtered['y_emb']`)
   - `hovertemplate=df['hovertxt']` (was `df_filtered['hovertxt']`)
   - `color=df['HEX-Win']` (was `df_filtered['HEX-Win']`)
   - `customdata=original_indices` (was `filtered_to_original`)
8. **Lines 149-169:** Removed conditional scatter rendering (if show_points wrapper and else block)
9. **Lines 177-185:** Simplified click handling
   - Removed `if show_points and` condition
   - Changed from `filtered_to_original[clicked_filtered_pos]` to `original_indices[clicked_pos]`
10. **Lines 189-191:** Simplified status caption to show total solution count

**Files modified:**
- `streamlit_app/streamlit_app.py` (-52 lines, +30 lines, net -22 lines)

**What was NOT changed (preserved for Phase 5):**
- Participant multiselect dropdown (lines 65-71)
- df_filtered computation (line 99) - will be used for arrows/areas
- show_arrows and show_areas checkboxes (lines 76-89)
- All existing click handling and detail panel rendering

## Deviations from Plan

None - plan executed exactly as written. This was a straightforward bug fix (Rule 1) to correct incorrect filtering behavior.

## Verification

**Code verification:**
```bash
# Confirm scatter trace uses full df
grep -n "x=df\['x_emb'\]" streamlit_app/streamlit_app.py
# Output: 135:    x=df['x_emb'],  ✓

# Confirm no show_points references
grep -n "show_points" streamlit_app/streamlit_app.py | wc -l
# Output: 0  ✓

# Confirm no empty filter guard
grep -n "df_filtered.empty" streamlit_app/streamlit_app.py | wc -l
# Output: 0  ✓

# Confirm simplified click handling
grep -n "original_indices\[clicked" streamlit_app/streamlit_app.py
# Output: 181:        clicked_original_idx = original_indices[clicked_pos]  ✓

# Confirm iteration over full df
grep -n "for orig_idx, row in df\\.iterrows" streamlit_app/streamlit_app.py
# Output: 115:for orig_idx, row in df.iterrows():  ✓
```

**Expected behavioral verification (manual):**
1. App loads with scatter plot showing all 563 solutions
2. Deselect some participants → scatter plot UNCHANGED (all 563 points still visible)
3. Click any scatter point → detail panel shows correct solution
4. Deselect all participants → scatter plot UNCHANGED, no error/warning
5. Status caption shows "Showing 563 solutions from 31 participants"
6. Points checkbox no longer exists in sidebar

## Outcomes

**Gap closed:** Scatter plot now correctly displays all 563 solutions at all times. Participant filter is a no-op until Phase 5 implements arrows/areas traces.

**Code quality improvements:**
- Simplified codebase (-22 lines)
- Removed unnecessary conditional logic
- Clearer separation of concerns (participant filter for Phase 5 features only)
- More accurate variable names (`original_indices` vs `filtered_to_original`)

**User experience:**
- Scatter plot never becomes empty (always shows all solutions)
- No confusing "no data matches filters" warnings
- Click handling works consistently (all points always clickable)
- Simpler UI (removed show_points checkbox that was redundant)

## Self-Check: PASSED

**Files created:** None (SUMMARY.md created as part of plan completion)

**Files modified:**
- [x] `streamlit_app/streamlit_app.py` exists and contains changes
  ```bash
  [ -f "C:/Py/DS_Viz_SL/streamlit_app/streamlit_app.py" ] && echo "FOUND"
  # Output: FOUND
  ```

**Commits exist:**
- [x] 288c3243 - "fix(03-02): scatter plot now shows all 563 solutions regardless of participant filter"
  ```bash
  git log --oneline --all | grep -q "288c3243" && echo "FOUND"
  # Output: FOUND
  ```

## Next Steps

This plan completes Phase 03 (Filtering and Visibility Controls). The participant filter dropdown remains in the UI but has no visible effect until Phase 5 implements arrows/areas traces that will respect the filter.

**Recommended next phase:** Phase 04 or Phase 05 per ROADMAP.md execution sequence.
