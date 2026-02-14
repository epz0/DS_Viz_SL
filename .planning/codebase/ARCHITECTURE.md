# Architecture

## Overview

**Pattern:** Sequential data processing pipeline with interactive visualization layer

**Domain:** Design space analysis for creativity research — takes experimental design solutions, computes pairwise distances, reduces to 2D via UMAP, then computes geometric metrics (convex hulls, novelty, clustering) and runs ANCOVA statistics across participant groups.

## Layers

### 1. Data Input Layer
- `scripts/design_space/read_data.py` — Reads Excel spreadsheet into pandas DataFrames (base data, color scheme, labels)
- Input: `.xlsx` file with sheets `ExpData-100R-Expanded` and `ColorScheme`
- Output: `df_base`, `df_colors`, `labels`

### 2. Distance Computation Layer
- `scripts/design_space/dist_matrix.py` — Computes pairwise distance matrices using Jaccard + Gower metrics
- Input: `df_base`, data directory, filename
- Output: Normalized distance matrix (`n_distmatrix`)

### 3. Dimensionality Reduction Layer
- `scripts/design_space/dim_reduction.py` — UMAP embedding of distance matrix to 2D
- Caches embedding as `.pkl`/`.csv` in `export/` directory
- Parameters: `NN` (neighbors), `MD` (min distance), `densm` (density)
- Output: `embedding` (Nx2 matrix), `graph` (igraph object)

### 4. Metrics Computation Layer
- `scripts/design_space/design_space.py` — Convex hull area/perimeter per participant (full/pre/post sessions)
- `scripts/design_space/dspace_metrics.py` — DS coverage, alternative metrics (overlap, RAE)
- `scripts/design_space/dspace_dist_metrics.py` — Distance-based metrics per participant (full/pre/post)
- `scripts/design_space/dspace_metric_novelty.py` — Global/local novelty metrics
- `scripts/design_space/dspace_cluster.py` — Cluster assignment via igraph

### 5. Visualization Layer
- `scripts/design_space/dspace_viz_arrows.py` — Arrow plots showing design space exploration paths
- `scripts/design_space/dspace_viz_density.py` — KDE density heatmaps
- `scripts/design_space/dspace_viz_landscape.py` — Landscape visualizations
- Static plots via matplotlib, saved to `viz/` directory

### 6. Interactive Dashboard Layer
- `scripts/interactive_tool.py` — Main Dash web app (~1175 lines)
- `scripts/interactive_tool_quant.py` — Quantitative-focused variant
- `scripts/interactive_tool_rt.py` — Real-time variant
- Uses Plotly/Dash with callbacks for participant selection, graph interactions
- Served via `Procfile` (Heroku-compatible)

### 7. Statistics Layer
- `scripts/stats/stats_main.py` — ANCOVA wrapper using statsmodels
- `scripts/stats/stats_mt1_fluency.py` — Fluency metric comparisons
- `scripts/stats/stats_mt2_variety.py` — Variety metric comparisons
- `scripts/stats/stats_mt3_mt4_novelty.py` — Novelty metric comparisons
- Output: Excel files in `export/stats/`

### 8. Validation Layer
- `scripts/validation/validation_distmetric.py` — Distance metric weight validation
- `scripts/validation/validation_areametric.py` — Area sensitivity validation
- `scripts/validation/validation_viz.py` — Visual validation of solutions placement

## Data Flow

```
Excel (.xlsx)
    → read_analysis()
    → calc_distmatrix()         → distance matrix
    → create_embedding()        → 2D UMAP embedding + graph
    → unmask_data()             → unmasked participant IDs
    → create_cvxh()             → convex hull metrics (full/pre/post)
    → dist_metrics_fs/pre/post()→ distance metrics
    → get_clusters()            → cluster assignments
    → ancova_stat()             → statistical comparisons → Excel export
    → Dash app                  → interactive web dashboard
```

## Entry Points

| Entry Point | Purpose | Run Context |
|---|---|---|
| `scripts/interactive_tool.py` | Main interactive dashboard | `python -m scripts.interactive_tool` or via Procfile |
| `scripts/interactive_tool_quant.py` | Quantitative dashboard variant | Direct execution |
| `scripts/interactive_tool_rt.py` | Real-time dashboard variant | Direct execution |
| `scripts/interactive_run.py` | Dash app launcher (imports interactive_tool) | Direct execution |
| `scripts/test_run.py` | Full pipeline test/execution | Run from `scripts/` directory |
| `scripts/stats_run.py` | Statistics pipeline | Run from `scripts/` directory |
| `scripts/viz_run.py` | Visualization pipeline | Run from `scripts/` directory |
| `scripts/validation_run.py` | Validation pipeline | Run from `scripts/` directory |

## Key Abstractions

- **Masked/Unmasked data**: Participant and group IDs are masked in the spreadsheet; `unmask_data()` in `utils.py` decodes them using a `MASKING_KEYS` sheet
- **Session segments**: Data split into Full Session (FS), Pre-intervention (PRE/KYY), Post-intervention (POST/ZSB)
- **Participant metrics**: Each participant gets convex hull area, perimeter, distance metrics, novelty scores, cluster assignments
- **Group comparisons**: Three experimental groups (GA/GB/GC mapped to UF/CG/SF) compared via ANCOVA

## Configuration

- No centralized config file — parameters are hardcoded in each run script
- UMAP parameters: `NN`, `MD`, `densm` set per entry point
- Data paths: Hardcoded `Path(r'C:/Py/...')` in run scripts; Dash apps use `Path.cwd()`
- File/sheet names defined as module-level variables in each run script
