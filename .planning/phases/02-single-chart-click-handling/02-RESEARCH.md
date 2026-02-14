# Phase 02: Single-Chart Click Handling - Research

**Researched:** 2026-02-14
**Domain:** Streamlit interactive visualization with Plotly click events
**Confidence:** HIGH

## Summary

Phase 2 implements click interaction on the scatter plot to display detailed solution information and screenshots. The core technical challenge is capturing click events from Plotly charts in Streamlit and managing state to highlight the selected point while displaying corresponding details.

**Primary technical findings:**

1. **Two viable approaches for click handling:** `streamlit-plotly-events` (community component, click-specific) vs native `st.plotly_chart` with `on_select="rerun"` (official, selection-focused)
2. **Highlighting technique:** Use per-point marker arrays (size, line width) to visually distinguish selected points - Plotly supports arrays for all marker properties
3. **State management:** Use `st.session_state` to persist selected point across reruns, initialized with conditional checks
4. **Layout pattern:** Two-column layout (`st.columns`) is standard for chart + detail panel, with 2:1 or 3:2 ratio
5. **Image loading:** `st.image()` natively supports external URLs including GitHub raw content URLs, with try-except for graceful fallback

**Primary recommendation:** Use `streamlit-plotly-events` over native `on_select` because it provides true click events (not just selection events), matches the prior decision from Phase 1, and has proven compatibility with go.Scatter. Implement highlighting via per-point marker property arrays rather than creating separate traces.

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| streamlit-plotly-events | 0.0.6 | Click event capture from Plotly charts | Only viable option for true click events in Streamlit; native `on_select` only handles selection events |
| streamlit | >=1.30.0 | Web framework | Already in use (Phase 1) |
| plotly | >=5.23.0 | Visualization library | Already in use (Phase 1) |
| pandas | >=2.2.0 | Data manipulation | Already in use (Phase 1) |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| PIL/Pillow | (optional) | Image fallback rendering | If generating placeholder images locally; not needed for URL-based images |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| streamlit-plotly-events | Native `st.plotly_chart` with `on_select="rerun"` | Native approach only supports selection events (box/lasso/click all treated as selection), not true click events. Returns all selected points, not just clicked point. Introduced in Streamlit 1.35+, more future-proof but doesn't match UX requirement for single-point click. |
| Two-column layout | Sidebar (`st.sidebar`) | Sidebar persists across pages (not relevant for single-page app), takes up less horizontal space but detail panel needs substantial width for screenshot display |
| Expander for details | Always-visible panel | Expander hides content by default, requiring extra click; not ideal when click interaction already exists |

**Installation:**
```bash
pip install streamlit-plotly-events>=0.0.6
```

## Architecture Patterns

### Recommended Project Structure
```
streamlit_app/
├── streamlit_app.py       # Main app (existing)
├── data/                  # Pre-computed data (existing)
│   ├── df_base.parquet
│   ├── metadata.json
│   └── ...
└── .streamlit/
    └── config.toml        # Optional: CORS settings if needed
```

### Pattern 1: Click Event Capture with State Management
**What:** Capture click events from Plotly chart and store selected point index in session state
**When to use:** Any interactive Plotly chart in Streamlit requiring click handling
**Example:**
```python
# Source: https://github.com/ethanhe42/streamlit-plotly-events
from streamlit_plotly_events import plotly_events

# Initialize session state for selected point
if 'selected_point_idx' not in st.session_state:
    st.session_state.selected_point_idx = None

# Display chart and capture click events
selected_points = plotly_events(fig, click_event=True, select_event=False, hover_event=False)

# Update session state when point is clicked
if selected_points:
    # selected_points is a list of dicts with keys: x, y, curveNumber, pointNumber, pointIndex
    st.session_state.selected_point_idx = selected_points[0]['pointIndex']
```

### Pattern 2: Conditional Highlighting via Per-Point Marker Arrays
**What:** Dynamically build marker size and line width arrays based on selected point
**When to use:** Highlighting specific points in scatter plots without creating multiple traces
**Example:**
```python
# Build per-point marker arrays based on selection
default_size = 7
highlight_size = 12
default_line_width = 0
highlight_line_width = 2

# Create arrays for all points
marker_sizes = [highlight_size if i == st.session_state.selected_point_idx else default_size
                for i in range(len(df))]
marker_line_widths = [highlight_line_width if i == st.session_state.selected_point_idx else default_line_width
                      for i in range(len(df))]

# Apply to scatter trace
fig.add_trace(go.Scatter(
    x=df['x_emb'],
    y=df['y_emb'],
    mode='markers',
    marker=dict(
        size=marker_sizes,  # Per-point array
        color=df['HEX-Win'].tolist(),
        symbol=df['clust_symb'].tolist(),
        line=dict(
            color='black',  # Or per-point array if needed
            width=marker_line_widths  # Per-point array
        ),
    ),
    name='',
))
```

### Pattern 3: Two-Column Layout with Conditional Detail Display
**What:** Create side-by-side layout with chart on left and detail panel on right
**When to use:** Displaying primary visualization alongside contextual details
**Example:**
```python
# Source: https://docs.streamlit.io/develop/api-reference/layout
col1, col2 = st.columns([2, 1])  # 2:1 ratio - chart gets more space

with col1:
    # Chart with click handling
    selected_points = plotly_events(fig, click_event=True)
    if selected_points:
        st.session_state.selected_point_idx = selected_points[0]['pointIndex']

with col2:
    # Conditional detail panel
    if st.session_state.selected_point_idx is not None:
        idx = st.session_state.selected_point_idx
        row = df.iloc[idx]

        st.header("Solution Details")
        st.markdown(f"**Participant:** {row['ParticipantID']}")
        st.markdown(f"**Group:** {row['GroupID']}")
        # ... more details
    else:
        st.info("Click a point to view details")
```

### Pattern 4: External Image Loading with Graceful Fallback
**What:** Load images from external URLs with error handling for missing/failed images
**When to use:** Displaying images from GitHub or other external sources
**Example:**
```python
# Source: https://docs.streamlit.io/develop/api-reference/media/st.image
# No explicit try-except needed in Streamlit - st.image handles errors internally
# But validate URL format and provide fallback message

image_url = row['videoPreview']
if image_url and image_url != '-':
    try:
        st.image(image_url, caption=f"Solution {row['SolutionID']}", width=300)
    except Exception:
        st.warning("Screenshot unavailable")
else:
    st.warning("No screenshot available for this solution")
```

### Anti-Patterns to Avoid
- **Creating separate traces for highlighting:** Inefficient and complicates legend management. Use per-point marker arrays instead.
- **Using `on_select` for click-only interactions:** Native `on_select` treats all interactions (click, box, lasso) as selections, returning arrays. Use `streamlit-plotly-events` for true click events.
- **Accessing session state without initialization:** Always check `if 'key' not in st.session_state` before first use to avoid KeyError.
- **Using relative GitHub URLs:** Must use `raw.githubusercontent.com` format, not `github.com/.../blob/...` URLs.
- **Not handling empty click events:** `plotly_events` returns empty list when chart area (not point) is clicked; always check `if selected_points:`.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Plotly click event capture | Custom JavaScript component | `streamlit-plotly-events` | Handles iframe communication, event serialization, Streamlit rerun coordination; custom components require complex bidirectional communication |
| Session state management | Global variables or file-based state | `st.session_state` | Streamlit's native state persists across reruns per-user-session; globals don't survive reruns, files don't scale or isolate users |
| Layout containers | HTML/CSS grid system | `st.columns`, `st.container` | Streamlit handles responsive behavior and mobile layout automatically; custom HTML breaks on mobile |
| Image caching | Manual requests + file storage | `st.image(url)` | Streamlit's internal caching handles HTTP requests, CORS, and browser caching; manual approach requires managing cache invalidation |
| Markdown formatting | HTML string building | `st.markdown()` | Supports GitHub-flavored Markdown, handles escaping, maintains consistent styling with Streamlit theme |

**Key insight:** Streamlit's ecosystem has mature solutions for common interactive visualization patterns. Custom implementations rarely add value and often introduce compatibility issues with Streamlit's rerun model.

## Common Pitfalls

### Pitfall 1: Empty Chart When Using streamlit-plotly-events
**What goes wrong:** Chart renders as blank white area with axes but no data points
**Why it happens:** Version incompatibility between `streamlit-plotly-events` (last updated April 2021) and modern Streamlit versions (1.30+); component's iframe rendering can conflict with Streamlit's component lifecycle
**How to avoid:**
- Test with minimal example first before integrating into full app
- Ensure `fig` is valid Plotly object before passing to `plotly_events()`
- Check browser console for JavaScript errors
- If persistent, fall back to native `st.plotly_chart` with `on_select="rerun"` and adjust UX to handle selection events
**Warning signs:** White chart area, axes visible but no markers, no JavaScript console errors in browser dev tools

### Pitfall 2: Session State KeyError on First Run
**What goes wrong:** `KeyError: 'selected_point_idx'` on app load
**Why it happens:** Session state keys don't exist until explicitly created; accessing undefined key raises KeyError
**How to avoid:** Always initialize session state variables with conditional check at top of script:
```python
if 'selected_point_idx' not in st.session_state:
    st.session_state.selected_point_idx = None
```
**Warning signs:** Error on first page load but not on subsequent interactions, error message references session_state key

### Pitfall 3: Selected Point Persists Across Data Changes
**What goes wrong:** Highlighting stays on wrong point after filtering/updating dataset
**Why it happens:** Session state persists across reruns; `selected_point_idx` refers to DataFrame index which shifts when data changes
**How to avoid:**
- Store unique identifier (e.g., `SolutionID`) instead of index
- Reset selection when data changes: `st.session_state.selected_point_idx = None`
- Use `df.reset_index(drop=True)` to ensure index alignment
**Warning signs:** Highlight appears on wrong point after filtering, clicking point shows different point's details

### Pitfall 4: GitHub Image URLs Fail to Load
**What goes wrong:** Images don't display, blank space or error icon shown
**Why it happens:** Using `github.com/.../blob/...` URL format instead of `raw.githubusercontent.com`; CORS restrictions from GitHub
**How to avoid:**
- Convert URLs to raw format: `https://raw.githubusercontent.com/user/repo/branch/path/image.png`
- Validate URL format in data preprocessing (Phase 0)
- Implement graceful fallback with try-except or conditional check
**Warning signs:** Images work in browser direct navigation but not in Streamlit, CORS errors in browser console

### Pitfall 5: Chart Reruns on Every Interaction, Losing Zoom State
**What goes wrong:** User zooms in on chart, clicks point, zoom resets to default
**Why it happens:** `plotly_events()` triggers Streamlit rerun, which rebuilds entire figure from scratch
**How to avoid:**
- Not easily solvable with `streamlit-plotly-events` due to Streamlit's rerun model
- Consider using `st.plotly_chart` with `on_select` and `key` parameter (preserves zoom via session state)
- Document as known limitation if using `plotly_events`
**Warning signs:** User reports frustration with zoom resetting, especially with large/dense scatter plots

### Pitfall 6: Detail Panel Flickers on Click
**What goes wrong:** Detail panel briefly shows "Click a point" message then updates to selected point
**Why it happens:** Streamlit reruns entire script; detail panel renders before `plotly_events()` updates session state
**How to avoid:**
- Use `st.empty()` placeholder for detail panel and update after event capture
- Or accept as inherent Streamlit behavior (minimal impact on UX)
**Warning signs:** Visual flicker visible on each click, especially noticeable with slow network/rendering

## Code Examples

Verified patterns from official sources:

### Capturing Click Events and Updating Session State
```python
# Source: https://github.com/ethanhe42/streamlit-plotly-events/blob/master/README.md
import streamlit as st
from streamlit_plotly_events import plotly_events
import plotly.graph_objects as go

# Initialize session state
if 'selected_point_idx' not in st.session_state:
    st.session_state.selected_point_idx = None

# Create figure (example with existing data)
fig = go.Figure()
fig.add_trace(go.Scatter(x=[1,2,3], y=[4,5,6], mode='markers'))

# Capture click events
selected_points = plotly_events(
    fig,
    click_event=True,      # Enable click events (default: True)
    select_event=False,    # Disable lasso/box selection
    hover_event=False      # Disable hover (VERY RESOURCE INTENSIVE)
)

# Update session state if point clicked
if selected_points:
    st.session_state.selected_point_idx = selected_points[0]['pointIndex']
```

### Building Dynamic Marker Arrays for Highlighting
```python
# Source: https://plotly.com/python/bubble-charts/ (per-point marker arrays)
# Source: https://plotly.com/python/marker-style/ (marker line properties)

# Build marker property arrays based on selection
selected_idx = st.session_state.selected_point_idx

# Per-point size array
marker_sizes = [
    12 if i == selected_idx else 7
    for i in range(len(df))
]

# Per-point line width array (for border emphasis)
marker_line_widths = [
    2 if i == selected_idx else 0
    for i in range(len(df))
]

# Create scatter with per-point arrays
fig = go.Figure()
fig.add_trace(go.Scatter(
    x=df['x_emb'],
    y=df['y_emb'],
    mode='markers',
    hovertemplate=df['hovertxt'].tolist(),
    marker=dict(
        size=marker_sizes,                    # Per-point array
        color=df['HEX-Win'].tolist(),         # Per-point array (existing)
        symbol=df['clust_symb'].tolist(),     # Per-point array (existing)
        line=dict(
            color='black',                     # Uniform (or could be per-point array)
            width=marker_line_widths           # Per-point array
        ),
    ),
    name='',
))
```

### Two-Column Layout with Conditional Detail Panel
```python
# Source: https://docs.streamlit.io/develop/api-reference/layout
import streamlit as st

# Create two columns: chart (left, wider) and detail panel (right, narrower)
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("Design Space")
    # Chart code here (see above)
    selected_points = plotly_events(fig, click_event=True)
    if selected_points:
        st.session_state.selected_point_idx = selected_points[0]['pointIndex']

with col2:
    st.subheader("Solution Details")

    # Conditional rendering based on session state
    if st.session_state.selected_point_idx is not None:
        idx = st.session_state.selected_point_idx
        row = df.iloc[idx]

        # Display details with Markdown formatting
        st.markdown(f"**Participant:** {row['ParticipantID']}")
        st.markdown(f"**Group:** {row['GroupID']}")
        st.markdown(f"**Phase:** {row['PrePost']}")

        # Separator
        st.divider()

        # More details...
    else:
        st.info("Click a point on the chart to view solution details")
```

### Loading External Images with Fallback
```python
# Source: https://docs.streamlit.io/develop/api-reference/media/st.image
import streamlit as st

# Get image URL from data (example: GitHub raw content URL)
image_url = row['videoPreview']

# Conditional display with fallback
if image_url and image_url != '-':
    try:
        st.image(
            image_url,
            caption=f"Solution {row['SolutionID']}",
            width=300,  # Fixed width in pixels
            use_container_width=False  # Deprecated: use width parameter
        )
    except Exception as e:
        st.warning("Screenshot unavailable")
        st.caption(f"URL: {image_url}")
else:
    st.info("No screenshot available for this solution")
```

### Session State Initialization Pattern
```python
# Source: https://docs.streamlit.io/develop/concepts/architecture/session-state
import streamlit as st

# Best practice: Initialize all session state keys at top of script
if 'selected_point_idx' not in st.session_state:
    st.session_state.selected_point_idx = None

# Access with confidence (no KeyError possible)
if st.session_state.selected_point_idx is not None:
    # Use the value
    selected_row = df.iloc[st.session_state.selected_point_idx]
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `streamlit-plotly-events` only option | Native `st.plotly_chart(on_select="rerun")` available | Streamlit 1.35.0 (June 2024) | Native option more future-proof but only handles selection events (box/lasso/click), not true click events; `streamlit-plotly-events` still needed for click-only UX |
| Manual image downloading | Direct URL support in `st.image()` | Streamlit 1.0+ | Streamlit handles HTTP requests, caching, CORS internally; no need for requests library |
| `use_container_width` parameter | `width` parameter with "content"/"stretch"/int | Streamlit 1.36.0 (August 2024) | Old parameter deprecated but still works; new parameter more explicit |
| Global variables for state | `st.session_state` API | Streamlit 0.84.0 (July 2021) | Session state persists across reruns per user; globals don't survive reruns |

**Deprecated/outdated:**
- `use_container_width=True/False` in `st.image()`: Use `width="stretch"` or `width="content"` instead (deprecated in Streamlit 1.36.0)
- Manual state management via hidden widgets: Use `st.session_state` directly (cleaner, more explicit since 0.84.0)
- `streamlit-plotly-events` may become obsolete if Streamlit adds native click event support (currently only selection events supported as of 1.40+)

## Open Questions

1. **Does streamlit-plotly-events work reliably with current Streamlit versions (1.30+)?**
   - What we know: Last updated April 2021, community reports of empty chart rendering in some cases
   - What's unclear: Whether issues are reproducible with current environment (Streamlit 1.30+, Python 3.12)
   - Recommendation: Test with minimal example in Phase 2 Task 1; be prepared to pivot to native `on_select` if component fails

2. **What's the optimal column ratio for 700px height chart + detail panel?**
   - What we know: Common ratios are 2:1, 3:2, or 3:1 for chart:detail
   - What's unclear: How wide detail panel needs to be for screenshot (GitHub images vary in aspect ratio)
   - Recommendation: Start with 2:1 ratio, adjust based on visual testing with real data

3. **Should we reset selection when chart is clicked outside a point?**
   - What we know: `plotly_events()` returns empty list when background is clicked
   - What's unclear: User expectation - should clicking background deselect current point or preserve selection?
   - Recommendation: Preserve selection (don't reset on empty click) for stable UX; user can select different point to change

4. **How should we handle missing/invalid GitHub image URLs?**
   - What we know: Data has `videoPreview` field, some may be "-" or invalid
   - What's unclear: Whether all valid URLs follow same pattern, whether CORS issues exist
   - Recommendation: Implement conditional check for "-", use try-except for invalid URLs, display friendly fallback message

## Sources

### Primary (HIGH confidence)
- streamlit-plotly-events GitHub: https://github.com/ethanhe42/streamlit-plotly-events - Component usage, event data structure
- streamlit-plotly-events PyPI: https://pypi.org/project/streamlit-plotly-events/ - Version 0.0.6, last updated April 2021
- Streamlit Session State docs: https://docs.streamlit.io/develop/concepts/architecture/session-state - Initialization patterns, best practices
- Streamlit st.plotly_chart docs: https://docs.streamlit.io/develop/api-reference/charts/st.plotly_chart - on_select parameter, PlotlyState schema
- Streamlit Layout docs: https://docs.streamlit.io/develop/api-reference/layout - st.columns, st.container, st.expander
- Streamlit st.image docs: https://docs.streamlit.io/develop/api-reference/media/st.image - URL support, width parameter
- Streamlit st.markdown docs: https://docs.streamlit.io/develop/api-reference/text/st.markdown - Markdown formatting
- Plotly Marker Style docs: https://plotly.com/python/marker-style/ - Marker borders, opacity, per-point customization
- Plotly Bubble Charts docs: https://plotly.com/python/bubble-charts/ - Per-point marker.size arrays
- Plotly Scatter API: https://plotly.com/python-api-reference/generated/plotly.graph_objects.Scatter.html - Marker properties

### Secondary (MEDIUM confidence)
- Streamlit forum - Empty Plotly Chart: https://discuss.streamlit.io/t/empty-plotly-chart-when-using-streamlit-plotly-events/115654 - Known issue with streamlit-plotly-events
- Streamlit forum - Session state with clicks: https://discuss.streamlit.io/t/how-to-make-session-state-updated-when-i-select-a-point-on-plotly-chart/92735 - Update patterns
- Streamlit forum - Avoiding reruns: https://discuss.streamlit.io/t/avoiding-complete-reruns-during-the-plotly-events-like-mouse-clicks-on-the-graphs/119819 - Rerun behavior
- Streamlit forum - GitHub images: https://discuss.streamlit.io/t/opening-an-image-in-streamlit-cloud-from-github/20036 - raw.githubusercontent.com format
- Plotly community - Marker borders: https://community.plotly.com/t/add-mark-border-on-specific-points/66975 - Per-point line styling
- Plotly docs - Creating and updating figures: https://plotly.com/python/creating-and-updating-figures/ - update_traces, for_each_trace patterns

### Tertiary (LOW confidence - flagged for validation)
- Medium article on session state: https://medium.com/@baertschi91/state-management-in-streamlit-135b51aae3ee - Best practices (needs verification with official docs)
- GeeksforGeeks - Exception handling requests: https://www.geeksforgeeks.org/python/exception-handling-of-python-requests-module/ - Error handling patterns (Python standard, not Streamlit-specific)

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - streamlit-plotly-events is documented and widely used; version 0.0.6 confirmed on PyPI
- Architecture: HIGH - All patterns verified with official Streamlit/Plotly documentation
- Pitfalls: MEDIUM-HIGH - Empty chart issue confirmed in community forum; other pitfalls inferred from Streamlit rerun model and session state documentation
- Image loading: HIGH - st.image URL support confirmed in official docs; GitHub raw format confirmed via community discussions
- Event handling: MEDIUM - streamlit-plotly-events last updated 2021, potential version compatibility concerns flagged for testing

**Research date:** 2026-02-14
**Valid until:** 2026-03-16 (30 days - stable ecosystem, but streamlit-plotly-events age is concern)

**Critical validation needed:**
- Test streamlit-plotly-events compatibility with Streamlit 1.30+ and Python 3.12 (Task 1 of Phase 2)
- Verify GitHub image URLs load correctly in deployed Streamlit app (not just local)
