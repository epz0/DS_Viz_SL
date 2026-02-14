# Phase 5: Full Feature Parity & Deployment - Research

**Researched:** 2026-02-14
**Domain:** Plotly convex hull/polygon rendering, exploration arrows, complete metrics display, Streamlit Community Cloud deployment optimization
**Confidence:** HIGH

## Summary

Phase 5 completes the Streamlit migration by adding the three major visualization features still missing from the original Dash app: (1) full design space convex hull as a background trace, (2) per-participant convex hulls as semi-transparent filled polygons (31 traces), and (3) per-participant exploration arrows showing solution sequences (30 traces). It also adds the remaining creativity metrics to the detail panel (area explored, distance traveled, clusters visited: total/pre/post, novelty neighbors/density, performance). Finally, it ensures the app deploys stably to Streamlit Community Cloud within the free tier's 1GB memory limit.

The critical technical challenges are:

1. **Rendering 62 additional traces efficiently** (31 hulls + 1 full DS hull + 30 arrow sequences) on top of the existing scatter trace without exceeding memory limits or causing performance degradation
2. **Managing trace visibility** with participant filtering and display toggles (Points/Arrows/Areas checkboxes)
3. **Optimizing memory footprint** to stay under 800MB (target) or 1GB (hard limit) on Streamlit Community Cloud

**Good news:** All convex hull vertices are pre-computed and stored in `convex_hulls.pkl` (5.5KB), and all metrics are pre-computed in `df_base.parquet` (148KB). The original Dash app already demonstrates the exact trace structure needed. Plotly's `go.Scatter` with `fill='toself'` is the standard approach for rendering filled polygons. The challenge is not computation (already done) but orchestrating trace rendering and visibility efficiently within Streamlit's rerun model.

**Primary recommendation:** Build all 64 traces once per render (1 full DS hull + 31 participant hulls + 30 arrow sequences + 1 scatter + 1 performance chart = 64 total traces across two figures), then control visibility via trace.visible property based on session state filters. Use `showlegend=False` to avoid legend clutter. Monitor memory usage during development and deploy with aggressive caching (`@st.cache_data` for all data loads). Target < 800MB memory usage to leave headroom under the 1GB Community Cloud limit.

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| plotly | >=5.23.0 | Convex hull polygons and arrow traces | Already in use; go.Scatter with fill='toself' is canonical for filled polygons |
| streamlit | >=1.30.0 | Web framework and deployment platform | Already in use; Community Cloud is target platform |
| pandas | >=2.2.0 | Data filtering for per-participant traces | Already in use |
| pickle | (stdlib) | Load pre-computed convex hull vertices | Standard Python library, efficient binary format |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| shapely | >=2.0.0 | (Already computed) Convex hull calculation | Not needed at runtime - hulls pre-computed in Phase 0 |
| numpy | >=1.26.0 | Array operations for trace construction | Already in use for embeddings |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Pre-computed hulls | Runtime computation with shapely | Would add 80MB+ to deployment deps and compute on every render; already pre-computed in Phase 0 |
| go.Scatter fill='toself' | Plotly Shapes (add_shape) | Shapes are static annotations, not traces; can't control visibility per participant easily |
| Single trace per hull | Combined multi-polygon trace | Visibility control requires per-participant traces; combined trace complicates filtering |

**Installation:**
No new dependencies. All required libraries already in `requirements.txt` from Phase 1.

## Architecture Patterns

### Recommended Trace Structure
```
Figure 1 (Scatter Plot):
├── Trace 0: Full DS convex hull (background)
├── Traces 1-31: Per-participant convex hulls (GALL, P_001-P_030)
├── Traces 32-61: Per-participant arrow sequences (P_001-P_030, no GALL arrows)
└── Trace 62: All solutions scatter points

Figure 2 (Performance Chart):
└── Traces 0-29: Per-participant performance lines (P_001-P_030, no GALL)
```

### Pattern 1: Loading Pre-Computed Convex Hulls
**What:** Load convex hull vertices from pickle file and build trace dictionaries
**When to use:** App initialization, cached with `@st.cache_data`
**Example:**
```python
# Source: C:\Py\DS_Viz_SL\streamlit_app\data\convex_hulls.pkl structure
import pickle
import streamlit as st

@st.cache_data
def load_convex_hulls():
    """Load pre-computed convex hull vertices.

    Returns:
        dict: {
            'full_ds': {'x': [...], 'y': [...], 'area': float},
            'GALL': {'x': [...], 'y': [...], 'area': float},
            'P_001': {'x': [...], 'y': [...], 'area': float},
            ...
            'P_030': {'x': [...], 'y': [...], 'area': float}
        }
    """
    with open(DATA_DIR / 'convex_hulls.pkl', 'rb') as f:
        return pickle.load(f)

# Usage
hulls = load_convex_hulls()
full_ds_x = hulls['full_ds']['x']  # ~11 points
full_ds_y = hulls['full_ds']['y']  # ~11 points
```

### Pattern 2: Rendering Full DS Convex Hull
**What:** Add full design space convex hull as first trace (background layer)
**When to use:** Always render as base layer, before participant hulls
**Example:**
```python
# Source: Original Dash app lines 228-246 (interactive_tool.py)
fig = go.Figure()

# Full DS hull (trace 0, background)
fig.add_trace(go.Scatter(
    x=hulls['full_ds']['x'],
    y=hulls['full_ds']['y'],
    mode='lines',
    fill='toself',
    fillcolor='rgba(240,240,240,0.5)',  # Light gray, semi-transparent
    line=dict(color='rgba(240,240,240,0.5)', width=0),  # No visible border
    hoverinfo='skip',
    name='full_ds_hull',
    showlegend=False,
))
```

### Pattern 3: Rendering Per-Participant Convex Hulls
**What:** Add one trace per participant (31 traces: GALL + P_001-P_030)
**When to use:** After full DS hull, before arrow sequences
**Example:**
```python
# Source: Original Dash app lines 248-279 (interactive_tool.py)
# Helper: Convert hex to RGBA with alpha
def hex_to_rgba(hex_color, alpha):
    """Convert #RRGGBB to 'rgba(R, G, B, alpha)'"""
    h = hex_color.lstrip('#')
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f'rgba({r}, {g}, {b}, {alpha})'

# Add per-participant hulls (traces 1-31)
for pt_id in metadata['participant_ids']:  # ['GALL', 'P_001', ..., 'P_030']
    hull_data = hulls[pt_id]
    color = metadata['color_mapping'][pt_id]

    # Line color: 30% opacity, Fill color: 10% opacity
    line_color = hex_to_rgba(color, 0.3)
    fill_color = hex_to_rgba(color, 0.1)

    fig.add_trace(go.Scatter(
        x=hull_data['x'],
        y=hull_data['y'],
        mode='lines',
        fill='toself',
        fillcolor=fill_color,
        line=dict(color=line_color, width=1),
        hoverinfo='skip',
        name=f'{pt_id}_hull',
        showlegend=False,
        visible=True  # Controlled by filters later
    ))
```

### Pattern 4: Rendering Exploration Arrows
**What:** Add one trace per participant showing solution sequence as arrows
**When to use:** After convex hulls, before scatter points
**Example:**
```python
# Source: Original Dash app lines 281-298 (interactive_tool.py)
# Add arrow sequences (traces 32-61, P_001-P_030 only, no GALL)
participant_ids = metadata['participant_ids'][1:31]  # Exclude GALL

for pt_id in participant_ids:
    # Get participant solutions sorted by OriginalID_Sol
    pt_data = df[df['OriginalID_PT'] == pt_id].sort_values('OriginalID_Sol')
    x_vals = pt_data['x_emb'].tolist()
    y_vals = pt_data['y_emb'].tolist()
    color = metadata['color_mapping'][pt_id]
    arrow_color = hex_to_rgba(color, 0.5)  # 50% opacity

    fig.add_trace(go.Scatter(
        x=x_vals,
        y=y_vals,
        mode='lines+markers',
        line=dict(color=arrow_color, width=1),
        marker=dict(
            symbol='arrow-up',      # Plotly arrow symbol
            size=8,
            angleref='previous',    # Arrow points from previous to current point
            color=arrow_color
        ),
        hoverinfo='skip',
        name=f'{pt_id}_arrows',
        showlegend=False,
        visible=True  # Controlled by filters later
    ))
```

### Pattern 5: Controlling Trace Visibility with Filters
**What:** Update trace.visible property based on participant filter and display toggles
**When to use:** After building all traces, apply visibility based on session state
**Example:**
```python
# After adding all traces to fig, apply filters
# Trace indices:
#   0: Full DS hull
#   1-31: Participant hulls (GALL at 1, P_001 at 2, ..., P_030 at 31)
#   32-61: Arrow sequences (P_001 at 32, ..., P_030 at 61)
#   62: Scatter points

# Get selected participants from sidebar
selected_participants = st.session_state.get('participant_filter', metadata['participant_ids'])

# Get display toggles from sidebar
show_areas = st.session_state.get('show_areas', True)
show_arrows = st.session_state.get('show_arrows', True)
show_points = st.session_state.get('show_points', True)

# Full DS hull: always show if Areas enabled
fig.data[0].visible = show_areas

# Per-participant hulls (traces 1-31)
for i, pt_id in enumerate(metadata['participant_ids'], start=1):
    # Show if: Areas enabled AND participant selected
    fig.data[i].visible = show_areas and (pt_id in selected_participants)

# Arrow sequences (traces 32-61, P_001-P_030 only)
for i, pt_id in enumerate(metadata['participant_ids'][1:31], start=32):
    # Show if: Arrows enabled AND participant selected
    fig.data[i].visible = show_arrows and (pt_id in selected_participants)

# Scatter points (trace 62): show if Points enabled
fig.data[62].visible = show_points
```

### Pattern 6: Adding Metrics to Detail Panel
**What:** Display all creativity metrics below core attributes in detail panel
**When to use:** When point is selected (st.session_state.selected_point_idx is not None)
**Example:**
```python
# Source: Original Dash app lines 614-682 (interactive_tool.py)
# After existing detail panel sections (participant info, solution details, core attributes, screenshot)

if st.session_state.selected_point_idx is not None:
    idx = st.session_state.selected_point_idx
    row = df.iloc[idx]

    # ... existing detail panel sections ...

    # Section 7: Creativity Metrics (NEW)
    st.divider()
    st.markdown("##### Space Exploration / Creativity Metrics")

    # Helper: Format metric or show 'N/A'
    def fmt_metric(value, decimals=1, suffix=''):
        if isinstance(value, str) and value == 'N/A':
            return 'N/A'
        try:
            return f"{float(value):.{decimals}f}{suffix}"
        except (ValueError, TypeError):
            return 'N/A'

    # Area explored (DETL-07)
    area_tot = fmt_metric(row['Area-Perc-FS'], 1, '%')
    area_pre = fmt_metric(row['Area-Perc-PRE'], 1, '%')
    area_post = fmt_metric(row['Area-Perc-POST'], 1, '%')
    st.markdown(f"**Area explored** | Tot.: {area_tot} | Pre: {area_pre} | Post: {area_post}")

    # Distance traveled (DETL-08)
    dist_tot = fmt_metric(row['totaldist_FS'], 1)
    dist_pre = fmt_metric(row['totaldist_PRE'], 1)
    dist_post = fmt_metric(row['totaldist_PST'], 1)
    st.markdown(f"**Distance travel.** | Total: {dist_tot} | Pre: {dist_pre} | Post: {dist_post}")

    # Clusters visited (DETL-09)
    clust_tot = fmt_metric(row['n_clusters'], 0)
    clust_pre = fmt_metric(row['n_clusters_pre'], 0)
    clust_post = fmt_metric(row['n_clusters_post'], 0)
    st.markdown(f"**# Clusters visit.** | Total: {clust_tot} | Pre: {clust_pre} | Post: {clust_post}")

    # Novelty (DETL-10)
    nov_neig = fmt_metric(row['novel_nn'], 2)
    nov_dens = fmt_metric(row['novelty_norm'], 2)
    st.markdown(f"**Novelty** | Neighbors: {nov_neig} | Density: {nov_dens}")

    # Performance (DETL-11)
    perf = fmt_metric(row['performance'], 2)
    st.markdown(f"**Solution Performance:** {perf}")
```

### Anti-Patterns to Avoid
- **Don't compute hulls at runtime:** shapely adds ~80MB to deployment. Use pre-computed hulls from pickle file.
- **Don't use a single trace with None separators for all hulls:** Visibility control becomes impossible; must use separate traces per participant.
- **Don't rebuild all 64 traces on every interaction:** Build once per render based on session state, update only visibility properties.
- **Don't forget to set showlegend=False on hull/arrow traces:** 31 hull + 30 arrow traces = 61 legend entries = unusable UI.
- **Don't use scattergl for hulls with fill='toself':** Known rendering bugs with scattergl + multiple polygons; stick with go.Scatter.
- **Don't hardcode GALL index assumptions:** GALL is at index 0 in participant_ids but has no arrows (P_001-P_030 only for arrows).

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Convex hull calculation | Custom polygon algorithm | Pre-computed hulls from Phase 0 | Already computed using shapely; no runtime deps needed |
| Filled polygon rendering | SVG paths or custom shapes | go.Scatter with fill='toself' | Plotly's canonical approach; handles edge cases, supports visibility toggling |
| Hex to RGBA conversion | String manipulation | Standard formula (int conversion) | Edge cases (3-char hex, uppercase/lowercase) are subtle |
| Memory profiling | Manual logging | Streamlit Cloud metrics dashboard | Built-in monitoring available in deployment settings |
| Trace visibility management | Recreating figures | Update trace.visible property | Efficient; Plotly doesn't re-render unchanged traces |

**Key insight:** The original Dash app uses `Patch()` for efficient partial figure updates. Streamlit requires full figure rebuilds on every rerun, but this is NOT a performance issue because: (1) building 64 traces from arrays is fast (~10ms), (2) rendering happens client-side in the browser, (3) network round-trip from st.rerun() dominates latency, not Python figure construction. The critical optimization is caching data loads, not micro-optimizing trace creation.

## Common Pitfalls

### Pitfall 1: Trace Index Off-by-One Errors
**What goes wrong:** Hull/arrow visibility logic uses wrong trace indices, causing wrong participants to show/hide.

**Why it happens:** Trace order matters. Full DS hull is trace 0, participant hulls are traces 1-31 (GALL at 1, P_001 at 2, etc.), arrows are traces 32-61 (P_001 at 32, no GALL), scatter is trace 62. Off-by-one when mapping participant to trace index breaks visibility control.

**How to avoid:**
- Document trace index mapping clearly at top of figure-building code
- Use `enumerate(metadata['participant_ids'], start=1)` for hulls (GALL is index 1, not 0)
- Use `enumerate(metadata['participant_ids'][1:31], start=32)` for arrows (P_001 is index 32)
- Verify with `print(fig.data[i].name)` during development

**Warning signs:** Filtering participants shows wrong hulls, clicking Areas checkbox shows P_002's hull instead of P_001's, GALL hull visible when GALL not selected.

### Pitfall 2: Memory Limit Exceeded on Deployment
**What goes wrong:** App deploys successfully but crashes with "App over its resource limits" when users interact with it.

**Why it happens:** Streamlit Community Cloud has a 1GB memory limit. Base Python + libraries consume ~150-200MB. Multiple users trigger multiple reruns, each building 64 traces. Inefficient data structures or uncached loads cause memory bloat.

**How to avoid:**
- Use `@st.cache_data` on all data loading functions (load_solutions, load_metadata, load_convex_hulls)
- Monitor memory during local development: `memory_profiler` or `tracemalloc`
- Test with multiple concurrent users locally before deployment
- Target < 800MB peak usage to leave headroom
- Use parquet (binary, compressed) not CSV for df_base
- Avoid storing large objects in session state (store only indices/IDs)

**Warning signs:** Local app runs fine, deployed app crashes after 2-3 interactions, Streamlit Cloud dashboard shows memory near 1GB, reboot fixes temporarily then crashes again.

### Pitfall 3: Convex Hull Polygons Not Closed
**What goes wrong:** Hull traces render as lines without fill, or fill extends outside polygon.

**Why it happens:** Plotly `fill='toself'` requires first and last points to be identical to close the polygon. Pre-computed hulls from shapely include the closing point (first point repeated at end), but if you accidentally slice or filter the vertices, you may lose the closing point.

**How to avoid:**
- Verify pre-computed hulls have closing point: `assert hulls['P_001']['x'][0] == hulls['P_001']['x'][-1]`
- Don't slice hull vertices (use full list from pickle file)
- Test visually: filled polygon should have no gaps

**Warning signs:** Hull renders as unfilled line, fill color spills outside intended boundary, polygon appears open.

### Pitfall 4: Arrow Sequences Don't Show Direction
**What goes wrong:** Arrows render as dots or lines without visible arrow heads.

**Why it happens:** Plotly's arrow marker requires `angleref='previous'` to orient arrows correctly. Without this, arrows default to angle=0 (all pointing up). Also requires at least 2 points per trace (can't compute direction with 1 point).

**How to avoid:**
- Always set `marker=dict(symbol='arrow-up', angleref='previous', ...)`
- Filter out participants with only 1 solution (no sequence to show)
- Test with participant who has multiple solutions (e.g., P_001 has ~15 solutions)

**Warning signs:** Arrows all point upward regardless of movement direction, no arrows visible (only line trace), arrows render as circles.

### Pitfall 5: GALL Participant Special Case Not Handled
**What goes wrong:** Arrow trace index calculation assumes GALL has arrows, causing off-by-one error. Or GALL metrics display incorrectly (GALL solutions have 'N/A' for many metrics).

**Why it happens:** GALL is the gallery of all solutions (index 0 in participant_ids) but:
- Has no arrows (arrows are only P_001-P_030, 30 traces not 31)
- Metrics like n_clusters, Area-Perc-PRE are 'N/A' for GALL solutions
- Original Dash app explicitly checks `if pt_focus == 'GALL'` in multiple callbacks

**How to avoid:**
- Arrows loop: `for pt_id in metadata['participant_ids'][1:31]` (exclude GALL)
- Metrics display: use fmt_metric helper that handles 'N/A' strings gracefully
- Performance chart: GALL has no trace (traces 0-29 are P_001-P_030 only)

**Warning signs:** Clicking GALL solution causes IndexError in arrow visibility logic, GALL metrics show 'nan' instead of 'N/A', GALL selection tries to highlight non-existent performance trace.

### Pitfall 6: Display Toggles Don't Update Figure
**What goes wrong:** User clicks Areas checkbox in sidebar, but convex hulls don't appear/disappear.

**Why it happens:** Streamlit's session state updates, but figure was built before checkbox change. Need to trigger `st.rerun()` when toggles change, OR rebuild figure after reading checkbox values.

**How to avoid:**
- Read checkbox values from session state BEFORE building figure
- Checkboxes with `key` parameter automatically update session state
- No need for explicit `st.rerun()` if figure is rebuilt on every script execution
- Ensure toggles are outside cached functions (caching would freeze toggle state)

**Warning signs:** Toggling checkboxes does nothing, need to click a point first before toggles work, toggles work on second interaction but not first.

## Code Examples

Verified patterns from original Dash app:

### Building Full DS Convex Hull Trace
```python
# Source: Original Dash app lines 228-246 (interactive_tool.py)
import plotly.graph_objects as go

fig = go.Figure()

# Load pre-computed hull vertices
hulls = load_convex_hulls()  # Cached

# Full design space convex hull (background trace)
fig.add_trace(go.Scatter(
    x=hulls['full_ds']['x'],
    y=hulls['full_ds']['y'],
    mode='lines',
    fill='toself',
    fillcolor='rgba(240,240,240,0.5)',
    line=dict(color='rgba(240,240,240,0.5)', width=0),
    hoverinfo='skip',
    name='full_ds_hull',
    showlegend=False,
))
```

### Building Per-Participant Convex Hulls
```python
# Source: Original Dash app lines 248-279 (interactive_tool.py)
def hex_to_rgba(hex_color, alpha):
    """Convert #RRGGBB to rgba(R, G, B, alpha)"""
    h = hex_color.lstrip('#')
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f'rgba({r}, {g}, {b}, {alpha})'

# Add one hull per participant (31 traces)
for pt_id in metadata['participant_ids']:
    hull = hulls[pt_id]
    color = metadata['color_mapping'][pt_id]

    fig.add_trace(go.Scatter(
        x=hull['x'],
        y=hull['y'],
        mode='lines',
        fill='toself',
        fillcolor=hex_to_rgba(color, 0.1),  # 10% opacity fill
        line=dict(color=hex_to_rgba(color, 0.3), width=1),  # 30% opacity border
        hoverinfo='skip',
        name=f'{pt_id}_hull',
        showlegend=False,
    ))
```

### Building Exploration Arrow Sequences
```python
# Source: Original Dash app lines 281-298 (interactive_tool.py)
# P_001 through P_030 only (no GALL arrows)
for pt_id in metadata['participant_ids'][1:31]:
    pt_data = df[df['OriginalID_PT'] == pt_id].sort_values('OriginalID_Sol')
    x_vals = pt_data['x_emb'].tolist()
    y_vals = pt_data['y_emb'].tolist()
    color = metadata['color_mapping'][pt_id]

    fig.add_trace(go.Scatter(
        x=x_vals,
        y=y_vals,
        mode='lines+markers',
        line=dict(color=hex_to_rgba(color, 0.5), width=1),
        marker=dict(
            symbol='arrow-up',
            size=8,
            angleref='previous',  # Critical for arrow direction
            color=hex_to_rgba(color, 0.5)
        ),
        hoverinfo='skip',
        name=f'{pt_id}_arrows',
        showlegend=False,
    ))
```

### Controlling Trace Visibility Based on Filters
```python
# After building all traces, apply visibility logic
# Trace indices: 0=full_ds, 1-31=hulls, 32-61=arrows, 62=scatter

# Get filter values from session state (set by sidebar widgets)
selected_participants = st.session_state.get('participant_filter', metadata['participant_ids'])
show_areas = st.session_state.get('show_areas', True)
show_arrows = st.session_state.get('show_arrows', True)
show_points = st.session_state.get('show_points', True)

# Full DS hull (trace 0)
fig.data[0].visible = show_areas

# Per-participant hulls (traces 1-31)
for i, pt_id in enumerate(metadata['participant_ids'], start=1):
    fig.data[i].visible = show_areas and (pt_id in selected_participants)

# Arrow sequences (traces 32-61, P_001-P_030 only)
for i, pt_id in enumerate(metadata['participant_ids'][1:31], start=32):
    fig.data[i].visible = show_arrows and (pt_id in selected_participants)

# Scatter points (trace 62)
# NOTE: Scatter trace uses filtered df, so visibility toggle is separate from filtering
fig.data[62].visible = show_points
```

### Displaying All Creativity Metrics
```python
# Source: Original Dash app lines 614-682, 838-916 (interactive_tool.py)
if st.session_state.selected_point_idx is not None:
    idx = st.session_state.selected_point_idx
    row = df.iloc[idx]

    st.divider()
    st.markdown("##### Space Exploration / Creativity Metrics")

    # Helper function for metric formatting
    def fmt(value, decimals=1, suffix=''):
        """Format metric value or return 'N/A'"""
        if isinstance(value, str) and value == 'N/A':
            return 'N/A'
        try:
            return f"{float(value):.{decimals}f}{suffix}"
        except (ValueError, TypeError):
            return 'N/A'

    # Area explored (percent of full design space)
    st.markdown(f"**Area explored** | Tot.: {fmt(row['Area-Perc-FS'], 1, '%')} | "
                f"Pre: {fmt(row['Area-Perc-PRE'], 1, '%')} | "
                f"Post: {fmt(row['Area-Perc-POST'], 1, '%')}")

    # Distance traveled (sum of distances between consecutive solutions)
    st.markdown(f"**Distance travel.** | Total: {fmt(row['totaldist_FS'], 1)} | "
                f"Pre: {fmt(row['totaldist_PRE'], 1)} | "
                f"Post: {fmt(row['totaldist_PST'], 1)}")

    # Clusters visited (unique cluster IDs encountered)
    st.markdown(f"**# Clusters visit.** | Total: {fmt(row['n_clusters'], 0)} | "
                f"Pre: {fmt(row['n_clusters_pre'], 0)} | "
                f"Post: {fmt(row['n_clusters_post'], 0)}")

    # Novelty metrics (neighbors count and density-based)
    st.markdown(f"**Novelty** | Neighbors: {fmt(row['novel_nn'], 2)} | "
                f"Density: {fmt(row['novelty_norm'], 2)}")

    # Performance (budget efficiency: 15000 / budgetUsed if pass, else 0)
    st.markdown(f"**Solution Performance:** {fmt(row['performance'], 2)}")
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Runtime convex hull computation | Pre-computed hulls in pickle file | Phase 0 (2026-02) | Eliminates shapely dependency from deployment, saves ~80MB, no compute on render |
| Dash Patch() for visibility updates | Full figure rebuild per render | Streamlit migration (2024-2026) | No performance penalty; trace construction is fast, rendering is client-side |
| Separate Dash callbacks per metric group | Single detail panel render | Streamlit rerun model | Simpler code, all metrics update atomically on selection change |
| Multiple plotly.js issues with scattergl + fill='toself' | Use go.Scatter (not scattergl) for hulls | Plotly.js #2291 (2018) | Known rendering bugs with scattergl multi-polygon fills; standard Scatter is reliable |

**Deprecated/outdated:**
- Using alphahull parameter for convex hulls: Use pre-computed shapely hulls instead (no runtime computation)
- Relying on Streamlit Cloud automatic dependency detection: Always specify exact versions in requirements.txt
- Assuming 800MB is "safe" memory headroom: Community Cloud limit is 1GB hard limit; monitor actual usage, target < 800MB but be prepared to optimize further

## Open Questions

1. **Will 64 total traces (across two figures) cause rendering performance issues on slower devices?**
   - What we know: Original Dash app renders all traces without issue. Plotly handles 100+ traces efficiently. Rendering happens client-side (browser), not server-side.
   - What's unclear: Whether Streamlit's iframe embedding adds overhead vs. native Dash rendering. Whether mobile browsers struggle with 64 traces.
   - Recommendation: Build as designed. If performance issues arise, consider virtualizing traces (only render hulls/arrows for visible participants). Monitor with browser dev tools (Chrome Performance tab).

2. **What's the actual memory footprint of the deployed app with all features?**
   - What we know: Base libraries ~150-200MB. df_base.parquet is 148KB, hulls are 5.5KB. Streamlit Cloud limit is 1GB.
   - What's unclear: Memory usage with multiple concurrent users (each session has own df copy?). Whether caching reduces per-session memory or is shared.
   - Recommendation: Deploy Phase 5 to staging app first, monitor memory via Streamlit Cloud dashboard, load test with 5-10 concurrent users. If exceeds 800MB, optimize (reduce trace count, virtualize rendering, use session state more sparingly).

3. **Should we virtualize trace rendering (only build traces for selected participants)?**
   - What we know: Full trace set is 64 traces. Filtered rendering would reduce to ~3-5 traces if user selects 2-3 participants.
   - What's unclear: Whether the complexity of dynamic trace management outweighs memory/performance benefits. Whether Plotly's visibility toggling is already efficient enough.
   - Recommendation: Start with full trace set, visibility toggling. If memory/performance issues arise, refactor to build only filtered traces. Complexity tradeoff favors simple approach until proven necessary.

4. **How do we handle edge cases where participants have very few solutions (e.g., 2-3 points)?**
   - What we know: Convex hull of 2 points is a line, 3 points is a triangle. Arrow sequence with 2 points shows one arrow.
   - What's unclear: Whether these degenerate cases render visually poorly (tiny triangles, single arrows). Whether users expect different treatment.
   - Recommendation: Render all cases uniformly. Degenerate hulls are scientifically accurate (limited exploration = small area). No special casing needed unless user feedback indicates confusion.

## Sources

### Primary (HIGH confidence)
- Original Dash app code (C:\Py\DS_Viz_SL\scripts\interactive_tool.py) - Lines 228-298 (hull and arrow trace construction), lines 614-682 (metrics display layout), lines 838-916 (metrics update callback)
- Pre-computed data files (C:\Py\DS_Viz_SL\streamlit_app\data\) - convex_hulls.pkl structure, df_base.parquet columns verified
- Phase 0 Verification Report (C:\Py\DS_Viz_SL\.planning\phases\00-data-preparation\00-VERIFICATION.md) - Pre-computed data provenance and validation
- Phase 2 Research (C:\Py\DS_Viz_SL\.planning\phases\02-single-chart-click-handling\02-RESEARCH.md) - Session state patterns, detail panel structure
- Phase 4 Research (C:\Py\DS_Viz_SL\.planning\phases\04-performance-chart-cross-chart-sync\04-RESEARCH.md) - Trace visibility patterns, multi-chart rendering

### Secondary (MEDIUM confidence)
- [Streamlit Cloud resource limits blog post](https://blog.streamlit.io/common-app-problems-resource-limits/) - 1GB memory limit confirmed
- [Streamlit Cloud status and limitations docs](https://docs.streamlit.io/deploy/streamlit-community-cloud/status) - Free tier constraints
- [Streamlit Community discussion: App over resource limits](https://discuss.streamlit.io/t/app-over-its-resource-limits/36667) - Memory as primary bottleneck
- [Plotly filled area plots documentation](https://plotly.com/python/filled-area-plots/) - fill='toself' usage and examples
- [Plotly go.Scatter API reference](https://plotly.com/python-api-reference/generated/plotly.graph_objects.Scatter.html) - Marker angleref parameter for arrows
- [Plotly issue #2291: scattergl fillcolor incorrect with multiple polygons](https://github.com/plotly/plotly.js/issues/2291) - Known bug with scattergl + fill='toself'

### Tertiary (LOW confidence - community patterns)
- [Streamlit Community discussion: Confused about resource limits](https://discuss.streamlit.io/t/confused-about-how-resource-limit-scales/37922) - Anecdotal memory optimization strategies
- [Plotly Community discussion: Efficient polygon drawing](https://community.plotly.com/t/efficient-polygon-drawing/91655) - fill='toself' performance patterns (2023, unverified)

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - All libraries already in use, no new dependencies
- Architecture: HIGH - Original Dash app provides complete reference implementation for all 3 features (hulls, arrows, metrics)
- Pitfalls: HIGH - All identified from original Dash app code (trace indexing, GALL special case) and verified Streamlit Cloud documentation (1GB limit)
- Deployment constraints: MEDIUM-HIGH - 1GB limit verified in official docs, but actual memory usage under load is uncertain without testing

**Research date:** 2026-02-14
**Valid until:** 2026-03-14 (30 days - stable domain, Plotly/Streamlit APIs are mature, Streamlit Cloud limits unchanged since 2022)

**Critical validation needed:**
- Deploy Phase 5 to Streamlit Community Cloud and monitor memory usage with all features enabled
- Load test with multiple concurrent users to verify <800MB target
- Verify convex hull rendering quality (closed polygons, correct fill) across participants
- Verify arrow directionality (angleref='previous' works as expected)
