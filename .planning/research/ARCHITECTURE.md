# Architecture Research: Dash-to-Streamlit Migration

## Executive Summary

This document outlines the architecture for migrating a 1175-line Dash application to Streamlit Community Cloud. The strategy separates heavy pre-computation (UMAP, distance matrices, convex hulls, metrics) from the lightweight deployed visualization app. The current Dash app loads Excel, runs the full pipeline at startup, then renders interactive charts. The target architecture pre-computes all data locally, saves it as parquet/pickle, and deploys only a slim Streamlit app that loads cached data and renders interactive plotly charts.

---

## Proposed Directory Structure

```
DS_Viz_SL/
├── .streamlit/
│   └── config.toml                    # Streamlit app config (theme, server settings)
│
├── streamlit_app/                     # DEPLOYED CODE ONLY
│   ├── app.py                         # Main Streamlit app entry point
│   ├── components/
│   │   ├── __init__.py
│   │   ├── main_scatter.py            # Main DS scatter plot component
│   │   ├── performance_chart.py       # Performance graph component
│   │   ├── detail_panel.py            # Solution detail panel component
│   │   └── filters.py                 # Checklist and dropdown components
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── data_loader.py             # Load pre-computed data from parquet/pickle
│   │   └── viz_helpers.py             # Convex hull rendering, hex_rgba conversion
│   └── data/                          # PRE-COMPUTED DATA (checked into repo)
│       ├── df_base.parquet            # Main dataframe with all computed columns
│       ├── df_colors.parquet          # Participant color scheme
│       ├── convex_hulls.pkl           # Dict of {participant: vertices array}
│       ├── metadata.json              # ids list, DS_area, cluster symbols
│       └── MASKING_KEYS.xlsx          # (if needed for deployed app)
│
├── scripts/                           # LOCAL-ONLY ANALYSIS CODE (not deployed)
│   ├── design_space/                  # Core analysis modules (unchanged)
│   │   ├── read_data.py
│   │   ├── dist_matrix.py
│   │   ├── dim_reduction.py
│   │   ├── dspace_metrics.py
│   │   ├── dspace_metric_novelty.py
│   │   ├── dspace_viz_density.py
│   │   ├── dspace_cluster.py
│   │   └── ...
│   ├── utils/                         # Shared utilities (82KB utils.py)
│   │   ├── utils.py
│   │   └── dataset.py
│   ├── precompute_pipeline.py         # NEW: Runs full pipeline, saves to streamlit_app/data/
│   ├── interactive_tool.py            # Original Dash app (keep for reference)
│   ├── interactive_tool_quant.py      # Dash variant (local only)
│   ├── interactive_tool_rt.py         # Dash variant (local only)
│   ├── interactive_run.py             # Local run script
│   ├── stats_run.py                   # Statistical analysis script
│   ├── validation_run.py              # Validation script
│   └── ...
│
├── data/                              # SOURCE DATA (not deployed)
│   ├── MASKED_DATA_analysis_v2.xlsx   # Source Excel file
│   ├── MASKING_KEYS.xlsx              # Participant masking keys
│   └── json/                          # Per-participant JSON folders
│       ├── P_001/
│       ├── P_002/
│       └── ...
│
├── requirements.txt                   # DEPLOYED dependencies (slim)
├── requirements-dev.txt               # LOCAL dependencies (full pipeline)
├── Procfile                           # Heroku config (legacy, keep for reference)
├── .gitignore                         # Exclude venv, __pycache__, data/json/
└── README.md                          # Updated with migration notes
```

**Key Principles:**

1. **Clear separation**: `streamlit_app/` contains ONLY code and data that will be deployed to Streamlit Community Cloud. `scripts/` and `data/` contain local-only analysis code.

2. **Pre-computed data in repo**: The `streamlit_app/data/` directory contains pre-computed parquet/pickle files checked into git. This is acceptable for research projects with static datasets (not massive scale).

3. **Minimal deployed dependencies**: The deployed app only needs streamlit, plotly, pandas, numpy, shapely, streamlit-plotly-events. All heavy computation libraries stay in `requirements-dev.txt`.

4. **No need to ignore scripts/**: Streamlit Community Cloud deploys from the repo root but only runs `streamlit_app/app.py`. The presence of `scripts/` directory does not affect deployment or resource usage.

---

## Pre-Computation Pipeline

### What to Pre-Compute

The current Dash app runs the following pipeline at module level (before serving requests):

1. **Load Excel** → `df_base`, `df_colors`, `labels`
2. **Distance matrix** → `n_distmatrix` (from Gower distance on raw features)
3. **UMAP embedding** → `embedding` (2D coordinates), `graph` (UMAP neighbor graph)
4. **Unmask data** → Replace masked IDs with real participant IDs
5. **Derived columns** → `x_emb`, `y_emb`, `HEX-Win`, core attributes (`ca_sol`, `ca_deck`, etc.)
6. **Solution summary** → Merge `df_sol` (segment count, length, joints)
7. **Distance metrics** → Per-participant FS/PRE/POST distance summaries
8. **Convex hulls** → Per-participant vertices, areas, DS coverage metrics
9. **Novelty metrics** → Density-based novelty, neighbor-based novelty
10. **Clustering** → UMAP graph clusters, cluster symbols, cluster counts
11. **Hover text** → Pre-formatted strings for plotly hover

All of this can be pre-computed and saved as cached data files.

### What to Save

**Main dataframe (parquet):**
```python
# df_base with ALL computed columns:
# - Raw columns from Excel
# - x_emb, y_emb (UMAP coordinates)
# - HEX-Win (participant color)
# - Core attributes (ca_sol, ca_deck, ca_str, ca_rck, ca_mtr, ca_perf, performance, fullid_orig)
# - Solution summary (TLength, NSegm, NJoint)
# - Distance metrics (dist_to_avg_FS, dist_to_avg_PRE, dist_to_avg_PST, dist_change_FS, etc.)
# - Area metrics (Area-Perc-PRE, Area-Perc-POST, Area-Perc-FS)
# - Novelty metrics (novelty_density, novelty_nn)
# - Cluster info (cluster_id, clust_symb, n_clusters, n_clusters_pre, n_clusters_post)
# - hovertxt (pre-formatted hover text)
```

**Convex hull vertices (pickle):**
```python
# Dictionary mapping participant ID to convex hull vertices
{
    'GALL': array([[x1, y1], [x2, y2], ...]),
    'P_001': array([[x1, y1], [x2, y2], ...]),
    'P_002': array([[x1, y1], [x2, y2], ...]),
    ...
}
# Also include full design space hull as 'FULL_DS'
```

**Metadata (JSON):**
```python
{
    "ids": ["GALL", "P_001", "P_002", ...],  # Sorted unique participant IDs
    "DS_area": 123.45,                        # Total design space area
    "cluster_symbols": {                      # Cluster ID → plotly symbol mapping
        1: "circle",
        2: "diamond",
        ...
    }
}
```

**Color scheme (parquet):**
```python
# df_colors with columns: P, HEX-Win
# Lightweight, but needed for potential future use
```

### Pre-Computation Script Structure

**`scripts/precompute_pipeline.py`:**

```python
"""
Pre-computation script for Streamlit deployment.

Runs the full analysis pipeline (UMAP, metrics, convex hulls, clustering)
and saves pre-computed data to streamlit_app/data/ for lightweight deployment.

Usage:
    python -m scripts.precompute_pipeline

Output:
    - streamlit_app/data/df_base.parquet
    - streamlit_app/data/df_colors.parquet
    - streamlit_app/data/convex_hulls.pkl
    - streamlit_app/data/metadata.json
"""

from pathlib import Path
import pandas as pd
import numpy as np
import pickle
import json

# Import existing pipeline modules
from scripts.design_space.read_data import read_analysis
from scripts.design_space.dist_matrix import calc_distmatrix
from scripts.design_space.dim_reduction import create_embedding
from scripts.utils.utils import unmask_data, solutions_summary, cv_hull_vertices
# ... (all other imports from current interactive_tool.py)

def main():
    # [Lines 29-197 from interactive_tool.py: full pipeline]
    # Load Excel, compute UMAP, metrics, clusters, etc.
    # Result: df_base with all columns, df_colors, convex hull data

    # Save outputs
    output_dir = Path('streamlit_app/data')
    output_dir.mkdir(parents=True, exist_ok=True)

    # Save main dataframe
    df_base.to_parquet(output_dir / 'df_base.parquet', index=False)

    # Save color scheme
    df_colors[['P', 'HEX-Win']].to_parquet(output_dir / 'df_colors.parquet', index=False)

    # Compute and save convex hulls
    convex_hulls = {}
    for pt in ids:
        x_vals = df_base[df_base['OriginalID_PT'] == pt]['x_emb'].values
        y_vals = df_base[df_base['OriginalID_PT'] == pt]['y_emb'].values
        cvh_vtx = np.array(shapely.geometry.MultiPoint(
            [xy for xy in zip(x_vals, y_vals)]).convex_hull.exterior.coords)
        convex_hulls[pt] = cvh_vtx

    # Full DS convex hull
    fullds_xvt, fullds_yvt, DS_area = cv_hull_vertices(
        x=df_base['x_emb'], y=df_base['y_emb'])
    convex_hulls['FULL_DS'] = np.column_stack([fullds_xvt, fullds_yvt])

    with open(output_dir / 'convex_hulls.pkl', 'wb') as f:
        pickle.dump(convex_hulls, f)

    # Save metadata
    metadata = {
        'ids': ids,
        'DS_area': DS_area,
        'cluster_symbols': dict(zip(range(1, 17), symb_ls))
    }
    with open(output_dir / 'metadata.json', 'w') as f:
        json.dump(metadata, f, indent=2)

    print(f"Pre-computation complete. Saved to {output_dir}/")

if __name__ == '__main__':
    main()
```

**When to re-run:**

- After updating source data (`MASKED_DATA_analysis_v2.xlsx`)
- After changing UMAP parameters or analysis methodology
- After adding/modifying metric calculations
- Should be manual (not automated) to ensure data stability for deployed app

---

## Streamlit App Structure

### Entry Point: `streamlit_app/app.py`

```python
"""
DS-Viz Interactive Tool — Streamlit Edition

Displays pre-computed design space visualization with interactive scatter plot,
convex hulls, performance chart, and solution detail panels.
"""

import streamlit as st
import plotly.graph_objects as go
from streamlit_plotly_events import plotly_events

from components.main_scatter import create_main_scatter
from components.performance_chart import create_performance_chart
from components.detail_panel import render_detail_panel
from components.filters import render_filters
from utils.data_loader import load_all_data

# --- Page config ---
st.set_page_config(
    page_title="DS-Viz Interactive Tool | GAP Dataset",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- Load data (cached) ---
@st.cache_data
def get_data():
    return load_all_data()

df_base, df_colors, convex_hulls, metadata = get_data()
ids = metadata['ids']

# --- Initialize session state ---
if 'selected_idx' not in st.session_state:
    st.session_state.selected_idx = None
if 'show_elements' not in st.session_state:
    st.session_state.show_elements = ['Points', 'Arrows', 'Areas']
if 'selected_participants' not in st.session_state:
    st.session_state.selected_participants = []

# --- Layout ---
st.title("DS-Viz Interactive Tool | GAP Dataset")
st.caption("[more info](https://doi.org/10.1017/pds.2024.106) | [github](https://github.com/epz0/DS_Viz) | [email](mailto:ep650@cam.ac.uk)")

col1, col2 = st.columns([1, 1])

with col1:
    # Filters
    show_elements, selected_participants = render_filters(ids)

    # Main scatter plot
    fig_scatter = create_main_scatter(
        df_base, convex_hulls, metadata,
        show_elements, selected_participants
    )

    # Plotly events for click detection
    selected_points = plotly_events(
        fig_scatter,
        click_event=True,
        hover_event=False,
        select_event=False,
        override_height=650,
        override_width=725
    )

    # Update session state on click
    if selected_points:
        st.session_state.selected_idx = selected_points[0]['pointIndex']

with col2:
    # Detail panel (shows selected solution info)
    if st.session_state.selected_idx is not None:
        render_detail_panel(df_base, st.session_state.selected_idx)
    else:
        st.info("Click a point on the scatter plot to see solution details.")

    # Performance chart
    fig_performance = create_performance_chart(
        df_base, ids, st.session_state.selected_idx
    )

    # Performance chart clicks
    perf_points = plotly_events(
        fig_performance,
        click_event=True,
        hover_event=False,
        select_event=False,
        override_height=350,
        override_width=725
    )

    # Update selected solution from performance chart click
    if perf_points:
        curve_num = perf_points[0]['curveNumber']
        x_val = perf_points[0]['x']
        pt_id = ids[curve_num + 1]
        matched_idx = df_base[
            (df_base['OriginalID_PT'] == pt_id) &
            (df_base['OriginalID_Sol'] == x_val)
        ].index[0]
        st.session_state.selected_idx = matched_idx
        st.rerun()
```

**Key architectural decisions:**

1. **Session state for cross-chart sync**: `st.session_state.selected_idx` stores the currently selected solution index. Both charts update based on this shared state.

2. **streamlit-plotly-events for clicks**: This library enables plotly click events in Streamlit. Returns `pointIndex` for scatter plot clicks, `curveNumber` + `x` for performance chart clicks.

3. **st.rerun() for reactive updates**: When performance chart is clicked, we update session state and call `st.rerun()` to refresh the UI with the new selection.

4. **Component-based architecture**: Each major UI element is a separate module/function for maintainability.

5. **Cached data loading**: `@st.cache_data` ensures pre-computed data is loaded only once, not on every interaction.

### Component Structure

**`components/main_scatter.py`:**
- `create_main_scatter(df_base, convex_hulls, metadata, show_elements, selected_participants) -> go.Figure`
- Builds plotly figure with convex hulls, arrows, scatter points
- Applies visibility filters based on `show_elements` and `selected_participants`
- Highlights selected point if `st.session_state.selected_idx` is set

**`components/performance_chart.py`:**
- `create_performance_chart(df_base, ids, selected_idx) -> go.Figure`
- Line chart per participant showing performance over solution sequence
- Highlights selected solution with marker size/line width
- Returns plotly figure

**`components/detail_panel.py`:**
- `render_detail_panel(df_base, idx)`
- Streamlit UI showing solution details for row `idx`
- Participant, Group, Intervention, Solution ID
- Result, Cost, Max Stress
- Core attributes (deck, structure, rock support, materials)
- Creativity metrics (area, distance, clusters, novelty)
- Solution screenshot from GitHub URL

**`components/filters.py`:**
- `render_filters(ids) -> (show_elements, selected_participants)`
- Streamlit multiselect for show elements (Points/Arrows/Areas)
- Streamlit multiselect for participant filtering
- Returns current selections

**`utils/data_loader.py`:**
- `load_all_data() -> (df_base, df_colors, convex_hulls, metadata)`
- Loads parquet, pickle, JSON from `streamlit_app/data/`
- Returns data structures ready for visualization

**`utils/viz_helpers.py`:**
- `hex_rgba(hex_color, alpha) -> str`: Convert hex to rgba string for plotly
- Other small helpers from original Dash app

---

## Session State Architecture for Click-Synced Charts

### Challenge

In Dash, callbacks trigger on `clickData` inputs and can use `ctx.triggered_id` to determine which chart was clicked. In Streamlit, `plotly_events` returns click data, but we need to manually manage state to sync two charts.

### Solution: Shared Session State

**State variables:**
```python
st.session_state.selected_idx       # Currently selected solution (df_base row index)
st.session_state.show_elements      # List of visible elements: ['Points', 'Arrows', 'Areas']
st.session_state.selected_participants  # List of selected participant IDs for filtering
```

**Click flow:**

1. **Main scatter click:**
   - `plotly_events(fig_scatter)` → `selected_points[0]['pointIndex']`
   - Update `st.session_state.selected_idx = pointIndex`
   - Streamlit auto-reruns, detail panel and performance chart update

2. **Performance chart click:**
   - `plotly_events(fig_performance)` → `perf_points[0]['curveNumber']`, `perf_points[0]['x']`
   - Map `curveNumber` → participant ID: `ids[curveNumber + 1]`
   - Map `(participant, solution)` → `df_base` index
   - Update `st.session_state.selected_idx = matched_idx`
   - Call `st.rerun()` to refresh scatter plot with new selection

3. **Filter changes:**
   - Update `st.session_state.show_elements` or `st.session_state.selected_participants`
   - Streamlit auto-reruns, scatter plot applies new visibility filters

**Highlight rendering:**

Both chart components check `st.session_state.selected_idx` and apply visual highlights:
- Scatter plot: Increase marker size, add border to selected point
- Performance chart: Increase marker size, thicken line for selected solution's participant

### Behavioral Differences from Dash

**Acceptable:**
- Streamlit requires explicit `st.rerun()` for performance → scatter sync (Dash auto-updates via callback chain)
- `plotly_events` click detection is slightly different from Dash `clickData` (but functionally equivalent)
- Page reloads on filter changes (Dash uses `Patch()` for incremental updates; Streamlit fully rerenders)

**Mitigations:**
- Use `st.cache_data` aggressively to avoid re-computation
- Pre-compute all figures (no expensive operations in render path)
- Streamlit's reactivity model handles this well for datasets of this size (~100s of solutions)

---

## Deployment Configuration

### Streamlit Community Cloud Requirements

**Repository structure:**
- Streamlit Community Cloud expects `streamlit_app.py` OR `app.py` at repo root, OR a `streamlit_app/` directory with `app.py` inside.
- We use `streamlit_app/app.py` for clear separation.

**Configuration files:**

**`.streamlit/config.toml`:**
```toml
[theme]
primaryColor = "#4A90E2"
backgroundColor = "#FFFFFF"
secondaryBackgroundColor = "#F5F5F5"
textColor = "#333333"
font = "sans serif"

[server]
headless = true
enableCORS = false
enableXsrfProtection = true
maxUploadSize = 5

[browser]
gatherUsageStats = false
```

**`requirements.txt`** (deployed dependencies):
```txt
streamlit==1.41.0
plotly==5.23.0
pandas==2.2.3
numpy==2.0.2
shapely==2.0.6
streamlit-plotly-events==0.0.6
pyarrow==19.0.0  # for parquet support
```

**`requirements-dev.txt`** (local-only, full pipeline):
```txt
# Include everything from requirements.txt, plus:
scipy==1.14.1
scikit-learn==1.5.2
umap-learn==0.5.7
numba==0.60.0
llvmlite==0.43.0
matplotlib==3.9.2
openpyxl==3.1.5
gower==0.1.2
igraph==0.11.8
pynndescent==0.5.13
# ... (all other deps from current requirements.txt)
```

**`packages.txt`** (system packages, if needed):
```txt
# Typically not needed for this app, but available for apt packages
# Example:
# libspatialindex-dev
```

**`.gitignore`:**
```txt
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
env/
ENV/

# Data (exclude source data, include pre-computed)
data/json/
!streamlit_app/data/

# IDE
.vscode/
.idea/
*.swp

# OS
.DS_Store
Thumbs.db
```

**`README.md`** (updated):
```markdown
# DS-Viz: Design Space Visualization Tool

Interactive visualization of bridge design solutions from creativity research study.

## Deployed App

Visit: [https://ds-viz.streamlit.app](https://ds-viz.streamlit.app) (example URL)

## Local Development

### Run Pre-Computation (if data changed)

```bash
pip install -r requirements-dev.txt
python -m scripts.precompute_pipeline
```

### Run Streamlit App Locally

```bash
pip install -r requirements.txt
streamlit run streamlit_app/app.py
```

### Original Analysis Scripts

See `scripts/` directory for data pipeline, statistical analysis, and validation tools.

## Deployment

Deployed via Streamlit Community Cloud. Pre-computed data is checked into the repo at `streamlit_app/data/`.
```

### Deployment Checklist

Before deploying to Streamlit Community Cloud:

1. ✓ Run `python -m scripts.precompute_pipeline` to generate latest cached data
2. ✓ Verify `streamlit_app/data/` contains:
   - `df_base.parquet`
   - `df_colors.parquet`
   - `convex_hulls.pkl`
   - `metadata.json`
3. ✓ Test locally: `streamlit run streamlit_app/app.py`
4. ✓ Verify all interactions work (scatter click, performance click, filters)
5. ✓ Check file sizes (parquet should be <10MB, pickle <5MB)
6. ✓ Commit pre-computed data to git
7. ✓ Push to GitHub
8. ✓ Deploy via Streamlit Community Cloud dashboard (connect to repo, specify `streamlit_app/app.py`)

---

## Data Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│ LOCAL ANALYSIS ENVIRONMENT                                           │
│                                                                       │
│  data/MASKED_DATA_analysis_v2.xlsx                                   │
│         │                                                             │
│         ▼                                                             │
│  scripts/precompute_pipeline.py                                      │
│    ├─ Load Excel (read_data)                                         │
│    ├─ Compute distance matrix (Gower distance)                       │
│    ├─ Generate UMAP embedding (dim_reduction)                        │
│    ├─ Unmask participant IDs                                         │
│    ├─ Calculate all metrics (distance, area, novelty, clusters)      │
│    ├─ Compute convex hulls                                           │
│    └─ Derive all columns (ca_*, performance, hovertxt, etc.)         │
│         │                                                             │
│         ▼                                                             │
│  streamlit_app/data/                                                 │
│    ├─ df_base.parquet      [all computed columns]                    │
│    ├─ df_colors.parquet    [participant color scheme]                │
│    ├─ convex_hulls.pkl     [{participant: vertices}]                 │
│    └─ metadata.json        [ids, DS_area, cluster_symbols]           │
│                                                                       │
│  [Commit to git, push to GitHub]                                     │
└─────────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│ STREAMLIT COMMUNITY CLOUD                                            │
│                                                                       │
│  streamlit_app/app.py                                                │
│         │                                                             │
│         ▼                                                             │
│  utils/data_loader.py                                                │
│    ├─ Load df_base.parquet                                           │
│    ├─ Load df_colors.parquet                                         │
│    ├─ Load convex_hulls.pkl                                          │
│    └─ Load metadata.json                                             │
│         │                                                             │
│         ▼                                                             │
│  [Cached in st.session_state via @st.cache_data]                     │
│         │                                                             │
│         ▼                                                             │
│  components/main_scatter.py       → Plotly figure (scatter + hulls)  │
│  components/performance_chart.py  → Plotly figure (line chart)       │
│  components/detail_panel.py       → Streamlit UI (text + image)      │
│  components/filters.py            → Streamlit UI (multiselect)       │
│         │                                                             │
│         ▼                                                             │
│  [User interactions via streamlit-plotly-events]                     │
│    ├─ Click scatter → update st.session_state.selected_idx           │
│    ├─ Click performance → map to idx, update state, st.rerun()       │
│    └─ Change filters → update state, auto-rerun                      │
│         │                                                             │
│         ▼                                                             │
│  [Streamlit reactivity rerenders UI with updated state]              │
└─────────────────────────────────────────────────────────────────────┘
```

**Key points:**

1. **One-way data flow**: Pre-computation runs locally, outputs checked into git, deployed app reads cached data.

2. **No computation in deployed app**: All metrics, UMAP, distances, convex hulls pre-computed. Streamlit app only loads parquet/pickle and renders.

3. **Cached loading**: `@st.cache_data` ensures data is loaded once per session, not on every interaction.

4. **Interactive state management**: Session state tracks selected solution, filters. Plotly events detect clicks, update state, trigger rerenders.

---

## Build Order

### Phase 1: Pre-Computation Infrastructure

1. ✓ Create `scripts/precompute_pipeline.py`
   - Copy pipeline logic from `interactive_tool.py` lines 29-221
   - Add parquet/pickle/JSON save logic
   - Test output: verify data files are created correctly

2. ✓ Create `streamlit_app/data/` directory structure
   - Run pre-computation script
   - Inspect output files (size, schema, contents)
   - Verify convex hulls look reasonable

### Phase 2: Data Loading Layer

3. ✓ Create `streamlit_app/utils/data_loader.py`
   - `load_all_data()` function to read parquet/pickle/JSON
   - Test: load data and print summary statistics
   - Verify schema matches expected columns

4. ✓ Create `streamlit_app/utils/viz_helpers.py`
   - Port `hex_rgba()` from Dash app
   - Any other small helper functions

### Phase 3: Chart Components (Independent of Streamlit)

5. ✓ Create `streamlit_app/components/main_scatter.py`
   - Port figure creation logic from `interactive_tool.py` lines 226-333
   - Function signature: `create_main_scatter(df_base, convex_hulls, metadata, show_elements, selected_participants, selected_idx=None) -> go.Figure`
   - Test standalone: render figure in Jupyter/script

6. ✓ Create `streamlit_app/components/performance_chart.py`
   - Port figure creation logic from `interactive_tool.py` lines 336-382
   - Function signature: `create_performance_chart(df_base, ids, selected_idx=None) -> go.Figure`
   - Test standalone: render figure

### Phase 4: Streamlit UI Components

7. ✓ Create `streamlit_app/components/filters.py`
   - Streamlit multiselect for show elements (Points/Arrows/Areas)
   - Streamlit multiselect for participant filtering
   - Return current selections

8. ✓ Create `streamlit_app/components/detail_panel.py`
   - Port detail panel logic from `interactive_tool.py` lines 438-800
   - Use Streamlit layout components (st.columns, st.metric, st.image)
   - Test with sample row from `df_base`

### Phase 5: Main App Integration

9. ✓ Create `streamlit_app/app.py`
   - Page config, load data (cached)
   - Initialize session state
   - Layout: two columns (scatter + filters on left, detail panel + performance on right)
   - Wire up `plotly_events` for click detection
   - Implement state update logic

10. ✓ Test interactivity locally
    - Run: `streamlit run streamlit_app/app.py`
    - Test scatter click → detail panel updates
    - Test performance click → scatter highlight updates
    - Test filters → visibility updates
    - Test cross-chart sync (click scatter, then performance, verify state)

### Phase 6: Deployment Configuration

11. ✓ Create `.streamlit/config.toml`
    - Set theme, server settings

12. ✓ Create `requirements.txt` (slim)
    - Only deployed dependencies

13. ✓ Update `.gitignore`
    - Exclude `data/json/`, include `streamlit_app/data/`

14. ✓ Update `README.md`
    - Document new architecture
    - Add deployment instructions

### Phase 7: Deploy and Validate

15. ✓ Deploy to Streamlit Community Cloud
    - Connect GitHub repo
    - Specify `streamlit_app/app.py` as entry point
    - Monitor build logs for errors

16. ✓ Validate deployed app
    - Test all interactions (scatter, performance, filters)
    - Check screenshot loading from GitHub
    - Verify performance (should load <5s, interactions <1s)
    - Test on mobile (responsive layout)

17. ✓ Monitor resource usage
    - Check Streamlit Cloud dashboard for memory usage
    - Should be well under 1GB with pre-computed data

### Phase 8: Refinement (Optional)

18. [ ] Polish UI
    - Adjust colors, spacing, fonts
    - Add loading spinners for initial data load
    - Improve mobile layout if needed

19. [ ] Add analytics (optional)
    - Streamlit Cloud provides basic analytics
    - Can add custom tracking if needed

20. [ ] Document local-only scripts
    - Add comments to `scripts/` explaining what each does
    - Update `requirements-dev.txt` with full dependency list

---

## Critical Design Decisions Explained

### Why Parquet Over CSV?

- **Smaller file size**: ~50% reduction with compression
- **Type preservation**: No need to re-infer dtypes
- **Faster loading**: Binary format optimized for pandas
- **Column selection**: Can read subset of columns (not needed here, but nice for future)

### Why Pickle for Convex Hulls?

- **Numpy arrays**: Pickle natively handles numpy arrays with shape preservation
- **Nested structure**: Dict of arrays is natural in pickle
- **Small data**: Only ~30 participants × ~20 vertices each = ~600 coordinates = <5KB

### Why JSON for Metadata?

- **Human-readable**: Easy to inspect and edit if needed
- **Simple types**: Lists, dicts, strings, numbers (no complex objects)
- **Git-friendly**: Text format shows diffs clearly

### Why Session State Over URL Query Params?

- **Complexity**: Selected index is transient, not worth URL management
- **User experience**: No URL pollution, back button works naturally in Streamlit
- **Simplicity**: Session state is native Streamlit pattern for interactive state

### Why streamlit-plotly-events Over Native st.plotly_chart?

- **Click detection**: Native `st.plotly_chart` doesn't expose click events
- **Mature library**: `streamlit-plotly-events` is stable and widely used
- **Minimal overhead**: Small wrapper around plotly, no performance impact

### Why Component-Based Architecture?

- **Testability**: Can test chart rendering logic independently
- **Maintainability**: Clear separation of concerns (data loading, chart creation, UI layout)
- **Reusability**: Components can be reused in other Streamlit apps or Jupyter notebooks
- **Debugging**: Easier to isolate issues to specific components

---

## Risks and Mitigations

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| Streamlit Community Cloud resource limits | App crashes or becomes unresponsive | Low | Pre-compute all heavy operations; slim dependencies; test memory usage locally |
| Pre-computed data becomes stale | Deployed app shows outdated results | Low | Document when to re-run pre-computation; version data files; add last-updated timestamp to app |
| Click sync behavior differs from Dash | User confusion, perceived broken functionality | Medium | Thorough testing; document behavioral differences; consider tooltips/help text |
| Screenshot URLs break (external dependency) | Missing images in detail panel | Low | Screenshots hosted on stable GitHub repo; add error handling (fallback placeholder) |
| Parquet file corruption | App fails to load data | Very Low | Test data loading in CI; validate schema after pre-computation |
| Repository size grows too large | GitHub limits, slow clones | Low | Data files are <20MB total; monitor repo size; use Git LFS if needed |

---

## Success Criteria

**Functional:**
- ✓ All existing Dash interactions work in Streamlit (scatter click, performance click, filters)
- ✓ Charts render correctly with convex hulls, arrows, cluster symbols
- ✓ Detail panel shows correct solution info, screenshot, metrics
- ✓ Cross-chart sync works (clicking performance updates scatter, vice versa)

**Performance:**
- ✓ Initial load <5 seconds
- ✓ Click interactions <1 second
- ✓ Filter changes <1 second
- ✓ Memory usage <500MB (well under 1GB free tier limit)

**Deployment:**
- ✓ Deploys successfully to Streamlit Community Cloud
- ✓ No build errors or dependency conflicts
- ✓ App remains responsive after 10+ minutes of interaction
- ✓ Works on desktop and mobile browsers

**Maintainability:**
- ✓ Clear separation of deployed vs. local-only code
- ✓ Pre-computation script is documented and runnable
- ✓ README explains architecture and deployment process
- ✓ Components are modular and testable

---

## References

### Streamlit Documentation

- **Streamlit Community Cloud**: https://docs.streamlit.io/streamlit-community-cloud
- **Session State**: https://docs.streamlit.io/develop/api-reference/caching-and-state/st.session_state
- **Caching**: https://docs.streamlit.io/develop/api-reference/caching-and-state/st.cache_data
- **Layouts**: https://docs.streamlit.io/develop/api-reference/layout

### Third-Party Libraries

- **streamlit-plotly-events**: https://github.com/null-jones/streamlit-plotly-events
- **Plotly Python**: https://plotly.com/python/
- **Pandas Parquet**: https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.to_parquet.html

### Current Codebase

- **Dash app**: `c:/Py/DS_Viz_SL/scripts/interactive_tool.py` (1175 lines)
- **Analysis modules**: `c:/Py/DS_Viz_SL/scripts/design_space/` (12 modules)
- **Utilities**: `c:/Py/DS_Viz_SL/scripts/utils/utils.py` (1934 lines)
- **Source data**: `c:/Py/DS_Viz_SL/data/MASKED_DATA_analysis_v2.xlsx` (284KB)

---

*Document created: 2026-02-14*
*Last updated: 2026-02-14*
