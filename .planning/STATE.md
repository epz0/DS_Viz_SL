# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-02-14)

**Core value:** Interactive scatter plot with click-to-inspect — clicking any point shows solution details, screenshot, and metrics, with performance chart syncing to selected participant.
**Current focus:** Phase 2 - Single-Chart Click Handling

## Current Position

Phase: 3 of 5 (Filtering and Visibility Controls)
Plan: 2 of 2 in current phase
Status: Phase complete
Last activity: 2026-02-14 — Phase 3 Plan 2 complete (gap closure)

Progress: [████████░░] 60%

## Performance Metrics

**Velocity:**
- Total plans completed: 6
- Average duration: 4 min
- Total execution time: 0.53 hours

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 00 | 2 | 12 min | 6 min |
| 01 | 1 | 8 min | 8 min |
| 02 | 1 | 2 min | 2 min |
| 03 | 2 | 5 min | 2.5 min |

**Recent Trend:**
- Last 5 plans: 8 min, 2 min, 3 min, 2 min
- Trend: Accelerating (gap closure plans very efficient)

*Updated after each plan completion*

| Phase-Plan | Duration | Tasks | Files |
|------------|----------|-------|-------|
| 00-01 | 5 min | 1 | 3 |
| 00-02 | 7 min | 3 | 4 |
| 01-01 | 8 min | 3 | 5 |
| 02-01 | 2 min | 2 | 2 |
| 03-01 | 3 min | 1 | 1 |
| 03-02 | 2 min | 1 | 1 |

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.
Recent decisions affecting current work:

- Streamlit over Vercel: Python-native, minimal rewrite, existing plotly charts carry over
- Pre-compute pipeline: Eliminates ~400MB of heavy deps from deployment
- streamlit-plotly-events for clicks: Only viable Streamlit option for plotly click interactions
- Keep all scripts in repo: Existing analysis/stats/validation scripts still useful for local work
- Modular CLI with individual steps + 'all' command: Flexible execution and debugging (00-01)
- Skip-if-exists logic with --force override: Avoid redundant computation during development (00-01)
- Fail-fast error handling: No silent catches to ensure pipeline integrity (00-01)
- Production UMAP params (NN=115, MD=0.15, densm=2): Not dev values from interactive_tool.py (00-01)
- Auto-validate after every run: Validation step runs automatically for immediate feedback (00-02)
- Plain pandas validation (no pandera): Avoid additional dependencies for data integrity checks (00-02)
- String coercion for parquet: Convert mixed-type object columns to strings for PyArrow compatibility (00-02)
- go.Scatter with per-point arrays (not px.scatter): Matches original Dash app, avoids 31-entry legend (01-01)
- scaleanchor + fixed height for 1:1 ratio: use_container_width=False prevents aspect distortion (01-01)
- Replaced old Dash requirements.txt with 5-package slim file: Heavy deps moved to requirements-dev.txt (01-01)
- st.rerun() after selection change: Ensures figure rebuilds with updated marker arrays (02-01)
- NSegm->nodes, NJoint->segments mapping: Matches original Dash app counterintuitive mapping (02-01)
- Size 18 for selected, size 8 for unselected: Balance between visibility and clickability (02-01)
- Use OriginalID_PT for participant filter: Metadata provides unmasked IDs matching original Dash app (03-01)
- Default all participants selected: Ensures full chart on first load, avoids blank chart confusion (03-01)
- Scatter points always show all 563 solutions: Participant filter for Phase 5 arrows/areas only, not scatter points (03-02)
- Removed show_points checkbox: Points are core feature, always visible (03-02)
- Simplified click handling: Direct original_indices mapping, no filtered_to_original needed (03-02)

### Pending Todos

None yet.

### Blockers/Concerns

None yet.

## Session Continuity

Last session: 2026-02-14 (phase 3 execution)
Stopped at: Completed 03-02-PLAN.md - Scatter plot always shows all solutions
Resume file: None
