# Project Research Summary

**Project:** Dash-to-Streamlit Migration for DS-Viz Interactive Tool
**Domain:** Interactive Data Visualization Migration
**Researched:** 2026-02-14
**Confidence:** MEDIUM (training data only, needs verification)

## Executive Summary

This migration involves porting a 1175-line Dash application to Streamlit Community Cloud. The Dash app provides interactive design space visualization with 63-trace Plotly charts (convex hulls, arrows, scatter points), bidirectional chart synchronization, and real-time filtering. The recommended approach separates heavy pre-computation (UMAP, distance matrices, metrics) from lightweight deployment by running the full data pipeline locally and deploying only a slim Streamlit app that loads cached parquet files.

The key architectural shift is from Dash's callback-based reactive model to Streamlit's top-to-bottom rerun model. This requires abandoning Dash's partial update pattern (Patch()) and embracing full figure regeneration with aggressive caching. Cross-chart synchronization is achieved through session state management, with `streamlit-plotly-events` enabling click event detection that Streamlit doesn't natively support. The 63-trace complexity creates a critical performance risk that must be addressed through caching strategies and optimized figure generation.

**Primary risks:** (1) Performance degradation from full figure regeneration on every interaction, (2) Complex state synchronization between dual charts causing infinite rerun loops, (3) Pre-computed data missing critical fields discovered only at deployment. Mitigation requires phased implementation starting with data preparation, followed by simple prototypes to validate performance before building full feature parity.

## Key Findings

### Recommended Stack

**Core framework: Streamlit 1.40+** for zero-config deployment to Community Cloud with built-in state management and caching. The deployment stack is intentionally minimal (6 packages, ~150-200MB total) by pre-computing all analysis locally and serializing to parquet/pickle files.

**Core technologies:**
- **Streamlit 1.40+**: Native Python web framework with declarative syntax, automatic reruns on interaction, `st.session_state` for cross-run persistence, `@st.cache_data` for optimized loading
- **Plotly 5.23.0**: Existing visualization library (no version change), rendered via `st.plotly_chart` for display
- **streamlit-plotly-events 0.0.6**: Third-party library enabling click event detection (critical dependency - native `st.plotly_chart` has no click events)
- **Parquet (via pandas/pyarrow)**: Serialization format for pre-computed data (~50-70% smaller than pickle, type-safe, cross-platform)
- **Shapely 2.0.6**: Convex hull polygon operations (already in use, lightweight ~2MB)
- **Pandas/NumPy**: DataFrame and array operations on pre-loaded data

**Local-only dependencies (not deployed):** UMAP, scikit-learn, scipy, numba, llvmlite, matplotlib, seaborn, openpyxl, statsmodels, igraph (~400MB+ of heavy computation libraries)

**Deployment environment:** Streamlit Community Cloud with 1GB RAM limit, ~500MB disk, single-core CPU, 7-day inactivity timeout. No multiprocessing, treat filesystem as read-only post-deployment.

### Expected Features

**Must have (table stakes):**
- Interactive scatter plot with click event handling - users click points to see solution details
- Performance chart showing creativity metrics over solution sequence
- Bidirectional chart synchronization - clicking either chart updates both
- Participant filtering via dropdown (show specific participants)
- Element visibility toggles (Points/Arrows/Areas checkboxes)
- Solution detail panel showing participant info, screenshot, core attributes, metrics

**Should have (competitive):**
- Convex hull rendering for each participant's design space coverage (31 hull traces)
- Arrow traces showing solution sequence progression (30 arrow traces)
- Cluster symbols and creativity metrics visualization
- External image loading from GitHub URLs (solution screenshots)
- Pre-formatted hover text on scatter points

**Defer (v2+):**
- Real-time UMAP computation (pre-compute only)
- Data upload/modification features (static dataset)
- Advanced filtering (focus on participant selection first)
- Mobile-optimized separate view (document minimum screen size)

### Architecture Approach

The architecture splits into two distinct environments: **local analysis pipeline** (heavy computation) and **deployed visualization app** (lightweight rendering). The local pipeline runs UMAP dimensionality reduction, calculates distance matrices and metrics, computes convex hulls, performs clustering, and generates all derived columns. This outputs to `streamlit_app/data/` as parquet (DataFrames), pickle (convex hull vertices), and JSON (metadata). The deployed app uses `@st.cache_data` to load these files once per session, then generates Plotly figures from cached data with session state managing user selections.

**Major components:**
1. **Data Loader** (`utils/data_loader.py`) — Loads pre-computed parquet/pickle/JSON files with caching, validates schema
2. **Chart Components** (`components/main_scatter.py`, `components/performance_chart.py`) — Generate Plotly figures based on filters and selected state, cached where possible
3. **Detail Panel** (`components/detail_panel.py`) — Streamlit UI rendering solution information from selected DataFrame row
4. **State Manager** (session state pattern in `app.py`) — Coordinates `st.session_state.selected_idx` shared between charts, handles click events from `plotly_events`, triggers reruns when needed
5. **Pre-computation Pipeline** (`scripts/precompute_pipeline.py`) — Local-only script running full analysis, outputs cached data files

**Data flow:** Excel → [local pipeline] → Parquet/Pickle → [git commit] → [Streamlit Cloud] → Cached load → Interactive UI

### Critical Pitfalls

1. **Treating Streamlit Like Dash with Callbacks** — Developers fight Streamlit's top-to-bottom execution model trying to recreate explicit callbacks. Results in excessive session state, rerun loops, and performance degradation. **Prevention:** Embrace script reruns, use `st.session_state` sparingly, cache expensive operations, design for idempotent execution.

2. **Not Pre-Computing Everything Needed** — App depends on computation that works locally but fails on Streamlit Cloud (1GB RAM limit, CPU constraints). Results in deployment crashes, timeouts, memory errors. **Prevention:** Pre-compute ALL derived data/metrics/visualizations locally, save as parquet, test data loading time (<2s), validate pre-computed data has all required columns.

3. **Naive Handling of 63-Trace Plotly Figures** — Recreating entire figure on every interaction causes multi-second lag. Streamlit has no `Patch()` equivalent for partial updates. Results in 2-5s lag making app unusable. **Prevention:** Cache base figure generation, smart invalidation only when necessary, consider figure decomposition or lazy rendering, reduce trace complexity where possible.

4. **Sync'd Chart Interactions Without Proper State Management** — Click events trigger state updates triggering reruns triggering more click events = infinite loops. Also causes clicks not registering, stale data, race conditions. **Prevention:** Use session state as single source of truth, check if click data differs from current state before updating, unique keys for all `plotly_events` widgets, structure code so state updates happen before figure generation.

5. **GitHub URL Dependencies Breaking on Deployment** — Solution screenshots from GitHub raw URLs work locally but fail on Streamlit Cloud due to rate limiting, CORS, network differences. **Prevention:** Bundle images with app if possible, implement graceful fallback (placeholder image), test with images disabled to ensure app still functions.

## Implications for Roadmap

Based on research, suggested phase structure:

### Phase 0: Data Preparation & Pre-Computation
**Rationale:** Must establish pre-computed data pipeline before any Streamlit development. All downstream work depends on this data being complete and correct.

**Delivers:**
- `scripts/precompute_pipeline.py` running full UMAP/metrics/clustering pipeline
- `streamlit_app/data/df_base.parquet` with all 80+ computed columns
- `streamlit_app/data/convex_hulls.pkl` with participant vertices
- `streamlit_app/data/metadata.json` with ids, areas, cluster symbols
- Data validation proving all required fields present

**Addresses:** Pre-computing ALL derived data (FEATURES: must-have metrics, creativity scores)

**Avoids:** Pitfall #2 (missing pre-computed data), Pitfall #5 (GitHub URL dependency - validate image URLs)

**Research flag:** Standard ETL pattern, no additional research needed. Existing Dash code lines 29-221 provide full implementation reference.

### Phase 1: Minimal Streamlit Prototype
**Rationale:** Validate core architecture patterns (data loading, caching, session state) with simplest possible implementation before investing in complex features.

**Delivers:**
- `streamlit_app/app.py` with basic two-column layout
- Data loader with `@st.cache_data`
- Static scatter plot display (no clicks yet)
- Session state initialization pattern established

**Addresses:** Verifying data loads correctly, testing deployment to Streamlit Cloud early

**Avoids:** Pitfall #1 (fighting execution model - learn Streamlit patterns first), Pitfall #6 (memory limits - validate early)

**Research flag:** Standard Streamlit patterns, documentation sufficient. Deployment testing needed.

### Phase 2: Single-Chart Click Handling
**Rationale:** Implement core interaction pattern (click → detail update) in isolation before tackling dual-chart synchronization complexity.

**Delivers:**
- `streamlit-plotly-events` integration for main scatter plot
- Session state pattern for `selected_idx`
- Detail panel component rendering solution info
- Click event → state update → detail panel update cycle

**Addresses:** Click event handling (FEATURES: must-have interaction), solution detail display (FEATURES: must-have panel)

**Avoids:** Pitfall #4 (state management loops - test with single chart first)

**Research flag:** `streamlit-plotly-events` library specifics need validation. Check GitHub issues for 63-trace compatibility, click detection behavior on overlapping traces.

### Phase 3: Filtering & Visibility Controls
**Rationale:** Add filtering before dual-chart sync to reduce complexity. Filters don't require cross-component coordination.

**Delivers:**
- Participant multiselect filter component
- Points/Arrows/Areas visibility toggles
- Figure regeneration with filter application
- Optimized caching strategy for filtered figures

**Addresses:** Participant filtering (FEATURES: should-have), element visibility (FEATURES: must-have)

**Avoids:** Pitfall #3 (performance issues - establish caching patterns now)

**Research flag:** Standard Streamlit widgets, no additional research needed.

### Phase 4: Performance Chart & Cross-Chart Sync
**Rationale:** Most complex feature requiring bidirectional state synchronization. Build after single-chart patterns proven.

**Delivers:**
- Performance chart component with `plotly_events`
- Dual-chart state coordination (scatter ↔ performance)
- `st.rerun()` logic for immediate cross-chart updates
- Mapping logic from performance click → solution index

**Addresses:** Performance visualization (FEATURES: must-have), bidirectional sync (FEATURES: must-have)

**Avoids:** Pitfall #4 (infinite rerun loops - careful state management), Pitfall #3 (performance with two 63-trace charts)

**Research flag:** Complex state management. Needs prototyping to validate rerun behavior. Consider `/gsd:research-phase` if issues arise.

### Phase 5: Full Feature Parity & Polish
**Rationale:** Add remaining features after core interactions proven stable.

**Delivers:**
- Convex hull rendering (31 traces)
- Arrow rendering (30 traces)
- Cluster symbols and hover text
- Screenshot loading with error handling
- All creativity metrics in detail panel

**Addresses:** All remaining FEATURES items (hulls, arrows, clusters, screenshots)

**Avoids:** Pitfall #5 (GitHub URLs - graceful fallback), Pitfall #13 (error handling)

**Research flag:** Standard implementation, no additional research needed.

### Phase 6: Optimization & Deployment Validation
**Rationale:** Profile actual performance and optimize bottlenecks before final launch.

**Delivers:**
- Performance profiling of figure generation
- Cache optimization for 63-trace charts
- Cold start time optimization
- Memory usage validation (<800MB)
- Mobile testing and documentation

**Addresses:** Production readiness, user experience quality

**Avoids:** Pitfall #7 (cold starts), Pitfall #12 (mobile experience), Pitfall #14 (Plotly config optimization)

**Research flag:** Performance testing and optimization. Standard profiling tools sufficient.

### Phase Ordering Rationale

- **Phase 0 first:** All subsequent phases depend on pre-computed data. Must validate data completeness early to avoid rework.
- **Prototype before features:** Phase 1 validates deployment and architecture before investing in complex interactions.
- **Single-chart before dual-chart:** Phase 2 establishes state management patterns that Phase 4 builds upon. Reduces debugging complexity.
- **Filters before sync:** Phase 3 has no cross-component dependencies, safer to implement early. Establishes caching patterns for Phase 4.
- **Optimization last:** Phase 6 requires working app to profile. Premature optimization risks wasted effort.

**Dependency chain:** Phase 0 → [1, 2, 3 can partially parallelize] → Phase 4 (depends on 2) → Phase 5 → Phase 6

### Research Flags

**Phases likely needing deeper research:**
- **Phase 2:** `streamlit-plotly-events` library behavior with 63 traces, overlapping traces, click detection reliability
- **Phase 4:** Complex state synchronization patterns, rerun loop prevention, performance with dual charts

**Phases with standard patterns (skip research-phase):**
- **Phase 0:** Standard data pipeline, existing Dash code provides reference
- **Phase 1:** Basic Streamlit app structure, well-documented
- **Phase 3:** Standard Streamlit widgets and filtering
- **Phase 5:** Standard feature implementation
- **Phase 6:** Standard profiling and optimization

**Validation needed before Phase 2:**
1. Benchmark 63-trace figure generation time and JSON payload size
2. Test `streamlit-plotly-events` with multi-trace click handling
3. Verify click detection on overlapping traces (convex hulls vs. scatter points)

**Validation needed before Phase 4:**
1. Prototype dual-chart state synchronization with simple 2-trace figures
2. Test rerun behavior when clicking back-and-forth between charts
3. Verify performance impact of full app rerun on every click

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | MEDIUM | Streamlit and Plotly are well-known, but `streamlit-plotly-events` is third-party with limited documentation. Resource limits for Community Cloud (1GB RAM) are assumed from training data. |
| Features | HIGH | All features map directly from existing Dash app. Feature requirements are well-defined by current implementation. |
| Architecture | MEDIUM | Pre-computation pattern is sound and well-documented. State management patterns are standard but complex with dual charts. 63-trace performance is the key unknown. |
| Pitfalls | LOW | Research conducted without access to current docs, Context7, or web search. Pitfalls are based on general Streamlit patterns and training data, not project-specific validation. |

**Overall confidence:** MEDIUM

### Gaps to Address

**Critical unknowns requiring validation:**
- **streamlit-plotly-events current behavior:** API may have changed since training cutoff (Jan 2025). Need to verify click event return format, trace detection with 63 traces, known issues with overlapping traces.
- **Streamlit Community Cloud 2026 limits:** Assumed 1GB RAM, ~500MB disk, 7-day timeout. Need to verify current specs before deployment planning.
- **Performance with 63 traces:** No benchmark data for figure generation time or rerun latency. Critical for Phase 3/4 planning.
- **Dash Patch() equivalents:** Assumed no workaround exists, but Streamlit may have added features since training cutoff.

**How to handle during planning:**
1. **Phase 0 validation:** Run pre-computation locally, measure data file sizes, verify schema completeness
2. **Phase 1 validation:** Deploy minimal prototype to Streamlit Cloud early, measure actual resource usage and cold start time
3. **Phase 2 validation:** Benchmark figure generation before implementing UI, test `streamlit-plotly-events` with sample 63-trace figure
4. **Phase 4 validation:** Prototype dual-chart sync with simple figures, measure rerun performance before full implementation

**Non-critical gaps (acceptable to defer):**
- Mobile experience optimization (document minimum screen size instead)
- Advanced error handling edge cases (add as bugs arise)
- Custom Streamlit components for advanced features (only if performance issues prove insurmountable)

## Sources

### Primary (HIGH confidence)
- **Existing Dash implementation:** `c:/Py/DS_Viz_SL/scripts/interactive_tool.py` (1175 lines) — Complete feature requirements, data pipeline reference, figure generation logic
- **Current codebase:** Analysis modules in `scripts/design_space/` (12 modules), utilities in `scripts/utils/utils.py` (1934 lines) — Pre-computation pipeline implementation reference

### Secondary (MEDIUM confidence)
- **Streamlit core concepts:** Training data on execution model, caching decorators, session state, deployment patterns
- **Plotly integration:** Training data on `st.plotly_chart`, figure rendering, configuration options
- **Parquet serialization:** Pandas documentation patterns, compression options, type preservation

### Tertiary (LOW confidence)
- **streamlit-plotly-events behavior:** Inferred from training data, needs verification against current library version (0.0.6)
- **Streamlit Community Cloud limits:** Assumed 1GB RAM based on training data, needs verification for 2026
- **Performance characteristics:** No actual benchmarks, estimates based on general patterns

### Recommended verification before roadmap finalization
1. Check Streamlit documentation (2026) for Community Cloud current specs
2. Review `streamlit-plotly-events` GitHub repo for recent issues with multi-trace figures
3. Benchmark figure generation with 63 traces locally before Phase 2 planning
4. Test deployment to Streamlit Cloud in Phase 1 to validate assumptions

---
*Research completed: 2026-02-14*
*Ready for roadmap: yes (with validation steps in Phase 0-1)*
