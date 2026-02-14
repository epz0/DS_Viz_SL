# Requirements: DS-Viz Streamlit Migration

**Defined:** 2026-02-14
**Core Value:** Interactive scatter plot with click-to-inspect — clicking any point shows solution details, screenshot, and metrics, with performance chart syncing to selected participant.

## v1 Requirements

Requirements for full feature parity with the existing Dash app, deployed on Streamlit Community Cloud.

### Pre-Computation

- [ ] **PREC-01**: Pre-computation script runs full pipeline (read Excel, distance matrix, UMAP, unmask, metrics, clusters, novelty) and outputs cached data files
- [ ] **PREC-02**: df_base with all computed columns (80+ columns including embeddings, metrics, hover text, core attributes) saved as parquet
- [ ] **PREC-03**: Convex hull vertices per participant saved as pickle
- [ ] **PREC-04**: Metadata (participant IDs list, DS area, cluster symbols, color mappings) saved as JSON
- [ ] **PREC-05**: Data validation confirms all fields required by the Streamlit app are present in pre-computed files

### Scatter Plot

- [ ] **SCAT-01**: Main scatter plot renders all solutions as colored points (by participant) with cluster symbols
- [ ] **SCAT-02**: Full design space convex hull rendered as background trace
- [ ] **SCAT-03**: Per-participant convex hulls rendered as semi-transparent filled polygons
- [ ] **SCAT-04**: Per-participant exploration arrows showing solution sequence
- [ ] **SCAT-05**: Hover text on points shows participant ID, solution number, pre/post, result
- [ ] **SCAT-06**: Clicking a point highlights it (larger size, different symbol, border)

### Performance Chart

- [ ] **PERF-01**: Performance chart shows solution performance (budget efficiency) per participant as line+marker traces
- [ ] **PERF-02**: Clicking scatter point isolates the selected participant's trace in performance chart
- [ ] **PERF-03**: Vertical dashed line marks intervention point (pre/post boundary) for selected participant
- [ ] **PERF-04**: Clicked solution highlighted with larger marker and border in performance chart
- [ ] **PERF-05**: Horizontal reference line at performance = 1

### Cross-Chart Sync

- [ ] **SYNC-01**: Clicking scatter point updates performance chart to show selected participant
- [ ] **SYNC-02**: Clicking performance chart point highlights corresponding point in scatter
- [ ] **SYNC-03**: Clicking either chart updates the detail panel with clicked solution info
- [ ] **SYNC-04**: Clicking either chart updates the screenshot to the clicked solution

### Filters & Toggles

- [ ] **FILT-01**: Participant multi-select dropdown filters scatter to show only selected participants
- [ ] **FILT-02**: Checklist toggles visibility of Points, Arrows, and Areas independently
- [ ] **FILT-03**: Filters and toggles work together (e.g., show only Areas for selected participants)

### Detail Panel

- [ ] **DETL-01**: Participant info displayed (participant ID, group, intervention phase)
- [ ] **DETL-02**: Solution ID displayed
- [ ] **DETL-03**: Result, cost, and max stress displayed
- [ ] **DETL-04**: Total length, number of nodes, number of segments displayed
- [ ] **DETL-05**: Core attributes displayed (solution type, deck, structure, rock support, materials)
- [ ] **DETL-06**: Solution screenshot loaded from external GitHub URL
- [ ] **DETL-07**: Creativity metrics displayed (area explored: total/pre/post)
- [ ] **DETL-08**: Distance metrics displayed (distance traveled: total/pre/post)
- [ ] **DETL-09**: Cluster metrics displayed (clusters visited: total/pre/post)
- [ ] **DETL-10**: Novelty metrics displayed (neighbors, density)
- [ ] **DETL-11**: Performance metric displayed

### Deployment

- [ ] **DEPL-01**: Streamlit app loads pre-computed data with @st.cache_data (target <2s load time)
- [ ] **DEPL-02**: Deployed requirements.txt contains only visualization dependencies (~150-200MB)
- [ ] **DEPL-03**: Separate requirements-dev.txt for full local pipeline
- [ ] **DEPL-04**: App deploys to Streamlit Community Cloud within free tier limits
- [ ] **DEPL-05**: Streamlit config (.streamlit/config.toml) configured for appropriate theme and layout

### Code Organization

- [ ] **ORGN-01**: Streamlit app code in dedicated directory (streamlit_app/) separate from analysis scripts
- [ ] **ORGN-02**: Existing analysis scripts (scripts/) unchanged and functional for local use
- [ ] **ORGN-03**: Pre-computation script in scripts/ directory runs full pipeline and outputs to streamlit_app/data/

## v2 Requirements

Deferred to future release. Tracked but not in current roadmap.

### Enhanced Interactivity

- **EINT-01**: Real-time UMAP re-computation with parameter sliders
- **EINT-02**: Data upload capability for new datasets
- **EINT-03**: Advanced filtering (by group, by pre/post, by result)
- **EINT-04**: Export selected metrics to CSV from the app

### Mobile

- **MOBL-01**: Mobile-optimized responsive layout
- **MOBL-02**: Touch-friendly interaction targets

## Out of Scope

| Feature | Reason |
|---------|--------|
| Porting interactive_tool_quant.py | Only interactive_tool.py is deployed |
| Porting interactive_tool_rt.py | Only interactive_tool.py is deployed |
| Deleting unused scripts | User wants to keep all scripts in repo |
| Rewriting the analysis pipeline | Existing pipeline stays as-is for local use |
| Adding new visualizations | Pure port, no new functionality |
| Database backend | File-based approach sufficient for this dataset size |
| Authentication | Public research tool, no auth needed |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| PREC-01 | Phase 0 | Pending |
| PREC-02 | Phase 0 | Pending |
| PREC-03 | Phase 0 | Pending |
| PREC-04 | Phase 0 | Pending |
| PREC-05 | Phase 0 | Pending |
| SCAT-01 | Phase 1 | Pending |
| SCAT-02 | Phase 5 | Pending |
| SCAT-03 | Phase 5 | Pending |
| SCAT-04 | Phase 5 | Pending |
| SCAT-05 | Phase 1 | Pending |
| SCAT-06 | Phase 2 | Pending |
| PERF-01 | Phase 4 | Pending |
| PERF-02 | Phase 4 | Pending |
| PERF-03 | Phase 4 | Pending |
| PERF-04 | Phase 4 | Pending |
| PERF-05 | Phase 4 | Pending |
| SYNC-01 | Phase 4 | Pending |
| SYNC-02 | Phase 4 | Pending |
| SYNC-03 | Phase 4 | Pending |
| SYNC-04 | Phase 4 | Pending |
| FILT-01 | Phase 3 | Pending |
| FILT-02 | Phase 3 | Pending |
| FILT-03 | Phase 3 | Pending |
| DETL-01 | Phase 2 | Pending |
| DETL-02 | Phase 2 | Pending |
| DETL-03 | Phase 2 | Pending |
| DETL-04 | Phase 2 | Pending |
| DETL-05 | Phase 2 | Pending |
| DETL-06 | Phase 2 | Pending |
| DETL-07 | Phase 5 | Pending |
| DETL-08 | Phase 5 | Pending |
| DETL-09 | Phase 5 | Pending |
| DETL-10 | Phase 5 | Pending |
| DETL-11 | Phase 5 | Pending |
| DEPL-01 | Phase 1 | Pending |
| DEPL-02 | Phase 1 | Pending |
| DEPL-03 | Phase 1 | Pending |
| DEPL-04 | Phase 6 | Pending |
| DEPL-05 | Phase 1 | Pending |
| ORGN-01 | Phase 1 | Pending |
| ORGN-02 | Phase 0 | Pending |
| ORGN-03 | Phase 0 | Pending |

**Coverage:**
- v1 requirements: 40 total
- Mapped to phases: 40
- Unmapped: 0 ✓

---
*Requirements defined: 2026-02-14*
*Last updated: 2026-02-14 after initial definition*
