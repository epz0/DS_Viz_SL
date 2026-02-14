# Stack Research: Dash-to-Streamlit Migration

**Research Date:** 2026-02-14
**Context:** Migrating ~1175-line Dash app from Heroku to Streamlit Community Cloud

---

## Recommended Stack

### Core Framework
- **Streamlit 1.40+** (latest stable as of early 2026)
  - Native Python web framework with declarative syntax
  - Built-in state management via `st.session_state`
  - Automatic rerun on user interaction
  - Native caching with `@st.cache_data` decorator
  - **Why:** Zero-config deployment to Streamlit Community Cloud, minimal migration overhead

### Interactive Plotly Charts
- **Plotly 5.23.0** (match existing version)
  - Use `st.plotly_chart(fig, use_container_width=True)` for responsive charts
  - **Limitation:** Standard `st.plotly_chart` does NOT capture click events
  - **Solution:** Requires `streamlit-plotly-events` library (see below)

### Click Event Handling
- **streamlit-plotly-events 0.0.6** (latest stable)
  - GitHub: [streamlit-plotly-events](https://github.com/null-jones/streamlit-plotly-events)
  - Enables click detection on Plotly charts in Streamlit
  - Returns clicked point data (pointIndex, x, y, curveNumber)
  - **Usage:**
    ```python
    from streamlit_plotly_events import plotly_events

    selected_points = plotly_events(
        fig,
        click_event=True,
        hover_event=False,
        select_event=False,
        override_height=650,
        override_width="100%"
    )
    # Returns: [{"pointIndex": 42, "x": 1.23, "y": 4.56, "curveNumber": 0}]
    ```
  - **Known Issues:**
    - Each interaction triggers full Streamlit rerun (performance trade-off vs Dash callbacks)
    - Cannot distinguish between clicks on scatter points vs convex hull traces — filter by `curveNumber`
    - Must handle empty `selected_points` list when nothing is clicked
    - Component re-renders on every script run — cache figures to avoid regeneration

### Minimal Deployed Dependencies
- **pandas 2.2.3** - DataFrame loading from pre-computed parquet files
- **numpy 2.0.2** - Array operations for existing data structures
- **shapely 2.0.6** - Convex hull polygon operations (already in use, lightweight ~2MB)
- **streamlit-plotly-events 0.0.6** - Click event handling

**Total deployed footprint estimate:** ~150-200MB (vs 500MB+ with full pipeline)

---

## Deployment Stack (Streamlit Community Cloud)

### What Gets Deployed
1. **Streamlit app file** (e.g., `streamlit_app.py`) - Main visualization interface
2. **Pre-computed data files** (parquet format) - See serialization section below
3. **requirements.txt** (minimal):
   ```
   streamlit>=1.40.0
   plotly==5.23.0
   pandas==2.2.3
   numpy==2.0.2
   shapely==2.0.6
   streamlit-plotly-events==0.0.6
   ```
4. **Utility modules** - `scripts/utils/utils.py` for helper functions (convex hull, etc.)
5. **No Excel files** - Data pre-processed locally, only serialized output deployed

### Streamlit Community Cloud Constraints (2026)
- **Memory limit:** 1GB RAM per app
- **Disk limit:** ~500MB for app + dependencies
- **CPU:** Shared, single-core (no multiprocessing)
- **Inactivity timeout:** Apps sleep after ~7 days without traffic, wake on first request
- **Cold start:** ~10-30 seconds to wake from sleep
- **Build time limit:** 10 minutes (not an issue with slim dependencies)
- **Python version:** 3.12 supported (match current `runtime.txt`)
- **No local file writes** - Treat filesystem as read-only post-deployment

### Deployment Configuration Files
- **requirements.txt** - Dependencies (see minimal set above)
- **runtime.txt** - `python-3.12.2` (match existing)
- **.streamlit/config.toml** (optional):
  ```toml
  [theme]
  base = "light"

  [server]
  maxUploadSize = 10  # MB, irrelevant for this app
  enableCORS = false
  ```

---

## Local-Only Stack

### Heavy Dependencies (NOT Deployed)
- **umap-learn 0.5.7** - UMAP dimensionality reduction (~30MB)
- **scikit-learn 1.5.2** - Machine learning utilities (~40MB)
- **scipy 1.14.1** - Spatial algorithms, distance calculations (~50MB)
- **numba 0.60.0** - JIT compilation for UMAP performance (~15MB)
- **llvmlite 0.43.0** - LLVM bindings for Numba (~25MB)
- **openpyxl 3.1.5** - Excel file reading
- **statsmodels 0.14.4** - Statistical tests
- **igraph 0.11.8** - Graph clustering
- **matplotlib 3.9.2**, **seaborn 0.13.2** - Static visualization

### Local Pre-Computation Pipeline
**Workflow:**
1. Run full pipeline locally (existing `scripts/interactive_run.py` logic)
2. Generate all metrics, embeddings, convex hulls, creativity scores
3. Serialize final DataFrame(s) to parquet format
4. Commit parquet files to repo or upload to Streamlit deployment
5. Streamlit app loads pre-computed data on startup with `@st.cache_data`

**Script Structure:**
```
scripts/
  precompute_data.py      # New: Runs full pipeline, exports parquet
  interactive_tool.py     # Existing Dash app (keep for reference)
  interactive_tool_quant.py  # Keep local-only
  interactive_tool_rt.py     # Keep local-only
  stats_run.py            # Keep local-only
  validation_run.py       # Keep local-only
  viz_run.py              # Keep local-only

streamlit_app.py          # New: Streamlit port, loads parquet
```

---

## Key Findings

### 1. Serialization Format: Parquet Over Pickle

**Recommended:** **Parquet** (`.parquet`)

**Rationale:**
- **Columnar storage** - Efficient for DataFrame operations (faster reads than pickle)
- **Compression** - ~50-70% smaller than pickle for typical DataFrames
- **Cross-platform safety** - Pickle can break across Python versions or platforms
- **Pandas native** - `df.to_parquet()` / `pd.read_parquet()` with zero dependencies beyond pandas
- **Schema enforcement** - Type safety preserved (pickle can fail silently on schema drift)

**Example:**
```python
# Local pre-computation
df_base.to_parquet('data/precomputed/df_base.parquet', compression='gzip', index=False)

# Streamlit app loading
@st.cache_data
def load_data():
    df_base = pd.read_parquet('data/precomputed/df_base.parquet')
    return df_base
```

**Benchmark (estimated for ~300 solutions × 80 columns):**
- Pickle size: ~8MB
- Parquet (gzip): ~3-5MB
- Parquet (snappy): ~4-6MB (faster, slightly larger)

**When to use Pickle:**
- Complex Python objects (graphs, UMAP models) that won't be deployed
- Local caching only (never commit pickles to deployment)

**Current State:**
- Existing app pickles UMAP graph to `export/DS_*.pkl` (keep local-only)
- Embedding saved as CSV (`export/DS_*.csv`) — migrate to parquet

---

### 2. Streamlit Caching Strategy

**Use `@st.cache_data` for pre-computed data:**
```python
@st.cache_data
def load_precomputed_data():
    """Load all pre-computed DataFrames and configurations."""
    df_base = pd.read_parquet('data/precomputed/df_base.parquet')
    df_colors = pd.read_parquet('data/precomputed/df_colors.parquet')
    ids = df_base['OriginalID_PT'].unique().tolist()
    return df_base, df_colors, ids
```

**Cache figures conditionally:**
```python
@st.cache_data
def create_base_figure(df_base, df_colors, ids):
    """Generate base Plotly figure with all traces."""
    # Same logic as current fig_DS creation
    return fig
```

**DO NOT cache:**
- User-selected filters (participant dropdown, checkboxes)
- Click event state (changes every interaction)
- Dynamic figure updates (use Plotly's `update_traces` or create new figures)

**Why not `@st.cache_resource`?**
- `cache_resource` is for non-serializable objects (DB connections, ML models)
- DataFrames and figures are serializable → use `cache_data`

---

### 3. Click Event Behavior Differences

**Dash (current):**
- Dual inputs: `Input('main-ds-viz', 'clickData')` + `Input('performance-graph', 'clickData')`
- Callback context (`ctx.triggered_id`) distinguishes which chart was clicked
- Partial updates via `Patch()` — only modified traces re-render
- Independent callbacks fire in parallel

**Streamlit (migration):**
- **No native click events** on `st.plotly_chart` — must use `streamlit-plotly-events`
- **Full page rerun** on every click (no partial updates)
- Click detection returns list of dicts: `[{"pointIndex": N, "curveNumber": M, ...}]`
- Must handle empty list when no point clicked
- Filter by `curveNumber` to distinguish scatter points (trace 62) from convex hulls (traces 0-31) and arrows (traces 32-61)

**Migration Pattern:**
```python
# Render main scatter plot
selected_main = plotly_events(fig_DS, click_event=True, key="main_chart")

# Render performance graph
selected_perf = plotly_events(fig_PF, click_event=True, key="perf_chart")

# Determine last click source
if selected_main:
    clicked_sol = selected_main[0]['pointIndex']
    st.session_state.clicked_solution = clicked_sol
elif selected_perf:
    x_perf = selected_perf[0]['x']
    pat_id = ids[selected_perf[0]['curveNumber'] + 1]
    clicked_sol = df_base[(df_base['OriginalID_PT'] == pat_id) &
                          (df_base['OriginalID_Sol'] == x_perf)].index[0]
    st.session_state.clicked_solution = clicked_sol

# Use session state to populate detail panels
if 'clicked_solution' in st.session_state:
    idx = st.session_state.clicked_solution
    st.write(f"Participant: {df_base.loc[idx, 'OriginalID_PT']}")
    # ... etc.
```

---

### 4. Layout Migration Strategy

**Dash → Streamlit Mapping:**

| Dash Component | Streamlit Equivalent |
|----------------|----------------------|
| `html.Div([...])` | `st.container()` or column layout |
| `html.H3('Title')` | `st.title()` or `st.header()` |
| `html.Label('text', id='x')` | `st.text()` or `st.markdown()` |
| `dcc.Dropdown(ids, multi=True)` | `st.multiselect('Participants', ids)` |
| `dcc.Checklist(['A', 'B'])` | `st.multiselect()` or custom checkboxes |
| `dcc.Graph(figure=fig)` | `plotly_events(fig)` for interactivity |
| `html.Img(src=url)` | `st.image(url)` |
| `Output('x', 'children')` | Direct variable assignment in script flow |

**Two-column layout:**
```python
col1, col2 = st.columns([1, 1])  # 50/50 split

with col1:
    selected_main = plotly_events(fig_DS, click_event=True, key="main")

with col2:
    st.subheader("Solution Details")
    if 'clicked_solution' in st.session_state:
        # Render details
```

**No callbacks** - Streamlit reruns entire script on interaction. Use `st.session_state` for persistence.

---

### 5. Deployment Checklist

**Pre-Deployment (Local):**
- [ ] Create `scripts/precompute_data.py` to run full pipeline
- [ ] Export `df_base` as `data/precomputed/df_base.parquet` (gzip compression)
- [ ] Export `df_colors` as `data/precomputed/df_colors.parquet`
- [ ] Export pre-computed convex hull vertices if not in df_base
- [ ] Verify parquet files load correctly: `pd.read_parquet('...')`
- [ ] Test that all 80+ columns (metrics, core attributes) are preserved

**Streamlit App (`streamlit_app.py`):**
- [ ] Implement `load_precomputed_data()` with `@st.cache_data`
- [ ] Create base figures (scatter, performance) as cached functions
- [ ] Integrate `streamlit-plotly-events` for both charts
- [ ] Map click events to `st.session_state.clicked_solution`
- [ ] Port detail panels (participant info, solution screenshot, core attributes, metrics)
- [ ] Implement participant filter (multiselect dropdown)
- [ ] Implement element visibility toggles (Points/Arrows/Areas checkboxes)
- [ ] Test locally: `streamlit run streamlit_app.py`

**Deployment Configuration:**
- [ ] Create minimal `requirements.txt` (6 packages)
- [ ] Verify `runtime.txt` specifies `python-3.12.2`
- [ ] Add `data/precomputed/*.parquet` to repo (or upload separately)
- [ ] Create `.streamlit/config.toml` for theme/server settings (optional)
- [ ] Push to GitHub repo connected to Streamlit Community Cloud
- [ ] Monitor first deployment logs for dependency errors

**Post-Deployment Validation:**
- [ ] Test click events on main scatter plot
- [ ] Test click events on performance graph
- [ ] Verify participant dropdown filters correctly
- [ ] Verify Points/Arrows/Areas toggles work
- [ ] Check screenshot URLs load from GitHub
- [ ] Validate all metrics display correctly
- [ ] Test on mobile (Community Cloud is public-facing)

---

## Risks & Unknowns

### High Priority

1. **Performance on full dataset (300+ solutions)**
   - **Risk:** Streamlit reruns entire script on every click — may feel sluggish
   - **Mitigation:** Cache figure generation, minimize re-computation in main script
   - **Unknown:** Actual rerun time on Community Cloud hardware (test locally first)

2. **streamlit-plotly-events stability**
   - **Risk:** Third-party library, not officially maintained by Streamlit
   - **Mitigation:** Pin version (`==0.0.6`), test thoroughly before deployment
   - **Unknown:** Behavior with 63 traces (convex hulls + arrows + scatter) — may have undocumented limits

3. **Click detection on overlapping traces**
   - **Risk:** Convex hulls (traces 1-31) may capture clicks intended for points (trace 62)
   - **Mitigation:** Filter `selected_points[0]['curveNumber']` to only accept trace 62 (scatter) for main scatter clicks
   - **Test:** Click on dense cluster regions where hulls overlap

4. **Parquet file size in repo**
   - **Risk:** If df_base with 80+ columns exceeds 50MB, GitHub LFS may be needed
   - **Mitigation:** Use gzip compression, consider splitting into multiple files (base data + metrics)
   - **Unknown:** Actual compressed size (estimate 3-5MB, but could be higher)

### Medium Priority

5. **Arrow trace performance (30 traces × ~10 solutions each)**
   - **Risk:** Re-rendering 30+ arrow traces on every rerun may lag
   - **Mitigation:** Cache base figure, use Plotly's `fig.update_traces()` to toggle visibility
   - **Unknown:** Whether `streamlit-plotly-events` preserves trace visibility state across reruns

6. **Session state persistence across sleep/wake**
   - **Risk:** App sleeps after inactivity — session state clears on wake
   - **Mitigation:** Acceptable UX (user re-clicks a point), or store last-clicked index in URL params
   - **Unknown:** Streamlit's query params API (`st.experimental_get_query_params`) compatibility

7. **Image loading from external GitHub URLs**
   - **Risk:** GitHub may rate-limit image requests or change URL structure
   - **Mitigation:** Images already working in Dash app, same URLs carry over
   - **Unknown:** Streamlit Community Cloud IP blocks (unlikely)

### Low Priority

8. **Cross-browser compatibility of streamlit-plotly-events**
   - **Risk:** Click events may fail in Safari or older browsers
   - **Mitigation:** Test on Chrome, Firefox, Safari post-deployment
   - **Unknown:** Mobile browser support (iOS Safari, Chrome Mobile)

9. **Heroku Procfile cleanup**
   - **Risk:** Leftover `Procfile` and `gunicorn` in requirements.txt may confuse future maintainers
   - **Mitigation:** Document migration, keep Dash app as `scripts/interactive_tool_dash_legacy.py`
   - **Not a blocker:** Doesn't affect Streamlit deployment

---

## Migration Sequence Recommendation

**Phase 1: Pre-Computation (Local)**
1. Create `scripts/precompute_data.py` based on `interactive_tool.py` lines 41-221
2. Run locally, export parquet files to `data/precomputed/`
3. Verify data integrity: check column count, row count, metric ranges

**Phase 2: Minimal Streamlit Prototype**
1. Create `streamlit_app.py` with basic layout (2 columns)
2. Load parquet data with `@st.cache_data`
3. Render static scatter plot with `st.plotly_chart` (no clicks yet)
4. Test locally: `streamlit run streamlit_app.py`

**Phase 3: Click Interactivity**
1. Replace `st.plotly_chart` with `plotly_events` for main scatter
2. Store clicked solution in `st.session_state`
3. Populate detail panels from session state
4. Test click → detail update cycle

**Phase 4: Full Feature Parity**
1. Add performance graph with `plotly_events`
2. Implement participant filter (multiselect)
3. Implement Points/Arrows/Areas toggles
4. Port all 5 detail sections (participant info, screenshot, attributes, metrics, performance)

**Phase 5: Deployment**
1. Create minimal `requirements.txt`
2. Push to GitHub
3. Connect to Streamlit Community Cloud
4. Monitor deployment logs
5. Test live app

**Phase 6: Validation & Documentation**
1. Validate all features against Dash app checklist
2. Update README with deployment URL
3. Document pre-computation workflow for future data updates

---

## Example Streamlit App Structure

```python
# streamlit_app.py

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from streamlit_plotly_events import plotly_events

st.set_page_config(page_title="DS-Viz Interactive Tool", layout="wide")

# --- DATA LOADING ---
@st.cache_data
def load_data():
    df_base = pd.read_parquet('data/precomputed/df_base.parquet')
    df_colors = pd.read_parquet('data/precomputed/df_colors.parquet')
    ids = sorted(df_base['OriginalID_PT'].unique().tolist())
    return df_base, df_colors, ids

df_base, df_colors, ids = load_data()

# --- HEADER ---
st.title("DS-Viz Interactive Tool | GAP Dataset")
col_info1, col_info2 = st.columns([3, 1])
with col_info2:
    st.markdown("[more info](https://doi.org/10.1017/pds.2024.106) | [github](https://github.com/epz0/DS_Viz) | [email](mailto:ep650@cam.ac.uk)")

# --- SIDEBAR FILTERS ---
st.sidebar.header("Filters")
show_elements = st.sidebar.multiselect(
    "Show:",
    ["Points", "Arrows", "Areas"],
    default=["Points", "Arrows", "Areas"]
)
show_participants = st.sidebar.multiselect(
    "Participants:",
    ids,
    default=[]
)

# --- FIGURE GENERATION (cached) ---
@st.cache_data
def create_main_figure(df, df_colors, ids):
    # Same logic as fig_DS creation in interactive_tool.py
    fig = go.Figure()
    # ... (traces for convex hulls, arrows, scatter)
    return fig

@st.cache_data
def create_performance_figure(df, ids):
    # Same logic as fig_PF creation
    fig = go.Figure()
    # ... (traces for performance lines)
    return fig

fig_DS = create_main_figure(df_base, df_colors, ids)
fig_PF = create_performance_figure(df_base, ids)

# --- LAYOUT ---
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("Design Space")
    selected_main = plotly_events(
        fig_DS,
        click_event=True,
        hover_event=False,
        key="main_scatter",
        override_height=650
    )

with col2:
    st.subheader("Solution Details")

    # Handle click events
    if selected_main and len(selected_main) > 0:
        idx = selected_main[0]['pointIndex']
        st.session_state.clicked_solution = idx

    if 'clicked_solution' in st.session_state:
        idx = st.session_state.clicked_solution

        # Participant info
        st.write(f"**Participant:** {df_base.loc[idx, 'OriginalID_PT']}")
        st.write(f"**Group:** {df_base.loc[idx, 'OriginalID_Group']}")
        st.write(f"**Intervention:** {df_base.loc[idx, 'OriginalID_PrePost']}")
        st.write(f"**Solution:** {df_base.loc[idx, 'OriginalID_Sol']}")

        # Screenshot
        img_url = df_base.loc[idx, 'videoPreview']
        st.image(img_url, width=400)

        # Core attributes
        st.markdown("**Core Attributes**")
        st.write(f"Solution: {df_base.loc[idx, 'ca_sol']}")
        st.write(f"Deck: {df_base.loc[idx, 'ca_deck']}")
        # ... etc.

        # Metrics
        st.markdown("**Creativity Metrics**")
        st.write(f"Area explored (Total): {df_base.loc[idx, 'Area-Perc-FS']:.1f}%")
        # ... etc.

    # Performance graph
    st.subheader("Performance Over Time")
    selected_perf = plotly_events(
        fig_PF,
        click_event=True,
        key="performance_graph",
        override_height=300
    )
```

---

## References

- **Streamlit Docs:** https://docs.streamlit.io/
- **streamlit-plotly-events:** https://github.com/null-jones/streamlit-plotly-events
- **Plotly Python Docs:** https://plotly.com/python/
- **Streamlit Community Cloud:** https://streamlit.io/cloud
- **Parquet Format:** https://parquet.apache.org/docs/
- **Pandas Parquet I/O:** https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.to_parquet.html

---

*Research compiled: 2026-02-14*
*Next step: Implement pre-computation script (`scripts/precompute_data.py`)*
