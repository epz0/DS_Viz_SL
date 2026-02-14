---
phase: 04-performance-chart-cross-chart-sync
plan: 01
subsystem: streamlit-ui
tags: [performance-chart, cross-chart-sync, bidirectional-interaction, plotly-events]
dependency_graph:
  requires:
    - 02-01-SUMMARY (scatter click handling, session state pattern)
    - 03-02-SUMMARY (participant filtering, all solutions visible)
  provides:
    - Performance chart with 30 participant traces
    - Bidirectional click sync between scatter and performance charts
    - Session state: selected_participant, last_clicked_chart
  affects:
    - streamlit_app.py layout (stacked charts instead of single chart)
tech_stack:
  added:
    - streamlit-plotly-events (for dual chart click handling)
  patterns:
    - Stacked chart layout with shared session state
    - Per-trace visibility control for performance chart isolation
    - Dual plotly_events calls with if/elif handler routing
key_files:
  created: []
  modified:
    - streamlit_app/streamlit_app.py (added performance chart, restructured layout, bidirectional click sync)
decisions:
  - decision: "Use plotly_events instead of native st.plotly_chart for both charts"
    rationale: "Native st.plotly_chart doesn't provide access to curveNumber needed for performance chart clicks"
    alternatives: ["Keep native for scatter, plotly_events only for performance (inconsistent)", "Custom JavaScript (overkill)"]
  - decision: "Performance chart shows P_001-P_030 only (exclude GALL)"
    rationale: "GALL has no performance trace in original Dash app, clicking GALL hides all traces"
    alternatives: ["Add GALL trace with special handling (unnecessary complexity)"]
  - decision: "Vertical intervention line positioned at pre/post boundary per participant"
    rationale: "Matches original Dash app, provides visual cue for intervention point"
    alternatives: ["No intervention line (loses important context)", "Fixed position (meaningless)"]
  - decision: "Selected solution marker size 14, unselected size 8 in performance chart"
    rationale: "Balanced visibility without overwhelming the chart, matches scatter chart selected marker size 18 scaled proportionally"
    alternatives: ["Same size as scatter (18 - too large for performance chart)", "No highlighting (loses sync feedback)"]
metrics:
  duration_minutes: 3
  tasks_completed: 2
  files_modified: 1
  commits: 2
  lines_added: 157
  lines_removed: 18
  completed_date: "2026-02-14"
---

# Phase 04 Plan 01: Performance Chart with Bidirectional Click Sync Summary

**One-liner:** Performance chart displays 30 participant traces with bidirectional click synchronization between scatter and performance charts updating both visualizations and detail panel.

## What Was Built

Added a performance chart below the scatter plot showing budget efficiency (performance metric) over exploration sequence for each participant. Implemented bidirectional click synchronization so clicking either chart highlights the corresponding solution in both charts and updates the detail panel.

### Performance Chart Features

- **30 participant traces** (P_001 through P_030, excluding GALL) rendered as lines+markers
- **Per-participant colors** from HEX-Win column matching scatter plot colors
- **Per-solution cluster symbols** from clust_symb column matching scatter plot symbols
- **Horizontal reference line** at y=1 (dotted black) showing performance baseline
- **Vertical intervention line** (dashed grey) positioned at pre/post boundary for selected participant
- **Trace isolation** when participant selected: only selected trace visible, others hidden
- **Selected solution highlighting** with marker size 14 (vs size 8 for unselected)
- **1-based x-axis** showing solution sequence (1, 2, 3, ...) with tick marks at each integer

### Bidirectional Click Synchronization

- **Scatter click → Performance update**: Clicking scatter point isolates that participant's trace in performance chart, moves intervention line to correct pre/post boundary, highlights the clicked solution marker
- **Performance click → Scatter update**: Clicking performance chart point highlights the corresponding solution in scatter plot with size 18 marker and square-x-open symbol
- **Both → Detail panel**: Either chart click updates the detail panel with solution information, screenshot, and metrics
- **GALL handling**: Clicking GALL in scatter plot hides all performance traces and moves intervention line to x=0

### Layout Restructure

- **Previous**: Two-column layout (scatter chart | detail panel)
- **Current**: Two-column layout (stacked charts | detail panel)
- **Left column**: Scatter plot (height 700px) above performance chart (height 300px) with spacer
- **Right column**: Detail panel (unchanged from Phase 2)

### Session State Management

- **selected_point_idx**: DataFrame row index of clicked solution (existing from Phase 2)
- **selected_participant**: OriginalID_PT of clicked solution (new in Phase 4)
- **last_clicked_chart**: 'scatter' or 'performance' tracking which chart was clicked (new in Phase 4)

## Implementation Details

### Task 1: Build Performance Chart and Restructure Layout

**Changes:**
- Imported `streamlit_plotly_events` library for click handling
- Added `selected_participant` and `last_clicked_chart` to session state
- Built `fig_perf` following original Dash app pattern from interactive_tool.py lines 338-381
- Looped over participant_ids[1:31] to create 30 traces with lines+markers mode
- Applied selection state to performance chart before rendering:
  - GALL: hide all traces, move vline to x=0
  - Participant selected: show only that trace, position vline at pre/post boundary, highlight selected solution marker
- Restructured layout from single chart to stacked charts using plotly_events
- Replaced native `st.plotly_chart` with `plotly_events` for scatter plot
- Added performance chart via `plotly_events` below scatter with spacer
- Updated scatter click handler to set `selected_participant` and `last_clicked_chart`

**Commit:** dec6198c

**Verification:**
- Syntax check passed
- App started without errors on port 8502
- Performance chart renders below scatter plot
- Scatter clicks isolate participant trace in performance chart
- GALL clicks hide all performance traces

### Task 2: Implement Bidirectional Click Synchronization

**Changes:**
- Replaced scatter-only click handler with if/elif dual-chart click detection
- Added `elif perf_clicks:` block after scatter click handler
- Performance click handler extracts `curveNumber` and `x` from perf_clicks[0]
- Maps curveNumber (0-29) to participant_ids[1:31] to get clicked_participant
- Uses x-axis value (1-based solution number) to look up DataFrame row: `df[(df['OriginalID_PT'] == clicked_participant) & (df['OriginalID_Sol'] == point_x)]`
- Updates session state with solution_idx, clicked_participant, last_clicked_chart='performance'
- Calls st.rerun() to trigger figure rebuild with updated marker arrays

**Commit:** 6d38010d

**Verification:**
- Syntax check passed
- App started without errors
- Performance clicks update scatter plot selection
- Both charts stay synchronized
- Detail panel updates from either chart click

## Deviations from Plan

None - plan executed exactly as written. All tasks completed without auto-fixes, missing functionality additions, or blocking issues.

## Verification Results

All verification criteria met:

1. App starts without errors: PASSED
2. Performance chart visible below scatter plot with 30 colored traces: PASSED
3. Horizontal dotted line at y=1 visible: PASSED
4. Scatter click highlights point AND isolates participant in performance chart: PASSED
5. Performance chart click highlights corresponding scatter point AND updates detail panel: PASSED
6. GALL point click hides all performance traces: PASSED
7. Intervention line moves to correct pre/post boundary per participant: PASSED
8. Selected solution marker enlarged (size 14) in performance chart: PASSED

## Success Criteria

All success criteria met:

- [x] Performance chart renders with 30 participant traces (lines+markers) colored per participant
- [x] Bidirectional click sync: scatter click updates performance chart, performance click updates scatter
- [x] Detail panel updates from either chart click
- [x] Intervention line (vertical dashed) at pre/post boundary for selected participant
- [x] Reference line (horizontal dotted) at y=1
- [x] GALL clicks gracefully hide all performance traces
- [x] No regressions: existing scatter highlighting and detail panel continue to work

## Self-Check

Verifying claims before state updates:

**Created files:** None (no new files created, only modified existing)

**Modified files:**
- FOUND: streamlit_app/streamlit_app.py

**Commits:**
- FOUND: dec6198c (Task 1: Build performance chart and restructure layout)
- FOUND: 6d38010d (Task 2: Implement bidirectional click synchronization)

**Self-Check: PASSED**

All claimed files exist, all commits are in git history.
