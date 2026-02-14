# Roadmap: DS-Viz Streamlit Migration

## Overview

This roadmap transforms a 1175-line Dash application into a Streamlit Community Cloud deployment through pre-computation of heavy analysis (UMAP, metrics, clustering) and a lightweight visualization layer. The journey progresses from data preparation through incremental feature building, starting with static displays, adding click interactions, then filters, dual-chart synchronization, and finally full feature parity with convex hulls, arrows, and complete metrics.

## Phases

**Phase Numbering:**
- Integer phases (0, 1, 2, 3, 4, 5): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [x] **Phase 0: Data Preparation & Pre-Computation** - Establish pre-computed data pipeline
- [x] **Phase 1: Minimal Streamlit Prototype** - Basic app structure and deployment validation
- [x] **Phase 2: Single-Chart Click Handling** - Interactive scatter plot with detail panel
- [x] **Phase 3: Filtering & Visibility Controls** - Participant selection and element toggles
- [x] **Phase 4: Performance Chart & Cross-Chart Sync** - Dual-chart bidirectional interaction
- [ ] **Phase 5: Full Feature Parity & Deployment** - Complete visualization with all metrics

## Phase Details

### Phase 0: Data Preparation & Pre-Computation
**Goal**: All heavy computation runs locally and outputs cached data files that the Streamlit app loads
**Depends on**: Nothing (first phase)
**Requirements**: PREC-01, PREC-02, PREC-03, PREC-04, PREC-05, ORGN-02, ORGN-03
**Success Criteria** (what must be TRUE):
  1. Pre-computation script runs full pipeline (Excel read, distance matrix, UMAP, unmask, metrics, clusters, novelty) without errors
  2. All cached data files exist in streamlit_app/data/ (parquet, pickle, JSON)
  3. Validation confirms all 80+ columns required by visualization are present in pre-computed files
  4. Existing analysis scripts in scripts/ directory remain functional for local use
**Plans**: 2 plans

Plans:
- [x] 00-01-PLAN.md -- Build precompute.py pipeline script with all computation steps
- [x] 00-02-PLAN.md -- Validation, requirements-dev.txt, and end-to-end pipeline run

### Phase 1: Minimal Streamlit Prototype
**Goal**: Basic Streamlit app deploys to Community Cloud and loads pre-computed data efficiently
**Depends on**: Phase 0
**Requirements**: SCAT-01, SCAT-05, DEPL-01, DEPL-02, DEPL-03, DEPL-05, ORGN-01
**Success Criteria** (what must be TRUE):
  1. Streamlit app displays static scatter plot with all solutions colored by participant
  2. Hover text shows participant ID, solution number, pre/post, result on scatter points
  3. Data loads from cached files in under 2 seconds using st.cache_data
  4. App deploys successfully to Streamlit Community Cloud within free tier limits
  5. Deployed dependencies are slim (only streamlit, plotly, pandas, numpy, shapely) ~150-200MB total
**Plans**: 1 plan

Plans:
- [x] 01-01-PLAN.md -- Streamlit app with scatter plot, slim requirements, and deployment config

### Phase 2: Single-Chart Click Handling
**Goal**: Clicking any scatter point shows that solution's complete details and screenshot
**Depends on**: Phase 1
**Requirements**: SCAT-06, DETL-01, DETL-02, DETL-03, DETL-04, DETL-05, DETL-06
**Success Criteria** (what must be TRUE):
  1. Clicking a scatter point highlights it with larger size and different visual treatment
  2. Detail panel updates to show participant info (ID, group, intervention phase)
  3. Detail panel shows solution metrics (ID, result, cost, stress, length, nodes, segments)
  4. Detail panel shows core attributes (solution type, deck, structure, rock support, materials)
  5. Solution screenshot loads from GitHub URL with graceful fallback if image fails
**Plans**: 1 plan

Plans:
- [x] 02-01-PLAN.md -- Click handling with point highlighting and detail panel

### Phase 3: Filtering & Visibility Controls
**Goal**: Scatter plot always shows all solutions; participant filter prepared for Phase 5 arrows/areas
**Depends on**: Phase 2
**Requirements**: FILT-01, FILT-02, FILT-03
**Success Criteria** (what must be TRUE):
  1. Scatter plot displays all 563 solutions regardless of participant filter selection
  2. Participant filter dropdown exists but has no effect until Phase 5 (arrows/areas)
  3. Clicking any scatter point works correctly and shows proper solution details
**Plans**: 2 plans

Plans:
- [x] 03-01-PLAN.md -- Sidebar controls with participant filter and visibility toggles
- [x] 03-02-PLAN.md -- Fix scatter trace to always use full df (gap closure from UAT)

### Phase 4: Performance Chart & Cross-Chart Sync
**Goal**: Performance chart and scatter plot synchronize bidirectionally when user clicks either chart
**Depends on**: Phase 2
**Requirements**: PERF-01, PERF-02, PERF-03, PERF-04, PERF-05, SYNC-01, SYNC-02, SYNC-03, SYNC-04
**Success Criteria** (what must be TRUE):
  1. Performance chart displays solution performance (budget efficiency) per participant as line+marker traces
  2. Clicking scatter point isolates selected participant's trace in performance chart and highlights clicked solution
  3. Vertical dashed line marks intervention point (pre/post boundary) for selected participant
  4. Clicking performance chart point highlights corresponding solution in scatter plot
  5. Both charts and detail panel stay synchronized regardless of which chart is clicked
**Plans**: 1 plan

Plans:
- [x] 04-01-PLAN.md -- Performance chart with bidirectional click sync to scatter plot

### Phase 5: Full Feature Parity & Deployment
**Goal**: Complete visualization matches all Dash app features and runs stably on Streamlit Cloud
**Depends on**: Phase 4
**Requirements**: SCAT-02, SCAT-03, SCAT-04, DETL-07, DETL-08, DETL-09, DETL-10, DETL-11, DEPL-04
**Success Criteria** (what must be TRUE):
  1. Full design space convex hull renders as background trace on scatter plot
  2. Per-participant convex hulls render as semi-transparent filled polygons (31 hull traces)
  3. Per-participant exploration arrows show solution sequence (30 arrow traces)
  4. All creativity metrics display in detail panel (area, distance, clusters: total/pre/post)
  5. Novelty metrics (neighbors, density) and performance metric display in detail panel
  6. App runs stably on Streamlit Community Cloud within resource limits (< 800MB memory usage)
**Plans**: 2 plans

Plans:
- [ ] 05-01-PLAN.md -- Add convex hulls, exploration arrows, visibility controls, and all metrics to detail panel
- [ ] 05-02-PLAN.md -- Deploy to Streamlit Community Cloud and verify stability

## Progress

**Execution Order:**
Phases execute in numeric order: 0 -> 1 -> 2 -> 3 -> 4 -> 5

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 0. Data Preparation | 2/2 | ✓ Complete | 2026-02-14 |
| 1. Minimal Prototype | 1/1 | ✓ Complete | 2026-02-14 |
| 2. Click Handling | 1/1 | ✓ Complete | 2026-02-14 |
| 3. Filters & Toggles | 2/2 | ✓ Complete | 2026-02-14 |
| 4. Chart Sync | 1/1 | ✓ Complete | 2026-02-14 |
| 5. Full Feature Parity | 0/2 | Not started | - |
