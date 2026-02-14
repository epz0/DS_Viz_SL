# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-02-14)

**Core value:** Interactive scatter plot with click-to-inspect — clicking any point shows solution details, screenshot, and metrics, with performance chart syncing to selected participant.
**Current focus:** Phase 5 - Full Feature Parity & Deployment

## Current Position

Phase: 5 of 5 (Full Feature Parity & Deployment)
Plan: 1 of 2 in current phase
Status: In progress
Last activity: 2026-02-14 — Phase 5 Plan 1 complete (hull/arrow traces and complete metrics)

Progress: [█████████░] 90%

## Performance Metrics

**Velocity:**
- Total plans completed: 8
- Average duration: 3.75 min
- Total execution time: 0.5 hours

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 00 | 2 | 12 min | 6 min |
| 01 | 1 | 8 min | 8 min |
| 02 | 1 | 2 min | 2 min |
| 03 | 2 | 5 min | 2.5 min |
| 04 | 1 | 3 min | 3 min |
| 05 | 1 | 2 min | 2 min |

**Recent Trend:**
- Last 5 plans: 3 min, 2 min, 3 min, 2 min, 2 min
- Trend: Stable (consistent 2-3 min execution)

*Updated after each plan completion*

| Phase-Plan | Duration | Tasks | Files |
|------------|----------|-------|-------|
| 00-01 | 5 min | 1 | 3 |
| 00-02 | 7 min | 3 | 4 |
| 01-01 | 8 min | 3 | 5 |
| 02-01 | 2 min | 2 | 2 |
| 03-01 | 3 min | 1 | 1 |
| 03-02 | 2 min | 1 | 1 |
| 04-01 | 3 min | 2 | 1 |
| 05-01 | 2 min | 2 | 1 |

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
- Use plotly_events for both charts: Native st.plotly_chart doesn't provide curveNumber needed for performance clicks (04-01)
- Performance chart P_001-P_030 only: GALL has no performance trace, clicking GALL hides all traces (04-01)
- Intervention line at pre/post boundary: Matches original Dash app, provides visual intervention point cue (04-01)
- Selected marker size 14 in performance: Balanced visibility, proportional to scatter size 18 (04-01)
- Separate trace per participant for hulls/arrows: Enables per-participant visibility control via trace.visible property (05-01)
- Full DS hull as separate trace: Always shown when Areas enabled, independent of participant filter (05-01)
- No arrows for GALL: Gallery solutions have no sequence, arrows are P_001-P_030 only (30 traces not 31) (05-01)
- Build all traces unconditionally, control with visibility: Simpler than conditional rendering, matches original Dash pattern (05-01)

### Pending Todos

None yet.

### Blockers/Concerns

None yet.

## Session Continuity

Last session: 2026-02-14 (phase 5 execution)
Stopped at: Completed 05-01-PLAN.md - Full feature parity with hull/arrow traces and metrics
Resume file: None
