# Phase 4: Performance Chart & Cross-Chart Sync - Research

**Researched:** 2026-02-14
**Domain:** Dual-chart bidirectional synchronization with Streamlit and streamlit-plotly-events
**Confidence:** HIGH

## Summary

Phase 4 adds a second plotly chart (performance chart) and implements bidirectional click synchronization between the scatter plot and performance chart. The primary technical challenge is managing state when clicks originate from two different streamlit-plotly-events components.

The existing Phase 2 implementation already demonstrates the core pattern: `plotly_events()` returns click data, session state stores the selection, and `st.rerun()` rebuilds both figures with updated highlighting. The performance chart follows the same architecture as the original Dash app: one `go.Scatter` trace per participant (30 traces for P_001-P_030, excluding GALL), all with `mode='lines+markers'`. When a scatter point is clicked, the performance chart isolates the clicked participant's trace and highlights the clicked solution using per-point marker arrays (size, line width). When a performance chart point is clicked, the corresponding scatter point gets highlighted.

The key architectural decision is **how to determine which chart was clicked**. `streamlit-plotly-events` provides no built-in mechanism to identify the source chart. The solution is to compare the returned click data from both charts: whichever component returns a non-empty list was the one clicked. This comparison happens before the rerun, allowing us to set a `last_clicked_chart` session state variable that determines which chart's selection takes precedence.

**Primary recommendation:** Use session state variables `selected_point_idx` (existing), `selected_participant`, and `last_clicked_chart` to coordinate state. Build both figures on every render using session state values. Determine click source by checking which `plotly_events()` call returns non-empty data.

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| streamlit-plotly-events | >=0.0.6 | Click event handling | Only viable option for plotly click events in Streamlit (already in use from Phase 2) |
| plotly | Latest | Chart creation | Graph Objects API for full control over traces and markers (already in use) |
| streamlit | Latest | Web framework | Project foundation (already in use) |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| pandas | Latest | Data filtering | Filtering solutions by participant for performance traces |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| streamlit-plotly-events | Native st.plotly_chart on_select | Native support added in Streamlit 1.35+, but Phase 2 already uses streamlit-plotly-events and migration would break existing implementation |
| Multiple plotly_events calls | Single combined chart | Would lose semantic separation of scatter vs performance chart |

**Installation:**
Already installed in Phase 2. No new dependencies required.

## Architecture Patterns

### Recommended Session State Structure
```python
# Existing from Phase 2
if 'selected_point_idx' not in st.session_state:
    st.session_state.selected_point_idx = None

# New for Phase 4
if 'selected_participant' not in st.session_state:
    st.session_state.selected_participant = None

if 'last_clicked_chart' not in st.session_state:
    st.session_state.last_clicked_chart = None  # 'scatter' or 'performance'
```

### Pattern 1: Dual Chart Click Detection
**What:** Determine which chart was clicked by comparing non-empty click data
**When to use:** When you have multiple plotly_events components and need to know the click source
**Example:**
```python
# Call plotly_events for both charts
scatter_clicks = plotly_events(fig_scatter, click_event=True, key="scatter_chart", ...)
perf_clicks = plotly_events(fig_perf, click_event=True, key="perf_chart", ...)

# Determine which chart was clicked (non-empty list = that chart was clicked)
if scatter_clicks:
    # Process scatter click
    clicked_idx = scatter_clicks[0]['pointIndex']
    st.session_state.selected_point_idx = clicked_idx
    st.session_state.selected_participant = df.iloc[clicked_idx]['OriginalID_PT']
    st.session_state.last_clicked_chart = 'scatter'
    st.rerun()

elif perf_clicks:
    # Process performance chart click
    curve_num = perf_clicks[0]['curveNumber']  # Which participant trace (0-29)
    point_x = perf_clicks[0]['x']  # Solution number (1-based)

    # Map curveNumber to participant (matches Dash app logic)
    participant_ids = metadata['participant_ids'][1:31]  # Exclude GALL
    clicked_participant = participant_ids[curve_num]

    # Find the solution index in df_base
    solution_idx = df[(df['OriginalID_PT'] == clicked_participant) &
                      (df['OriginalID_Sol'] == point_x)].index[0]

    st.session_state.selected_point_idx = solution_idx
    st.session_state.selected_participant = clicked_participant
    st.session_state.last_clicked_chart = 'performance'
    st.rerun()
```

### Pattern 2: Performance Chart Construction
**What:** Build performance chart with one trace per participant, all initially visible
**When to use:** Initial chart creation matching original Dash app
**Example:**
```python
# Source: Original Dash app interactive_tool.py lines 338-381
fig_perf = go.Figure()

# Add vertical line at x=5.5 (intervention point, will be updated on click)
fig_perf.add_vline(x=5.5, line_width=2, line_dash="dash", line_color="darkgrey")

# Add one trace per participant (P_001 through P_030, skip GALL)
participant_ids = metadata['participant_ids'][1:31]  # Skip GALL at index 0

for pt_id in participant_ids:
    pt_data = df[df['OriginalID_PT'] == pt_id].sort_values('OriginalID_Sol')
    x_vals = list(range(1, len(pt_data) + 1))
    y_vals = pt_data['performance'].tolist()
    color = metadata['color_mapping'][pt_id]
    symbols = pt_data['clust_symb'].tolist()

    fig_perf.add_trace(go.Scatter(
        x=x_vals,
        y=y_vals,
        mode='lines+markers',
        name=pt_id,
        opacity=0.7,
        line=dict(color=color),
        marker=dict(
            size=7,  # Default size, updated per-point when selection happens
            color=color,
            symbol=symbols,  # Per-point symbols from cluster assignments
            line=dict(color=color)
        ),
    ))

# Add horizontal reference line at y=1 (performance baseline)
fig_perf.add_hline(y=1, line_width=2, line_dash="dot", line_color="black")

# Layout
fig_perf.update_layout(
    autosize=True,
    height=300,
    margin=dict(l=5, r=5, b=5, t=5, pad=2),
    xaxis=dict(tickmode='linear', dtick=1),
    showlegend=False,
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor='white'
)
```

### Pattern 3: Isolate Participant Trace on Selection
**What:** When scatter point clicked, hide all traces except selected participant's, update marker sizes
**When to use:** After scatter click to focus performance chart on clicked participant
**Example:**
```python
# After scatter click (selected_point_idx and selected_participant are set)
if st.session_state.selected_participant and st.session_state.selected_participant != 'GALL':
    participant_ids = metadata['participant_ids'][1:31]  # P_001 through P_030
    selected_trace_idx = participant_ids.index(st.session_state.selected_participant)

    # Update trace visibility (hide all except selected)
    for i, trace in enumerate(fig_perf.data):
        if i == selected_trace_idx:
            trace.visible = True
        else:
            trace.visible = 'legendonly'  # Plotly convention for hidden trace

    # Update intervention line position
    pt_data = df[df['OriginalID_PT'] == st.session_state.selected_participant]
    num_pre = len(pt_data[pt_data['OriginalID_PrePost'] == 'Pre'])
    intervention_x = num_pre + 0.5

    # Update vline position (first shape in layout.shapes)
    fig_perf.layout.shapes[0].x0 = intervention_x
    fig_perf.layout.shapes[0].x1 = intervention_x

    # Update marker sizes to highlight selected solution
    pt_data_sorted = pt_data.sort_values('OriginalID_Sol')
    selected_sol_num = df.iloc[st.session_state.selected_point_idx]['OriginalID_Sol']

    # Map solution number to index in sorted participant data (0-based)
    sol_index = int(selected_sol_num - 1)  # OriginalID_Sol is 1-based

    # Build per-point marker arrays
    num_solutions = len(pt_data_sorted)
    marker_sizes = [14 if i == sol_index else 8 for i in range(num_solutions)]
    marker_line_widths = [2 if i == sol_index else 0 for i in range(num_solutions)]

    # Update trace markers
    fig_perf.data[selected_trace_idx].marker.size = marker_sizes
    fig_perf.data[selected_trace_idx].marker.line.width = marker_line_widths
```

### Pattern 4: Three-Column Layout
**What:** Scatter chart | Performance chart | Detail panel
**When to use:** This phase adds performance chart, requiring layout restructure
**Example:**
```python
# Two columns: chart area (left) and detail panel (right)
col_charts, col_detail = st.columns([2, 1])

with col_charts:
    # Scatter plot (existing from Phase 2)
    scatter_clicks = plotly_events(
        fig_scatter,
        click_event=True,
        select_event=False,
        hover_event=False,
        override_height=700,
        override_width="100%",
    )

    # Spacer
    st.write("")

    # Performance chart (new in Phase 4)
    perf_clicks = plotly_events(
        fig_perf,
        click_event=True,
        select_event=False,
        hover_event=False,
        override_height=300,
        override_width="100%",
    )

with col_detail:
    # Existing detail panel from Phase 2 (unchanged)
    if st.session_state.selected_point_idx is not None:
        # ... detail panel content ...
```

### Anti-Patterns to Avoid
- **Don't use unique keys for plotly_events components:** The `key` parameter in `plotly_events()` is for component state management, not for identifying which chart was clicked. Use the pattern of checking which return value is non-empty instead.
- **Don't rebuild performance chart from scratch on every click:** Build it once per render with all traces, then update visibility and marker arrays based on session state.
- **Don't use trace index directly as participant index:** GALL is at index 0 in participant_ids but excluded from performance chart. Always use `participant_ids[1:31]` for the trace mapping.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Click event handling | Custom JavaScript component | streamlit-plotly-events | Already proven in Phase 2, handles all edge cases, maintained by community |
| Identifying click source | Polling or timers | Check non-empty return values | Streamlit's execution model makes this pattern reliable and simple |
| Trace visibility toggling | Rebuilding entire figure | Update trace.visible property | Plotly efficiently handles visibility without full rebuild |
| Participant-to-trace mapping | Manual index tracking | Build mapping from metadata | Single source of truth prevents off-by-one errors |

**Key insight:** The original Dash app uses `Patch()` to update only changed properties. Streamlit requires full figure rebuilds on every render, but this is not a performance issue because: (1) figures are lightweight JSON structures, (2) rendering happens client-side, (3) the bottleneck is the network round-trip from rerun, not figure construction.

## Common Pitfalls

### Pitfall 1: Off-by-One Errors in Performance Chart Mapping
**What goes wrong:** Performance chart x-axis is 1-based (solution 1, 2, 3...) but Python indices are 0-based. OriginalID_Sol is also 1-based. When highlighting a marker, using OriginalID_Sol directly as the index causes the wrong solution to be highlighted.

**Why it happens:** The original Dash app has this same complexity (see line 951: `selecSol = df_base.loc[clickedSol,'OriginalID_Sol']-1`). The performance chart x-values are `list(range(1, len(pt_data) + 1))` (1-based), but marker size arrays are built with 0-based indices.

**How to avoid:** Always subtract 1 when converting OriginalID_Sol to a marker array index. Document this conversion clearly.

**Warning signs:** Selected point highlight appears on the wrong marker in the performance chart. The highlighted solution number doesn't match the detail panel.

### Pitfall 2: GALL Participant Handling
**What goes wrong:** GALL is the first participant in the metadata (index 0) but is excluded from the performance chart (no trace for GALL). Clicking a GALL solution causes an IndexError when trying to find its trace.

**Why it happens:** The original Dash app explicitly checks `if pt_focus == 'GALL'` and hides all traces (lines 972-981). The performance chart only has 30 traces (P_001 through P_030), not 31.

**How to avoid:** When scatter point is clicked, check if `selected_participant == 'GALL'`. If so, hide all performance traces and move the intervention line to x=0 (matching Dash app behavior).

**Warning signs:** Clicking a GALL point (black marker) causes an error. Performance chart doesn't handle GALL gracefully.

### Pitfall 3: Stale Click Data After Rerun
**What goes wrong:** After `st.rerun()`, the script re-executes from top to bottom. The `plotly_events()` calls return empty lists on the first render after rerun, but the code expects click data.

**Why it happens:** `plotly_events()` only returns data when a NEW click happens. After rerun, there's no new click, so both return `[]`. If you don't check for this, you'll try to process empty click data.

**How to avoid:** Process click data ONLY if the returned list is non-empty. Use `if scatter_clicks:` not `if scatter_clicks is not None:`.

**Warning signs:** Clicking works once, then subsequent clicks do nothing. Error about indexing into empty list.

### Pitfall 4: curveNumber Doesn't Match Participant Order
**What goes wrong:** When clicking a performance chart point, `perf_clicks[0]['curveNumber']` returns the trace index (0-29), but mapping this directly to `metadata['participant_ids'][curveNumber]` gives the wrong participant because GALL is at index 0.

**Why it happens:** Performance chart has 30 traces (indices 0-29) corresponding to P_001 through P_030. But `metadata['participant_ids']` has 31 entries (GALL at 0, then P_001 through P_030). The mapping is offset by 1.

**How to avoid:** Use `participant_ids = metadata['participant_ids'][1:31]` (exclude GALL) to build the performance chart. Then `clicked_participant = participant_ids[curveNumber]` maps correctly.

**Warning signs:** Clicking P_001's trace in performance chart highlights P_002's solutions in scatter plot. Off-by-one in participant selection.

### Pitfall 5: Detail Panel Update Timing
**What goes wrong:** Click one chart, both charts update, but detail panel shows old data for a frame.

**Why it happens:** Detail panel reads from `st.session_state.selected_point_idx`, which is updated before `st.rerun()`. After rerun, the detail panel should show the new data. This shouldn't happen if state updates happen before rerun.

**How to avoid:** Always update ALL session state variables (selected_point_idx, selected_participant, last_clicked_chart) BEFORE calling `st.rerun()`. Ensure detail panel reads from session state, not from local variables.

**Warning signs:** Detail panel lags one click behind. Clicking solution A shows solution B's details.

## Code Examples

Verified patterns from original Dash app and streamlit-plotly-events usage:

### Building Performance Chart with All Traces
```python
# Source: Original Dash app interactive_tool.py lines 338-381
fig_perf = go.Figure()

# Vertical line for intervention point (updated on selection)
fig_perf.add_vline(x=5.5, line_width=2, line_dash="dash", line_color="darkgrey")

# One trace per participant (exclude GALL)
participant_ids = metadata['participant_ids'][1:31]  # P_001 through P_030

for pt_id in participant_ids:
    pt_data = df[df['OriginalID_PT'] == pt_id].sort_values('OriginalID_Sol')
    x_vals = list(range(1, len(pt_data) + 1))  # 1-based solution numbers
    y_vals = pt_data['performance'].tolist()
    color = metadata['color_mapping'][pt_id]
    symbols = pt_data['clust_symb'].tolist()  # Per-point symbols

    fig_perf.add_trace(go.Scatter(
        x=x_vals,
        y=y_vals,
        mode='lines+markers',
        name=pt_id,
        opacity=0.7,
        line=dict(color=color),
        marker=dict(
            size=7,
            color=color,
            symbol=symbols,
            line=dict(color=color, width=0)
        ),
    ))

# Horizontal reference line at performance = 1
fig_perf.add_hline(y=1, line_width=2, line_dash="dot", line_color="black")

fig_perf.update_layout(
    autosize=True,
    height=300,
    margin=dict(l=5, r=5, b=5, t=5, pad=2),
    xaxis=dict(tickmode='linear', dtick=1),
    showlegend=False,
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor='white'
)
```

### Detecting Which Chart Was Clicked
```python
# Two plotly_events calls (order matters - scatter first, then performance)
scatter_clicks = plotly_events(
    fig_scatter,
    click_event=True,
    select_event=False,
    hover_event=False,
    override_height=700,
    override_width="100%",
)

perf_clicks = plotly_events(
    fig_perf,
    click_event=True,
    select_event=False,
    hover_event=False,
    override_height=300,
    override_width="100%",
)

# Process clicks (only one will be non-empty)
if scatter_clicks:
    clicked_idx = scatter_clicks[0]['pointIndex']
    if clicked_idx != st.session_state.selected_point_idx:
        st.session_state.selected_point_idx = clicked_idx
        st.session_state.selected_participant = df.iloc[clicked_idx]['OriginalID_PT']
        st.session_state.last_clicked_chart = 'scatter'
        st.rerun()

elif perf_clicks:
    curve_num = perf_clicks[0]['curveNumber']
    point_x = perf_clicks[0]['x']

    participant_ids = metadata['participant_ids'][1:31]
    clicked_participant = participant_ids[curve_num]

    solution_idx = df[(df['OriginalID_PT'] == clicked_participant) &
                      (df['OriginalID_Sol'] == point_x)].index[0]

    if solution_idx != st.session_state.selected_point_idx:
        st.session_state.selected_point_idx = solution_idx
        st.session_state.selected_participant = clicked_participant
        st.session_state.last_clicked_chart = 'performance'
        st.rerun()
```

### Updating Performance Chart Based on Selection
```python
# After building fig_perf with all traces, apply selection-based updates
if st.session_state.selected_participant:
    if st.session_state.selected_participant == 'GALL':
        # Hide all traces (no performance chart for GALL)
        for trace in fig_perf.data:
            trace.visible = 'legendonly'
        # Move intervention line to x=0
        fig_perf.layout.shapes[0].x0 = 0
        fig_perf.layout.shapes[0].x1 = 0
    else:
        # Isolate selected participant's trace
        participant_ids = metadata['participant_ids'][1:31]
        selected_trace_idx = participant_ids.index(st.session_state.selected_participant)

        # Update trace visibility
        for i, trace in enumerate(fig_perf.data):
            trace.visible = True if i == selected_trace_idx else 'legendonly'

        # Update intervention line
        pt_data = df[df['OriginalID_PT'] == st.session_state.selected_participant]
        num_pre = len(pt_data[pt_data['OriginalID_PrePost'] == 'Pre'])
        intervention_x = num_pre + 0.5
        fig_perf.layout.shapes[0].x0 = intervention_x
        fig_perf.layout.shapes[0].x1 = intervention_x

        # Highlight selected solution
        selected_sol_num = df.iloc[st.session_state.selected_point_idx]['OriginalID_Sol']
        sol_index = int(selected_sol_num - 1)  # Convert 1-based to 0-based

        num_solutions = len(pt_data)
        marker_sizes = [14 if i == sol_index else 8 for i in range(num_solutions)]
        marker_line_widths = [2 if i == sol_index else 0 for i in range(num_solutions)]

        fig_perf.data[selected_trace_idx].marker.size = marker_sizes
        fig_perf.data[selected_trace_idx].marker.line.width = marker_line_widths
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Dash callbacks with ctx.triggered_id | Streamlit session state + rerun | Streamlit migration (2024-2026) | No built-in triggered_id equivalent, must infer from non-empty click data |
| Dash Patch() for partial updates | Full figure rebuild per render | Streamlit architecture | Negligible performance impact, simpler mental model |
| plotly_events 0.0.6 | Native st.plotly_chart on_select | Streamlit 1.35+ (2024) | Native support now exists but project already uses plotly_events from Phase 2 |

**Deprecated/outdated:**
- Using st.experimental_rerun(): Deprecated in Streamlit 1.27, replaced by st.rerun()
- Detecting trigger source via st.session_state._scriptrunner: Never officially supported, removed in later versions

## Open Questions

1. **Performance chart rendering performance with 30 traces**
   - What we know: Original Dash app renders 30 traces without issue. Plotly handles this efficiently.
   - What's unclear: Whether Streamlit Community Cloud will handle 30 traces + scatter plot updates smoothly.
   - Recommendation: Build the implementation as designed. If performance issues arise, consider hiding all traces by default and only showing on first click.

2. **Handling edge case where solution numbers aren't consecutive**
   - What we know: OriginalID_Sol appears to be consecutive integers (1, 2, 3...) per participant based on sample data.
   - What's unclear: Whether all participants have consecutive solution numbers without gaps.
   - Recommendation: Use `list(range(1, len(pt_data) + 1))` for x-values (generates consecutive integers regardless of actual OriginalID_Sol values). This matches original Dash app approach.

## Sources

### Primary (HIGH confidence)
- Original Dash app code (scripts/interactive_tool.py) - Lines 336-381 (performance chart creation), lines 920-1007 (update_performance_graph callback)
- Pre-computed data files (streamlit_app/data/df_base.parquet, metadata.json) - Verified performance column exists and participant mapping

### Secondary (MEDIUM confidence)
- [streamlit-plotly-events README](https://github.com/ethanhe42/streamlit-plotly-events/blob/master/README.md) - Click event return values and parameters
- [Plotly add_vline/add_hline documentation](https://plotly.com/python/horizontal-vertical-shapes/) - Reference line syntax
- [Plotly go.Scatter marker arrays](https://plotly.com/python/marker-style/) - Per-point symbol arrays
- [Streamlit Session State documentation](https://docs.streamlit.io/develop/concepts/architecture/session-state) - State management patterns

### Tertiary (LOW confidence - community patterns)
- [Streamlit discussion: Detecting which component triggered rerun](https://discuss.streamlit.io/t/is-it-possible-to-know-which-element-component-triggered-a-rerun/4757) - Pattern of checking non-empty return values
- [Streamlit discussion: Synchronizing plotly graphs](https://discuss.streamlit.io/t/synchronizing-plotly-graphs/104985) - General approach to multi-chart sync

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - streamlit-plotly-events already in use from Phase 2, no new dependencies
- Architecture: HIGH - Original Dash app provides complete reference implementation, patterns verified in existing code
- Pitfalls: HIGH - All identified from original Dash app code (off-by-one conversions, GALL handling, curveNumber mapping)

**Research date:** 2026-02-14
**Valid until:** 2026-03-14 (30 days - stable domain, plotly/streamlit APIs are mature)
