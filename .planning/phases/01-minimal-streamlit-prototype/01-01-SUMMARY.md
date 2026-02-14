---
phase: 01-minimal-streamlit-prototype
plan: 01
subsystem: ui
tags: [streamlit, plotly, scatter-plot, caching, deployment]

# Dependency graph
requires:
  - phase: 00-data-preparation
    provides: Pre-computed df_base.parquet and metadata.json with UMAP coordinates, colors, symbols, hover text
provides:
  - Streamlit app entry point with cached data loading and scatter plot
  - Slim deployment requirements (5 packages)
  - Streamlit theme configuration
affects: [02-single-chart-click-handling, 05-full-feature-parity]

# Tech tracking
tech-stack:
  added: [streamlit, plotly, shapely]
  patterns: [st.cache_data for data loading, go.Scatter with per-point arrays]

key-files:
  created:
    - streamlit_app/streamlit_app.py
    - .streamlit/config.toml
  modified:
    - requirements.txt
    - requirements-dev.txt
    - .gitignore

key-decisions:
  - "go.Scatter with per-point color/symbol arrays (not px.scatter) to match original Dash app"
  - "scaleanchor + fixed height=700 for 1:1 aspect ratio without stretching"
  - "use_container_width=False to prevent aspect ratio distortion"
  - "Replaced old Dash/Heroku requirements.txt with 5-package slim deployment file"

patterns-established:
  - "Data loading: @st.cache_data functions in streamlit_app.py load from streamlit_app/data/"
  - "Plot construction: go.Figure + go.Scatter with per-point arrays from DataFrame columns"

# Metrics
duration: 8min
completed: 2026-02-14
---

# Plan 01-01: Streamlit App with Scatter Plot Summary

**Streamlit app loading 563 pre-computed solutions as interactive scatter plot with per-participant colors, per-cluster symbols, and 1:1 aspect ratio**

## Performance

- **Duration:** 8 min
- **Tasks:** 3
- **Files modified:** 5

## Accomplishments
- Streamlit app displays all 563 solutions with correct participant colors and cluster marker symbols
- Hover text shows participant ID, solution number, pre/post, and result from pre-formatted hovertxt column
- Scatter plot enforces 1:1 aspect ratio via scaleanchor with fixed 700px height
- Slim requirements.txt with only 5 packages (streamlit, plotly, pandas, numpy, shapely)
- Pipeline dependencies moved to requirements-dev.txt for local development

## Task Commits

Each task was committed atomically:

1. **Task 1: Create Streamlit app with cached data loading and scatter plot** - `2329ba1b` (feat)
2. **Task 2: Create deployment requirements and Streamlit config** - `7e0a9611` (chore)
3. **Task 3: Verify Streamlit app runs locally** - `1c5a96d4` (fix: 1:1 aspect ratio)

## Files Created/Modified
- `streamlit_app/streamlit_app.py` - Main Streamlit entry point with cached data loading and go.Scatter plot
- `requirements.txt` - Slim 5-package deployment dependencies (replaced old 81-line Dash file)
- `requirements-dev.txt` - Full pipeline dependencies with -r requirements.txt
- `.streamlit/config.toml` - Theme configuration (blue primary) and headless server settings
- `.gitignore` - Cleaned up: removed self-ignore, added venv/ and __pycache__/

## Decisions Made
- Used go.Scatter with per-point arrays instead of px.scatter to match original Dash app (avoids 31-entry legend)
- Set scaleanchor='x' + scaleratio=1 + height=700 + use_container_width=False for proper 1:1 scatter ratio
- Replaced entire requirements.txt (was Dash/Heroku deployment) with slim Streamlit deployment deps

## Deviations from Plan

### Auto-fixed Issues

**1. Aspect ratio distortion with full-width container**
- **Found during:** Task 3 (user visual verification)
- **Issue:** use_container_width=True stretched the scatter plot horizontally, distorting the 1:1 ratio
- **Fix:** Added height=700, scaleanchor='x', scaleratio=1, set use_container_width=False
- **Files modified:** streamlit_app/streamlit_app.py
- **Verification:** User confirmed plot displays with correct proportions
- **Committed in:** 1c5a96d4

---

**Total deviations:** 1 auto-fixed (aspect ratio)
**Impact on plan:** Minor layout fix. No scope creep.

## Issues Encountered
- Streamlit was not installed in DS_312 conda env — installed via pip during verification

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Streamlit app is the foundation for Phase 2 (click handling with streamlit-plotly-events)
- All data loading patterns established via @st.cache_data
- Plot construction pattern (go.Figure + go.Scatter) ready for extension with click callbacks

---
*Phase: 01-minimal-streamlit-prototype*
*Completed: 2026-02-14*
