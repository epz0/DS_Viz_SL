# Features Research: Dash-to-Streamlit Migration

## Executive Summary

This document maps the interactive features of the Dash application to their Streamlit equivalents. The Dash app is a complex data visualization tool with bidirectional chart interactions, dynamic filtering, and efficient partial updates using Dash's `Patch()` mechanism.

**Key Challenge**: Streamlit uses a fundamentally different execution model (top-to-bottom rerun on every interaction) compared to Dash's callback-based reactive system. This affects how state management, cross-chart syncing, and partial updates are implemented.

---

## Direct Equivalents (Table Stakes)

These features map cleanly from Dash to Streamlit with minimal changes:

### 1. Basic UI Components

| Dash Component | Streamlit Equivalent | Notes |
|---------------|---------------------|-------|
| `dcc.Checklist` | `st.multiselect` or multiple `st.checkbox` | `st.multiselect(['Points', 'Arrows', 'Areas'], default=['Points', 'Arrows', 'Areas'])` |
| `dcc.Dropdown` (multi=True) | `st.multiselect` | Direct 1:1 mapping |
| `dcc.Dropdown` (single) | `st.selectbox` | Direct 1:1 mapping |
| `html.Label` (static text) | `st.write()` or `st.text()` | Simple text output |
| `html.Label` (dynamic data) | `st.metric()` or `st.write()` | For displaying values |
| `html.Div` | `st.container()` or column layout | Streamlit has different layout approach |
| `html.Img(src=url)` | `st.image(url)` | Both support external URLs |
| `html.H3`, `html.H5`, `html.H6` | `st.header()`, `st.subheader()`, markdown | Use appropriate hierarchy |
| `html.Br()` | `st.write("")` or `st.markdown("<br>", unsafe_allow_html=True)` | Whitespace |

### 2. Plotly Charts

| Feature | Dash | Streamlit | Notes |
|---------|------|-----------|-------|
| Display Plotly figure | `dcc.Graph(figure=fig)` | `st.plotly_chart(fig, use_container_width=True)` | Direct support |
| Initial rendering | Same | Same | Both use plotly.graph_objects |
| Chart size | `autosize=False, width=725, height=650` | `use_container_width=True` or `config={'responsive': True}` | Streamlit prefers responsive |

### 3. External Resources

| Feature | Dash | Streamlit | Notes |
|---------|------|-----------|-------|
| External URLs in images | `html.Img(src='https://...')` | `st.image('https://...')` | Both support GitHub raw URLs |
| External links | `html.A('text', href='...')` | `st.markdown('[text](url)')` | Markdown syntax |
| External CSS | `external_stylesheets` parameter | Custom CSS via `st.markdown()` with `unsafe_allow_html=True` | More limited in Streamlit |

---

## Workarounds Needed

Features that work differently in Streamlit and require architectural changes:

### 1. Callback System → Session State + Rerun Model

**Dash Approach:**
```python
@callback(
    Output('image-src-id', 'src'),
    Input('main-ds-viz', 'clickData'),
    Input('performance-graph', 'clickData'),
    prevent_initial_call=True
)
def update_solution_screenshot(clickData_m, clickData_p):
    last_click = ctx.triggered_id
    # Process click and return new value
    return image_link
```

**Streamlit Equivalent:**
```python
# Initialize session state
if 'clicked_solution' not in st.session_state:
    st.session_state.clicked_solution = None

# Get click events (using streamlit-plotly-events)
selected_main = plotly_events(fig_DS, key="main_chart")
selected_perf = plotly_events(fig_PF, key="perf_chart")

# Update session state based on clicks
if selected_main:
    st.session_state.clicked_solution = selected_main[0]['pointIndex']
    st.session_state.last_click = 'main_chart'
elif selected_perf:
    # Map performance chart click to solution
    st.session_state.clicked_solution = calculate_solution_index(selected_perf)
    st.session_state.last_click = 'perf_chart'

# Use session state to display image
if st.session_state.clicked_solution is not None:
    image_link = df_base.loc[st.session_state.clicked_solution, 'videoPreview']
    st.image(image_link)
```

**Key Differences:**
- Dash: Explicit Input/Output declarations, callbacks fire on changes
- Streamlit: Manual state management, entire script reruns on interaction
- Dash: `ctx.triggered_id` tells you which input fired
- Streamlit: Need separate keys for each interactive component to track source

### 2. Click Data Extraction

**Dash:**
```python
clickedSol = clickData_m['points'][0]['pointIndex']
x_perf = clickData_p['points'][0]['x']
pat_id = ids[clickData_p['points'][0]['curveNumber']+1]
```

**Streamlit (via streamlit-plotly-events):**
```python
from streamlit_plotly_events import plotly_events

selected = plotly_events(fig, key="unique_key")
# Returns: [{'x': value, 'y': value, 'curveNumber': N, 'pointNumber': N, 'pointIndex': N}]

if selected:
    clicked_sol = selected[0]['pointIndex']
    curve_num = selected[0]['curveNumber']
```

**Installation required:**
```bash
pip install streamlit-plotly-events
```

### 3. Cross-Chart Syncing (Click one, update another)

**Dash Pattern:**
- Single callback can have multiple Inputs and Outputs
- `ctx.triggered_id` identifies which input triggered the callback
- Separate callbacks update different components based on same inputs

**Streamlit Pattern:**
```python
# Use session state to coordinate between charts
if 'selected_solution' not in st.session_state:
    st.session_state.selected_solution = None
    st.session_state.selected_participant = None

# Main scatter plot
col1, col2 = st.columns([1, 1])

with col1:
    # Create highlighted figure based on session state
    fig_DS_highlighted = create_highlighted_scatter(
        fig_DS,
        st.session_state.selected_solution
    )
    selected_main = plotly_events(fig_DS_highlighted, key="main")

    if selected_main:
        st.session_state.selected_solution = selected_main[0]['pointIndex']
        st.rerun()  # Force immediate update

with col2:
    # Performance chart uses session state to highlight
    fig_PF_highlighted = create_highlighted_performance(
        fig_PF,
        st.session_state.selected_solution
    )
    selected_perf = plotly_events(fig_PF_highlighted, key="perf")

    if selected_perf:
        # Map performance click to solution
        st.session_state.selected_solution = map_perf_to_solution(selected_perf)
        st.rerun()
```

**Critical Notes:**
- Must call `st.rerun()` to immediately reflect changes across charts
- Each plotly_events needs unique `key` parameter
- Charts must be regenerated with highlighting on each rerun
- Order matters: create figures before calling plotly_events

### 4. Filtering (Checklist + Dropdown)

**Dash Pattern:**
```python
@callback(
    Output('main-ds-viz', 'figure'),
    Input('show-element-type', 'value'),  # Checklist
    Input('show-participant', 'value'),   # Dropdown
    State('main-ds-viz', 'figure'),
)
def update_main_graph(ckb_value, pt_selec, fig_state):
    patched_figure = Patch()
    # Modify trace visibility
    patched_figure['data'][tr]['visible'] = True / 'legendonly'
    return patched_figure
```

**Streamlit Pattern:**
```python
# Filters in sidebar or top of page
show_elements = st.multiselect(
    'Show:',
    ['Points', 'Arrows', 'Areas'],
    default=['Points', 'Arrows', 'Areas']
)

selected_participants = st.multiselect(
    'Participants:',
    ids,
    default=[]
)

# Recreate figure with filtered traces
fig_DS = create_main_scatter(
    df_base,
    show_points='Points' in show_elements,
    show_arrows='Arrows' in show_elements,
    show_areas='Areas' in show_elements,
    participant_filter=selected_participants
)

st.plotly_chart(fig_DS, use_container_width=True)
```

**Key Differences:**
- Dash: Modify existing figure via Patch()
- Streamlit: Recreate figure each time with filters applied
- Streamlit is less efficient but simpler code

---

## Known Limitations

Features that won't work the same way or have significant constraints:

### 1. Partial Figure Updates (Dash Patch() → Full Regeneration)

**The Problem:**
Dash's `Patch()` allows surgical updates to figure properties without sending entire figure:
```python
patched_figure = Patch()
patched_figure['data'][62]['marker']['size'] = updated_size  # Only update marker size
patched_figure['data'][62]['marker']['symbol'] = updated_type
return patched_figure
```

**Streamlit Reality:**
- Streamlit has no equivalent to Dash's `Patch()`
- Must regenerate entire figure on every update
- For 63 traces (1 hull + 31 participant hulls + 30 arrows + 1 scatter), this is computationally expensive

**Impact on Your App:**
- Main scatter has 63 traces → full regeneration on every click
- Performance chart has 30 traces → full regeneration on every click
- Potential performance degradation, especially with large datasets
- Network overhead from sending full figure JSON

**Mitigation Strategies:**
```python
# Strategy 1: Cache figure generation
@st.cache_data
def create_base_figure(df_hash):
    # Create base figure (expensive operation)
    return fig

# Strategy 2: Only update what changed
def update_highlight(fig, clicked_solution):
    # Modify figure in place (still sent in full)
    fig.data[-1].marker.size = [18 if i == clicked_solution else 8
                                 for i in range(len(df_base))]
    return fig

# Strategy 3: Use Plotly's relayout/restyle via custom component
# (Advanced - requires custom Streamlit component)
```

### 2. Immediate Multi-Output Updates

**Dash:**
```python
@callback(
    Output('participant-id', 'children'),
    Output('group-id', 'children'),
    Output('intervention-id', 'children'),
    Output('solution-id', 'children'),
    Output('result-id', 'children'),
    Output('cost-id', 'children'),
    Output('max-stress-id', 'children'),
    Input('main-ds-viz', 'clickData'),
)
def update_participantinfo(clickData_m):
    # Single callback updates 7 elements simultaneously
    return pt_id, gp_id, int_id, sol, res, cost, mst
```

**Streamlit:**
```python
# All updates happen in sequence during rerun
if st.session_state.clicked_solution is not None:
    sol_data = df_base.loc[st.session_state.clicked_solution]

    col1, col2, col3 = st.columns(3)
    with col1:
        st.write(f"Participant: {sol_data['OriginalID_PT']}")
    with col2:
        st.write(f"Group: {sol_data['OriginalID_Group']}")
    with col3:
        st.write(f"{sol_data['OriginalID_PrePost']} intervention")

    st.metric("Solution", sol_data['OriginalID_Sol'])
    # ... etc for all 7 outputs
```

**Difference:**
- Dash: Single callback, clear input→output mapping
- Streamlit: Sequential code execution, no explicit mapping
- Streamlit actually simpler to read but less explicit about dependencies

### 3. Performance with Complex Interactions

**Dash:**
- Callbacks only fire when inputs change
- `prevent_initial_call=True` prevents unnecessary execution
- Multiple callbacks can run in parallel
- Network traffic optimized (only changed data sent)

**Streamlit:**
- Entire script reruns on any interaction
- Can use `@st.cache_data` and `@st.cache_resource` to optimize
- Sequential execution (no parallel callbacks)
- Full figure serialization on every update

**Performance Implications for Your App:**
- 63-trace scatter + 30-trace performance chart = ~93 traces to serialize
- Each click triggers full app rerun + figure regeneration
- Expected: Noticeable lag (0.5-2s depending on data size)
- Dash app is likely faster for these complex interactions

### 4. Layout Flexibility

**Dash:**
```python
html.Div([...], style={'width': '49%', 'float': 'left'})
```
- Pixel-perfect control via CSS
- Complex nested layouts with inline styles
- Full HTML/CSS capability

**Streamlit:**
```python
col1, col2 = st.columns([1, 1])
```
- Limited to columns, containers, expanders, tabs
- Less control over exact positioning
- Cannot do exact 49%/49% split with gaps easily
- Mobile-responsive by default (can be pro or con)

**Your App Layout Challenges:**
- Dash: Two-panel (49%/49%) layout with multiple nested divs
- Streamlit: Best approach is `st.columns([1, 1])` but not identical
- Fine-grained positioning (text alignment, margins) harder in Streamlit

### 5. State Management Between Interactions

**Dash:**
- `State` parameter for read-only access to component values
- `ctx.triggered_id` to identify trigger source
- Clear dependency graph

**Streamlit:**
- Must manually manage `st.session_state`
- Easy to create state bugs (forgetting to initialize)
- No built-in way to know which widget triggered rerun (need separate keys)

---

## Migration Patterns

Common patterns for each feature type:

### Pattern 1: Single Chart with Click Handling

**Dash:**
```python
@callback(
    Output('image-src-id', 'src'),
    Input('main-ds-viz', 'clickData'),
)
def update_image(clickData):
    idx = clickData['points'][0]['pointIndex']
    return df.loc[idx, 'image_url']
```

**Streamlit:**
```python
from streamlit_plotly_events import plotly_events

# Display chart and capture clicks
selected = plotly_events(fig, key="main_chart")

# Handle click
if selected:
    idx = selected[0]['pointIndex']
    st.image(df.loc[idx, 'image_url'])
else:
    st.info("Click a point to see its image")
```

### Pattern 2: Multiple Inputs, Single Output (Filter Pattern)

**Dash:**
```python
@callback(
    Output('graph', 'figure'),
    Input('checklist', 'value'),
    Input('dropdown', 'value'),
)
def update_graph(checked_items, selected_participant):
    # Filter and update
    return filtered_figure
```

**Streamlit:**
```python
# Get filter values (triggers rerun automatically)
checked_items = st.multiselect('Show:', options)
selected_participant = st.selectbox('Participant:', participants)

# Create filtered figure
fig = create_filtered_figure(
    df,
    show_items=checked_items,
    participant=selected_participant
)

st.plotly_chart(fig)
```

### Pattern 3: Cross-Chart Interaction (Click one, update both)

**Dash:**
```python
@callback(
    Output('chart1', 'figure'),
    Output('chart2', 'figure'),
    Input('chart1', 'clickData'),
    Input('chart2', 'clickData'),
    State('chart1', 'figure'),
    State('chart2', 'figure'),
)
def sync_charts(click1, click2, fig1_state, fig2_state):
    trigger = ctx.triggered_id

    if trigger == 'chart1':
        # Update both charts based on chart1 click
        return updated_fig1, updated_fig2
    else:
        # Update both charts based on chart2 click
        return updated_fig1, updated_fig2
```

**Streamlit:**
```python
# Initialize state
if 'selected_idx' not in st.session_state:
    st.session_state.selected_idx = None

col1, col2 = st.columns(2)

with col1:
    # Chart 1 with highlighting
    fig1 = create_chart1(df, highlight=st.session_state.selected_idx)
    click1 = plotly_events(fig1, key="chart1")

    if click1:
        st.session_state.selected_idx = click1[0]['pointIndex']
        st.rerun()  # Trigger immediate update

with col2:
    # Chart 2 with highlighting
    fig2 = create_chart2(df, highlight=st.session_state.selected_idx)
    click2 = plotly_events(fig2, key="chart2")

    if click2:
        st.session_state.selected_idx = map_chart2_to_index(click2)
        st.rerun()  # Trigger immediate update
```

**Critical:** Must call `st.rerun()` after state change for immediate cross-chart updates.

### Pattern 4: Dynamic Text Updates

**Dash:**
```python
@callback(
    Output('participant-id', 'children'),
    Output('result-id', 'children'),
    Output('cost-id', 'children'),
    Input('chart', 'clickData'),
)
def update_labels(clickData):
    idx = clickData['points'][0]['pointIndex']
    return df.loc[idx, 'participant'], df.loc[idx, 'result'], df.loc[idx, 'cost']
```

**Streamlit:**
```python
# Using metrics (recommended for numeric data)
if st.session_state.selected_idx is not None:
    row = df.loc[st.session_state.selected_idx]

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Participant", row['participant'])
    with col2:
        st.metric("Result", row['result'])
    with col3:
        st.metric("Cost", f"${row['cost']:,.2f}")

# Or using simple text
st.write(f"**Participant:** {row['participant']}")
st.write(f"**Result:** {row['result']}")
st.write(f"**Cost:** ${row['cost']:,.2f}")
```

### Pattern 5: Conditional Visibility (Show/Hide Traces)

**Dash:**
```python
@callback(
    Output('graph', 'figure'),
    Input('checklist', 'value'),
    State('graph', 'figure'),
)
def toggle_visibility(checked_items, fig_state):
    patched_figure = Patch()

    # Toggle trace visibility
    patched_figure['data'][1]['visible'] = 'Points' in checked_items
    patched_figure['data'][2]['visible'] = 'Arrows' in checked_items
    patched_figure['data'][3]['visible'] = 'Areas' in checked_items

    return patched_figure
```

**Streamlit:**
```python
# Option 1: Recreate figure with conditional traces
checked_items = st.multiselect('Show:', ['Points', 'Arrows', 'Areas'])

fig = go.Figure()

if 'Points' in checked_items:
    fig.add_trace(scatter_trace)
if 'Arrows' in checked_items:
    fig.add_trace(arrow_trace)
if 'Areas' in checked_items:
    fig.add_trace(area_trace)

# Option 2: Create full figure, modify visibility
fig = create_full_figure(df)

# Set visibility based on checklist
fig.data[0].visible = 'Points' in checked_items
fig.data[1].visible = 'Arrows' in checked_items
fig.data[2].visible = 'Areas' in checked_items

st.plotly_chart(fig)
```

### Pattern 6: Performance Chart Participant Filtering

**Dash Pattern (from your app):**
```python
# Show all 30 traces, toggle visibility
for tr in range(30):
    patched_figure['data'][tr]['visible'] = 'legendonly'

patched_figure['data'][pat_id_n]['visible'] = True
```

**Streamlit Pattern:**
```python
# Option 1: Conditionally add only visible traces
fig_PF = go.Figure()

if st.session_state.selected_participant:
    # Add only selected participant's trace
    trace_data = df[df['OriginalID_PT'] == st.session_state.selected_participant]
    fig_PF.add_trace(create_performance_trace(trace_data))
else:
    # Add all traces
    for pt in participants:
        trace_data = df[df['OriginalID_PT'] == pt]
        fig_PF.add_trace(create_performance_trace(trace_data))

# Option 2: Add all traces, set visibility
fig_PF = create_all_performance_traces(df)

for i, trace in enumerate(fig_PF.data):
    if st.session_state.selected_participant:
        trace.visible = (trace.name == st.session_state.selected_participant)
    else:
        trace.visible = True
```

---

## Complexity Assessment

### Easy to Port (Low Risk)

**Component-Level Features:**
- ✅ Dropdowns → `st.selectbox` / `st.multiselect`
- ✅ Checklists → `st.multiselect` or individual `st.checkbox`
- ✅ Static text labels → `st.write()` / `st.markdown()`
- ✅ External images → `st.image(url)`
- ✅ External links → `st.markdown('[text](url)')`
- ✅ Basic plotly charts → `st.plotly_chart(fig)`

**Estimated effort:** 1-2 hours

### Medium Complexity (Moderate Risk)

**State Management & Single Chart Interactions:**
- ⚠️ Single chart click handling → `plotly_events` + session_state
- ⚠️ Dynamic text updates → session_state + conditional rendering
- ⚠️ Filter logic (checklist + dropdown) → recreate figures with filters
- ⚠️ Solution detail panel updates → session_state + data lookups
- ⚠️ Image carousel/switching → session_state + st.image()

**Challenges:**
- Need to learn `streamlit-plotly-events` library
- Manual session_state management for all interactive elements
- Must initialize all state variables properly

**Estimated effort:** 4-8 hours

### Hard to Port (High Risk)

**Cross-Chart Synchronization & Performance:**
- ❌ Bidirectional chart syncing (click chart1 → update chart2, vice versa)
- ❌ Efficient partial updates (Dash Patch() → full regeneration)
- ❌ Complex multi-callback coordination
- ❌ 63-trace scatter plot updates without lag
- ❌ Preserving exact layout (49%/49% split with nested divs)
- ❌ Performance optimization for large datasets

**Challenges:**
- No Patch() equivalent → must regenerate all 63 traces on every click
- Cross-chart updates require `st.rerun()` → full app reload
- Potential 0.5-2s lag on each interaction
- Layout system fundamentally different (columns vs CSS)
- May need custom Streamlit components for advanced features

**Estimated effort:** 12-20 hours

**Risk factors:**
- Performance may be noticeably slower than Dash
- User experience may feel less responsive
- Some layout nuances impossible to replicate exactly

---

## Recommended Migration Approach

### Phase 1: Core Structure (Easy)
1. Set up basic Streamlit app structure
2. Migrate UI components (dropdowns, checklists, text labels)
3. Display static plotly figures (no interactivity)
4. Test layout with `st.columns()` and `st.container()`

### Phase 2: Single-Chart Interactions (Medium)
1. Install and test `streamlit-plotly-events`
2. Implement main scatter plot click handling
3. Add session_state for selected solution
4. Update solution detail panel on click
5. Update screenshot on click

### Phase 3: Filters & Conditional Rendering (Medium)
1. Implement Points/Arrows/Areas visibility toggle
2. Implement participant dropdown filter
3. Regenerate figures based on filter state

### Phase 4: Cross-Chart Syncing (Hard)
1. Implement performance chart click handling
2. Sync main scatter ↔ performance chart clicks
3. Coordinate state between both charts
4. Add `st.rerun()` for immediate updates

### Phase 5: Optimization (Hard)
1. Profile performance bottlenecks
2. Add `@st.cache_data` for expensive operations
3. Optimize figure generation
4. Consider custom components if needed

---

## Alternative: Hybrid Approach

If Streamlit performance is insufficient, consider:

1. **Keep Dash for complex visualization page**
   - Use Streamlit for data prep, analysis, reports
   - Use Dash for interactive exploration dashboard
   - Link between apps

2. **Use Plotly Dash + Streamlit components**
   - Embed Dash app in Streamlit via iframe
   - Use Streamlit for everything else

3. **Build custom Streamlit component**
   - Wrap Dash callback system in Streamlit component
   - Best of both worlds (more complex development)

---

## Dependencies & Installation

```bash
# Core Streamlit
pip install streamlit

# For Plotly click events (CRITICAL for this migration)
pip install streamlit-plotly-events

# Existing dependencies (should already have)
pip install plotly pandas numpy scipy shapely
```

**streamlit-plotly-events Documentation:**
- GitHub: https://github.com/null-jones/streamlit-plotly-events
- Returns click data in format similar to Dash clickData
- Supports multiple simultaneous charts with unique keys
- Known issue: Can cause full page rerun (by design)

---

## Key Takeaways

### Streamlit Advantages
- ✅ Simpler mental model (top-to-bottom execution)
- ✅ Less boilerplate code
- ✅ Faster initial development
- ✅ Better for rapid prototyping
- ✅ Built-in state management (session_state)
- ✅ Better documentation and community

### Streamlit Disadvantages for This Use Case
- ❌ No partial figure updates (Patch equivalent)
- ❌ Full app rerun on every interaction
- ❌ Less efficient for complex multi-chart apps
- ❌ Limited layout control vs custom CSS
- ❌ Potential performance issues with 63-trace charts
- ❌ Must use external library (streamlit-plotly-events) for clicks

### Bottom Line
**Migration is feasible but expect:**
- 20-30 hours total development time
- Performance degradation (0.5-2s lag on interactions)
- Some layout compromises
- Need for creative solutions to match Dash's efficiency

**The migration makes sense if:**
- You value Streamlit's ecosystem and deployment options
- You're willing to accept some performance trade-offs
- You want simpler long-term maintenance
- You plan to add more Streamlit-native features (auth, data upload, etc.)

**Stick with Dash if:**
- Performance is critical (sub-100ms interactions)
- You need pixel-perfect layout control
- The app is stable and working well
- You don't need Streamlit-specific features
