# DS-Viz Streamlit Migration

## What This Is

An interactive design space visualization tool for creativity research. It displays a 2D UMAP embedding of bridge design solutions, with convex hulls, exploration arrows, and per-solution detail panels. Users click on points to see solution attributes, screenshots, creativity metrics, and performance data. Currently deployed as a Dash app on Heroku — being migrated to Streamlit Community Cloud.

## Core Value

The interactive scatter plot with click-to-inspect must work: clicking any point shows that solution's details, screenshot, and metrics, with the performance chart syncing to the selected participant.

## Requirements

### Validated

<!-- Shipped and confirmed valuable — inferred from existing codebase. -->

- ✓ Data pipeline reads Excel, computes distance matrix, generates UMAP embedding — existing
- ✓ Main scatter plot shows all solutions colored by participant with cluster symbols — existing
- ✓ Convex hulls drawn per participant on scatter plot — existing
- ✓ Exploration arrows show design sequence per participant — existing
- ✓ Checklist toggles visibility of Points/Arrows/Areas — existing
- ✓ Participant dropdown filters to specific participants — existing
- ✓ Clicking a point shows solution details (participant, group, intervention, result, cost, stress) — existing
- ✓ Clicking a point shows solution screenshot from GitHub — existing
- ✓ Clicking a point shows core attributes (deck, structure, rock support, materials) — existing
- ✓ Clicking a point shows creativity metrics (area, distance, clusters, novelty) — existing
- ✓ Performance graph shows per-participant performance, syncs with scatter clicks — existing
- ✓ Performance graph highlights selected solution and intervention point — existing

### Active

<!-- Current scope. Building toward these. -->

- [ ] Port Dash app to Streamlit with equivalent interactive functionality
- [ ] Pre-compute heavy pipeline (UMAP, metrics, distances) as cached data files
- [ ] Deploy on Streamlit Community Cloud within free tier limits
- [ ] Separate deployed app code from local-only analysis/stats/validation scripts
- [ ] Slim dependencies to only what the deployed visualization needs

### Out of Scope

<!-- Explicit boundaries. -->

- Deleting unused scripts — keep all existing code in repo, just don't deploy
- Rewriting the data pipeline — existing pipeline stays as-is for local use
- Adding new features — pure port, no new functionality
- Changing the analysis approach or UMAP parameters — keep existing methodology

## Context

- The Dash app (`scripts/interactive_tool.py`, ~1175 lines) is the only deployed artifact
- Two other variants (`_quant.py`, `_rt.py`) and all run scripts are local-only tools
- Heroku complained about 500MB+ slug size, driven by heavy deps (numba, llvmlite, scipy, scikit-learn, UMAP)
- Solution screenshots are hosted externally on GitHub (no local image storage needed)
- `scripts/utils/utils.py` (82KB) is the largest file — contains shared utilities including `unmask_data()`, `solutions_summary()`, `cv_hull_vertices()`
- The app pre-processes everything at module level (not in callbacks), so pre-computation is natural
- Data is masked for participant anonymity; `MASKING_KEYS` sheet handles unmasking

## Constraints

- **Hosting**: Streamlit Community Cloud free tier — 1GB resource limit, apps sleep after inactivity
- **Size**: Must stay well under free tier limits — pre-compute heavy pipeline, deploy only visualization layer
- **Code changes**: Minimal — don't restructure the analysis pipeline or change the overall approach
- **Dependencies (deployed)**: Only streamlit, plotly, pandas, numpy, shapely (for convex hull rendering), streamlit-plotly-events
- **Dependencies (local)**: Keep full pipeline available for re-running analysis locally
- **Click interactions**: Use `streamlit-plotly-events` for click detection (acceptable behavioral difference from Dash)

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Streamlit over Vercel | Python-native, minimal rewrite, existing plotly charts carry over | — Pending |
| Pre-compute pipeline | Eliminates ~400MB of heavy deps (numba, llvmlite, scipy, scikit-learn, UMAP) from deployment | — Pending |
| streamlit-plotly-events for clicks | Only viable Streamlit option for plotly click interactions | — Pending |
| Keep all scripts in repo | Existing analysis/stats/validation scripts still useful for local work | — Pending |

---
*Last updated: 2026-02-14 after initialization*
