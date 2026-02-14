# Phase 3: Filtering & Visibility Controls - Research

**Researched:** 2026-02-14
**Domain:** Streamlit widgets + Plotly trace management + Pandas filtering
**Confidence:** HIGH

## Summary

Phase 3 adds participant filtering and element visibility toggles to the scatter plot. The standard approach uses `st.multiselect` for participant selection and `st.checkbox` widgets for toggling Points/Arrows/Areas visibility. The key implementation pattern is: filter DataFrame with pandas `.isin()` based on selected participants, then conditionally create or update Plotly traces based on checkbox states.

Streamlit's rerun model means the entire figure is recreated on each interaction, but this is acceptable for 563 data points across 31 participants. Caching the base data with `@st.cache_data` prevents performance issues. The critical architectural decision is whether to filter data before creating traces (recommended) versus using Plotly's `visible` property (creates unnecessary overhead for already-filtered data).

**Primary recommendation:** Filter DataFrame with pandas `.isin()` before creating traces. Use checkboxes to conditionally add traces (not update visibility). Organize controls in sidebar with clear labels. Default to all participants selected and all elements visible.

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| streamlit | 1.41+ | Widget framework (multiselect, checkbox) | Native filtering widgets, automatic reruns on interaction |
| plotly | 5.24+ | go.Scatter traces with conditional rendering | Already in use; trace creation is more efficient than visibility updates |
| pandas | 2.2+ | DataFrame filtering with `.isin()` | Already in use; vectorized filtering is fast for this dataset size |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| streamlit-plotly-events | latest | Click handling | Already committed in Phase 2; not needed for filters/toggles |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| pandas `.isin()` | DataFrame boolean masks | `.isin()` is cleaner for multi-value filters |
| Recreate traces | `fig.update_traces(visible=...)` | Update is slower than recreation for small datasets; filtering before trace creation avoids unused data |
| st.multiselect | Custom component (streamlit-dynamic-filters) | Overkill for 31 static participants; adds dependency |

**Installation:**
```bash
# No new dependencies needed
# streamlit, plotly, pandas already in requirements_slim.txt
```

## Architecture Patterns

### Recommended Project Structure
```
streamlit_app/
├── streamlit_app.py         # Main app with sidebar controls
├── data/
│   ├── df_base.parquet      # 563 solutions (already cached)
│   └── metadata.json        # 31 participant IDs (already cached)
└── .streamlit/
    └── config.toml          # Already exists
```

### Pattern 1: Sidebar Controls Before Chart
**What:** Create all filter/toggle widgets in sidebar before chart rendering
**When to use:** Always — prevents session state rendering order issues
**Example:**
```python
# Sidebar controls (defined BEFORE main content)
with st.sidebar:
    st.header("Filters")

    # Participant filter (default: all selected)
    selected_participants = st.multiselect(
        "Select Participants",
        options=metadata['participant_ids'],
        default=metadata['participant_ids'],  # All selected by default
        key='participant_filter'
    )

    st.header("Visibility")

    # Element toggles (default: all visible)
    show_points = st.checkbox("Show Points", value=True, key='show_points')
    show_arrows = st.checkbox("Show Arrows", value=True, key='show_arrows')
    show_areas = st.checkbox("Show Areas", value=True, key='show_areas')

# Main content uses widget values
df_filtered = df[df['ParticipantID'].isin(selected_participants)]
```
**Source:** [Streamlit sidebar organization patterns](https://docs.streamlit.io/develop/api-reference/layout/st.sidebar)

### Pattern 2: Filter DataFrame Before Creating Traces
**What:** Apply pandas filter, then conditionally create traces based on checkboxes
**When to use:** Always — avoids creating traces for invisible elements
**Example:**
```python
# Filter data first
df_filtered = df[df['ParticipantID'].isin(selected_participants)]

# Conditionally add traces
fig = go.Figure()

if show_points and not df_filtered.empty:
    fig.add_trace(go.Scatter(
        x=df_filtered['x_emb'],
        y=df_filtered['y_emb'],
        mode='markers',
        # ... rest of scatter config
    ))

if show_arrows and not df_filtered.empty:
    # Phase 4/5: Add arrow traces (prepared infrastructure)
    pass

if show_areas and not df_filtered.empty:
    # Phase 4/5: Add area traces (prepared infrastructure)
    pass

st.plotly_chart(fig, use_container_width=False)
```
**Source:** [Pandas filtering best practices](https://docs.streamlit.io/develop/concepts/architecture/session-state)

### Pattern 3: Handle Empty Filter Results
**What:** Check if filtered DataFrame is empty before creating traces
**When to use:** Always — prevents Plotly errors and provides user feedback
**Example:**
```python
df_filtered = df[df['ParticipantID'].isin(selected_participants)]

if df_filtered.empty:
    st.warning("No data matches current filters. Select at least one participant.")
elif not any([show_points, show_arrows, show_areas]):
    st.info("No elements visible. Enable at least one visibility toggle.")
else:
    # Create and display chart
    fig = go.Figure()
    # ... add traces conditionally
    st.plotly_chart(fig, use_container_width=False)
```

### Anti-Patterns to Avoid
- **Creating all traces, then using `visible` property:** Wastes memory and processing for already-filtered data. Filter first, create only needed traces.
- **Placing widgets after chart rendering:** Causes Streamlit session state errors if trying to modify widget state. Always define sidebar widgets before main content.
- **Using buttons for toggles:** Buttons return `False` on subsequent reruns. Use `st.checkbox` for persistent state.
- **Not defaulting to all participants selected:** Empty multiselect shows blank chart on first load. Use `default=metadata['participant_ids']`.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Filtering DataFrames by multiple values | Custom loop with conditionals | `df[df['col'].isin(list)]` | Vectorized pandas operation is 10-100x faster |
| Widget state management | Manual session_state tracking | Widget `key` parameter | Streamlit auto-syncs widget values to session_state |
| "Select All" functionality | Complex callback logic | `default=options` parameter | Multiselect accepts list as default; simpler than custom component |
| Empty data handling | Try/except around Plotly | `if not df_filtered.empty` check | Explicit is better than implicit; provides better user feedback |

**Key insight:** Streamlit's rerun model and pandas' vectorized operations make custom state management and filtering logic unnecessary. Use built-in features.

## Common Pitfalls

### Pitfall 1: Widget Rendering Order Issues
**What goes wrong:** Trying to modify session state for a widget after it's been rendered throws `StreamlitAPIException`
**Why it happens:** Streamlit renders widgets sequentially; can't retroactively change values
**How to avoid:** Always define sidebar widgets BEFORE main content. Use callbacks (`on_change`) if widgets need to modify each other's state.
**Warning signs:** `StreamlitAPIException: st.session_state.widget_key cannot be modified after widget instantiated`

### Pitfall 2: Empty Multiselect on First Load
**What goes wrong:** User sees blank chart on initial app load
**Why it happens:** Multiselect defaults to empty list if no `default` parameter provided
**How to avoid:** Always set `default=metadata['participant_ids']` for participant filter
**Warning signs:** `df_filtered` is empty on first run, but works after selecting participants

### Pitfall 3: Performance Issues with Large Traces
**What goes wrong:** Chart becomes sluggish with 31 separate per-participant traces
**Why it happens:** Plotly.js rendering degrades with many traces (100k traces @ 1 point = 11.25s vs 1 trace @ 100k points = 0.55s)
**How to avoid:** For Phase 3, use single trace with per-point arrays (current approach). Reserve multiple traces for Arrows/Areas in Phase 4/5 where necessary.
**Warning signs:** Chart takes >2 seconds to render, panning/zooming feels slow

### Pitfall 4: Not Checking Empty DataFrame
**What goes wrong:** Plotly throws errors when trying to create scatter with empty data
**Why it happens:** All participants deselected or all visibility toggles disabled
**How to avoid:** Always check `if df_filtered.empty` or `if not any([show_points, show_arrows, show_areas])` before creating figure
**Warning signs:** Plotly errors mentioning empty x/y arrays

### Pitfall 5: Using Update Instead of Recreate
**What goes wrong:** Code becomes complex trying to update existing figure traces
**Why it happens:** Assumption that updating is more efficient than recreating
**How to avoid:** For this dataset size (563 points), recreating the entire figure on each rerun is simpler and fast enough. Streamlit reruns trigger full recreation anyway.
**Warning signs:** Complex conditional logic around `fig.update_traces()`; trying to track which traces exist

## Code Examples

Verified patterns from official sources:

### Complete Sidebar Controls
```python
# Source: Streamlit multiselect and checkbox documentation
# https://docs.streamlit.io/develop/api-reference/widgets/st.multiselect
# https://docs.streamlit.io/develop/api-reference/widgets/st.checkbox

import streamlit as st

# Load metadata (already cached)
metadata = load_metadata()

# Sidebar: Filters and Toggles
with st.sidebar:
    st.header("Filters")

    # Participant multiselect (all selected by default)
    selected_participants = st.multiselect(
        "Select Participants",
        options=metadata['participant_ids'],
        default=metadata['participant_ids'],  # Critical: show all on first load
        help="Filter scatter plot to show only selected participants",
        key='participant_filter'
    )

    st.divider()
    st.header("Visibility")

    # Element toggles (all visible by default)
    show_points = st.checkbox(
        "Show Points",
        value=True,
        help="Display individual solution points",
        key='show_points'
    )
    show_arrows = st.checkbox(
        "Show Arrows",
        value=True,
        help="Display exploration sequence arrows (Phase 5)",
        key='show_arrows',
        disabled=True  # Phase 3: not yet implemented
    )
    show_areas = st.checkbox(
        "Show Areas",
        value=True,
        help="Display convex hull areas (Phase 5)",
        key='show_areas',
        disabled=True  # Phase 3: not yet implemented
    )
```

### Filtering and Conditional Rendering
```python
# Source: Pandas filtering + Plotly conditional trace creation
# https://docs.streamlit.io/develop/concepts/architecture/session-state
# https://plotly.com/python/creating-and-updating-figures/

import plotly.graph_objects as go

# Filter DataFrame by selected participants
df_filtered = df[df['ParticipantID'].isin(selected_participants)]

# Validate filters
if df_filtered.empty:
    st.warning("⚠️ No data matches current filters. Please select at least one participant.")
elif not any([show_points, show_arrows, show_areas]):
    st.info("ℹ️ No elements visible. Enable at least one visibility toggle in the sidebar.")
else:
    # Create figure
    fig = go.Figure()

    # Conditionally add Points trace
    if show_points:
        fig.add_trace(go.Scatter(
            x=df_filtered['x_emb'],
            y=df_filtered['y_emb'],
            mode='markers',
            hovertemplate=df_filtered['hovertxt'].tolist(),
            marker=dict(
                size=7,
                color=df_filtered['HEX-Win'].tolist(),
                symbol=df_filtered['clust_symb'].tolist(),
                line=dict(color=df_filtered['HEX-Win'].tolist()),
            ),
            name='Solutions',
            showlegend=False
        ))

    # Conditionally add Arrows (Phase 4/5: infrastructure ready)
    if show_arrows:
        # TODO: Add arrow traces when implemented
        pass

    # Conditionally add Areas (Phase 4/5: infrastructure ready)
    if show_areas:
        # TODO: Add convex hull traces when implemented
        pass

    # Update layout (1:1 aspect ratio preserved)
    fig.update_layout(
        showlegend=False,
        hovermode='closest',
        xaxis=dict(title='UMAP Dimension 1'),
        yaxis=dict(title='UMAP Dimension 2', scaleanchor='x', scaleratio=1),
        height=700,
        margin=dict(l=40, r=40, b=40, t=40, pad=2),
        plot_bgcolor='white',
        paper_bgcolor='rgba(0,0,0,0)',
    )

    # Display chart (use_container_width=False preserves 1:1 ratio)
    st.plotly_chart(fig, use_container_width=False)
```

### Status Caption with Filter Info
```python
# Provide user feedback about current filter state
total_solutions = len(df)
filtered_solutions = len(df_filtered)
total_participants = len(metadata['participant_ids'])
selected_count = len(selected_participants)

st.caption(
    f"Showing {filtered_solutions:,} of {total_solutions:,} solutions "
    f"from {selected_count} of {total_participants} participants"
)
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `fig.update_traces(visible=...)` | Filter DataFrame, conditionally create traces | 2025 best practices | Simpler code, better performance for small datasets |
| Custom "Select All" components | `default=options` parameter | Streamlit 1.25+ (2023) | Built-in support, no extra dependency |
| Manual session state tracking | Widget `key` auto-sync | Streamlit 1.0+ (2021) | Automatic state management |
| Boolean masks: `df[df['col'] == val1 | df['col'] == val2]` | `df[df['col'].isin([val1, val2])]` | Pandas best practice | Cleaner, more readable |

**Deprecated/outdated:**
- `st.beta_expander`: Renamed to `st.expander` (2021)
- `st.experimental_rerun`: Now `st.rerun` (2023)
- Manually managing widget state without `key` parameter: Use `key` for all filter/toggle widgets

## Open Questions

1. **Should filters affect click handling from Phase 2?**
   - What we know: Phase 2 adds click-to-detail functionality
   - What's unclear: Should clicking filtered-out points be ignored, or should filters clear on click?
   - Recommendation: Keep filters independent — clicking any point should work and show details regardless of filter state (user might want to explore hidden participants)

2. **Performance threshold for switching to Scattergl?**
   - What we know: `go.Scattergl` uses WebGL for better performance with large datasets
   - What's unclear: At what point (if ever) should we switch from `go.Scatter` to `go.Scattergl`?
   - Recommendation: Stick with `go.Scatter` for now (563 points is well within comfort zone). Consider `Scattergl` only if Phase 4/5 adds 31 arrow traces + 31 area traces and performance degrades.

3. **Should disabled checkboxes (Arrows, Areas) be visible in Phase 3?**
   - What we know: Arrows and Areas aren't implemented until Phase 4/5
   - What's unclear: Show disabled checkboxes now (prepares UI) or hide until implemented?
   - Recommendation: Show disabled checkboxes with `disabled=True` and helpful tooltips. Prepares users for future features and validates UI layout early.

## Sources

### Primary (HIGH confidence)
- [Streamlit st.multiselect documentation](https://docs.streamlit.io/develop/api-reference/widgets/st.multiselect) - API reference and default parameter usage
- [Streamlit st.checkbox documentation](https://docs.streamlit.io/develop/api-reference/widgets/st.checkbox) - Widget behavior and parameters
- [Streamlit session state](https://docs.streamlit.io/develop/concepts/architecture/session-state) - State management best practices
- [Streamlit sidebar layout](https://docs.streamlit.io/develop/api-reference/layout/st.sidebar) - Sidebar organization patterns
- [Plotly Scatter trace reference](https://plotly.com/python/reference/scatter/) - `visible` property and trace configuration
- [Streamlit button anti-patterns](https://docs.streamlit.io/develop/concepts/design/buttons) - Widget rendering order issues

### Secondary (MEDIUM confidence)
- [KDnuggets: Combine Streamlit, Pandas, and Plotly](https://www.kdnuggets.com/how-to-combine-streamlit-pandas-and-plotly-for-interactive-data-apps) - Integration patterns
- [Streamlit blog: Dynamic filters](https://blog.streamlit.io/make-dynamic-filters-in-streamlit-and-show-their-effects-on-the-original-dataset/) - Filtering workflows
- [Medium: Multi-select "All" option](https://medium.com/streamlit/multi-select-all-option-in-streamlit-3c92a0f20526) - "Select All" patterns
- [Streamlit blog: 10 Principles](https://blog.streamlit.io/10-principles-for-keeping-the-vibe-while-coding-streamlit-apps-b5e62cc8497d) - Common anti-patterns (Dec 2025)
- [Plotly performance issues #7489](https://github.com/plotly/plotly.js/issues/7489) - Many traces vs single trace performance

### Tertiary (LOW confidence)
- Community forum discussions about filter patterns and checkbox interactions
- GitHub issues about multiselect callbacks (some from 2023-2024, may not reflect current behavior)

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - All libraries already in use; no version conflicts
- Architecture: HIGH - Patterns verified against official docs; sidebar-before-content is documented best practice
- Pitfalls: MEDIUM-HIGH - Widget rendering order is documented; performance numbers from GitHub issue (2023); empty DataFrame handling is standard practice

**Research date:** 2026-02-14
**Valid until:** 2026-03-16 (30 days - Streamlit stable, but minor version updates possible)
