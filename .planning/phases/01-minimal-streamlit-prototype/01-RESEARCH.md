# Phase 1: Minimal Streamlit Prototype - Research

**Researched:** 2026-02-14
**Domain:** Streamlit web app with Plotly visualizations and Community Cloud deployment
**Confidence:** HIGH

## Summary

Phase 1 builds a minimal Streamlit app that loads pre-computed data files (from Phase 0) and displays a static scatter plot with hover interactions. The app must deploy to Streamlit Community Cloud within free tier constraints (~1GB RAM, slim dependencies). The standard approach uses **Streamlit's native caching (@st.cache_data)** for fast data loading, **Plotly Express scatter** for quick visualization with automatic hover text, **st.set_page_config** for layout configuration, and **streamlit-plotly-events** for click interactions (Phase 2+). Deployment requires a **GitHub repository** with **requirements.txt** in the root or app directory, and the app entry point named **streamlit_app.py** for zero-config deployment.

The minimal prototype focuses on proving the deployment works and data loads efficiently. Phase 0 created three key files: `df_base.parquet` (148KB, 80+ columns), `metadata.json` (participant colors/symbols), and `convex_hulls.pkl` (5.5KB, polygon vertices). The app needs only **5 dependencies** for deployment: streamlit, plotly, pandas, numpy, shapely. Heavy computation deps (umap-learn, scikit-learn, scipy, igraph) stay in requirements-dev.txt for local pipeline execution only.

**Primary recommendation:** Create `streamlit_app/streamlit_app.py` as the main entry point with @st.cache_data loading functions, use Plotly Express px.scatter with color/symbol mapping from metadata.json, set layout="wide" via st.set_page_config, and deploy from GitHub with minimal requirements.txt (~150-200MB total). Defer streamlit-plotly-events until Phase 2 (click interactions) to keep Phase 1 truly minimal.

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| streamlit | latest | Web app framework and deployment platform | Official platform for Python data apps, zero-config deployment to Community Cloud, native caching primitives |
| plotly | 5.23.0 | Interactive scatter plot with hover text | Already in requirements.txt, Plotly Express provides high-level scatter API with automatic legends and hover |
| pandas | 2.2.3 | Load parquet files and DataFrame operations | Already in requirements.txt, native parquet support via pyarrow engine |
| numpy | 2.0.2 | Array operations (convex hull vertices) | Already in requirements.txt, required for shapely |
| shapely | 2.0.6 | Geometric operations for convex hulls | Already in requirements.txt, needed if app displays participant polygons |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| streamlit-plotly-events | 0.0.6 (or 0.0.7 fork) | Click interactions on Plotly charts | Phase 2+ when implementing click-to-select functionality; NOT needed for Phase 1 static hover-only display |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Plotly Express scatter | Plotly graph_objects.Scatter | graph_objects gives fine-grained control but requires 5-100x more code; Express is sufficient for standard scatter with color/symbol mapping |
| Streamlit | Dash (existing app) | Already using Plotly/Dash but Streamlit chosen for Python-native simplicity, better Community Cloud integration, and lower migration effort |
| st.cache_data | functools.lru_cache | st.cache_data is Streamlit-aware (persists across sessions, handles reruns correctly), lru_cache only caches within single Python process |

**Installation (Streamlit deployment):**
```bash
# requirements.txt (root or streamlit_app/ directory)
streamlit>=1.30.0
plotly>=5.23.0
pandas>=2.2.0
numpy>=2.0.0
shapely>=2.0.0
```

**Installation (development with full pipeline):**
```bash
# requirements-dev.txt
-r requirements.txt

# Phase 0 pipeline dependencies (NOT deployed)
umap-learn>=0.5.7
scikit-learn>=1.5.2
scipy>=1.14.1
igraph>=0.11.8
gower>=0.1.2
openpyxl>=3.1.5
```

## Architecture Patterns

### Recommended Project Structure
```
C:/Py/DS_Viz_SL/
├── streamlit_app/
│   ├── streamlit_app.py          # Main entry point (Streamlit auto-detects this name)
│   └── data/                      # Pre-computed data files (committed to repo)
│       ├── df_base.parquet        # 148KB, all solutions with 80+ columns
│       ├── metadata.json          # Participant colors, cluster symbols, IDs
│       ├── convex_hulls.pkl       # 5.5KB, polygon vertices per participant
│       └── manifest.json          # Computation provenance (optional for app)
├── scripts/                       # Existing analysis/pipeline scripts
│   ├── precompute.py              # Phase 0 pipeline CLI
│   └── design_space/              # Computation modules (not imported by Streamlit)
├── data/
│   └── MASKED_DATA_analysis_v2.xlsx  # Source data (NOT deployed)
├── requirements.txt               # Streamlit deployment dependencies (~150-200MB)
└── requirements-dev.txt           # Full pipeline dependencies (~400MB+)
```

**Why streamlit_app.py:** Streamlit Community Cloud auto-detects this filename when deploying from the `streamlit_app/` directory. No configuration needed.

### Pattern 1: Cached Data Loading with @st.cache_data
**What:** Decorator that caches function return values across app reruns and user sessions
**When to use:** Loading data files (parquet, pickle, JSON) that don't change during app runtime
**Example:**
```python
# Source: Streamlit official docs - st.cache_data
import streamlit as st
import pandas as pd
import pickle
import json
from pathlib import Path

DATA_DIR = Path(__file__).parent / 'data'

@st.cache_data
def load_solutions():
    """Load main solutions DataFrame from parquet.
    Cached to avoid re-reading 148KB file on every interaction.
    """
    df = pd.read_parquet(DATA_DIR / 'df_base.parquet')
    return df

@st.cache_data
def load_metadata():
    """Load participant colors and cluster symbols from JSON.
    Returns dict with color_mapping, cluster_symbols, participant_ids.
    """
    with open(DATA_DIR / 'metadata.json', 'r') as f:
        metadata = json.load(f)
    return metadata

@st.cache_data
def load_convex_hulls():
    """Load convex hull vertices from pickle.
    Returns dict: {participant_id: {'x': [...], 'y': [...], 'area': float}}
    """
    with open(DATA_DIR / 'convex_hulls.pkl', 'rb') as f:
        hulls = pickle.load(f)
    return hulls

# Call once at module level (cached result reused)
df = load_solutions()
metadata = load_metadata()
hulls = load_convex_hulls()
```

**Performance:** First load takes <2 seconds (requirement: DEPL-01), subsequent loads are instant (cached in memory).

**Security note:** Phase 0 pipeline creates the pickle files, not user input. Safe to load trusted local files.

### Pattern 2: Page Configuration with st.set_page_config
**What:** Configure page layout, title, icon, sidebar state (must be first Streamlit command)
**When to use:** Always, as first line after imports in main app file
**Example:**
```python
# Source: Streamlit official docs - st.set_page_config
import streamlit as st

# MUST be first Streamlit command
st.set_page_config(
    page_title="Design Space Visualization",
    page_icon="📊",
    layout="wide",  # Use full screen width for large scatter plot
    initial_sidebar_state="auto",  # Collapsed on mobile, expanded on desktop
)
```

**Allowed values:**
- `layout`: "centered" (fixed-width column) or "wide" (full screen)
- `initial_sidebar_state`: "auto", "expanded", "collapsed"
- `page_icon`: single emoji, ":emoji_shortcode:", ":material/icon_name:", or image URL

### Pattern 3: Plotly Express Scatter with Custom Colors and Symbols
**What:** High-level scatter plot with automatic legend, hover text, color/symbol mapping
**When to use:** Standard scatter plots with categorical color and symbol dimensions
**Example:**
```python
# Source: Plotly official docs - plotly.express.scatter
import plotly.express as px
import pandas as pd

# Load data and metadata (from Pattern 1)
df = load_solutions()
metadata = load_metadata()

# Map cluster IDs to symbol names
df['cluster_symbol'] = df['cluster_id'].astype(str).map(metadata['cluster_symbols'])

# Create color list in participant order
color_discrete_map = metadata['color_mapping']  # {participant_id: hex_color}

# Scatter plot with color by participant, symbol by cluster
fig = px.scatter(
    df,
    x='x_emb',
    y='y_emb',
    color='ParticipantID',  # Color points by participant
    symbol='cluster_symbol',  # Shape points by cluster
    color_discrete_map=color_discrete_map,  # Use exact hex colors from metadata
    hover_data={
        'ParticipantID': True,   # Show in hover
        'SolutionNum': True,     # Show solution number
        'Condition': True,       # Show pre/post
        'Result': True,          # Show result value
        'x_emb': False,          # Hide x coordinate
        'y_emb': False,          # Hide y coordinate
        'cluster_symbol': False, # Hide symbol name
    },
    labels={
        'x_emb': 'UMAP X',
        'y_emb': 'UMAP Y',
        'ParticipantID': 'Participant',
    },
)

# Optional: Update layout for better appearance
fig.update_layout(
    showlegend=True,
    legend=dict(
        orientation="v",
        yanchor="top",
        y=1,
        xanchor="left",
        x=1.02
    ),
    hovermode='closest',
)

# Display in Streamlit with responsive width
st.plotly_chart(fig, use_container_width=True)
```

**Hover text:** Plotly Express automatically shows all columns in hover_data with formatted labels.

### Pattern 4: Custom Hover Templates (if hover_data insufficient)
**What:** Fine-grained control over hover text formatting using hovertemplate
**When to use:** When hover_data parameter doesn't provide enough formatting control
**Example:**
```python
# Source: Plotly official docs - hover text and formatting
import plotly.graph_objects as go

# After creating Plotly Express figure
fig = px.scatter(...)

# Update hover template for all traces
fig.update_traces(
    hovertemplate=(
        "<b>%{customdata[0]}</b><br>"  # Participant ID (bold)
        "Solution: %{customdata[1]}<br>"  # Solution number
        "Condition: %{customdata[2]}<br>"  # Pre/Post
        "Result: %{customdata[3]:.2f}<br>"  # Result (2 decimals)
        "<extra></extra>"  # Hide trace name in hover box
    ),
    customdata=df[['ParticipantID', 'SolutionNum', 'Condition', 'Result']].values
)
```

**Formatting syntax:**
- `%{x}`, `%{y}`: axis values
- `%{customdata[n]}`: nth column from customdata array
- `%{variable:.2f}`: d3-format number formatting (2 decimal places)
- `<extra></extra>`: remove secondary hover box with trace name

### Pattern 5: Streamlit Rerun Behavior and Session State
**What:** Streamlit reruns entire script from top to bottom on every interaction; session_state persists data
**When to use:** Understanding when caching is needed and how widgets trigger reruns
**Example:**
```python
# Source: Streamlit official docs - session state
import streamlit as st

# Script reruns from top on EVERY interaction (button click, slider change, etc.)
# @st.cache_data prevents reloading data on every rerun
df = load_solutions()  # Only loads once, cached thereafter

# Widgets automatically trigger reruns when interacted with
selected_participant = st.selectbox('Select Participant', options=['All'] + metadata['participant_ids'])

# Use session_state to persist values across reruns
if 'click_count' not in st.session_state:
    st.session_state.click_count = 0

if st.button('Count'):
    st.session_state.click_count += 1  # Persists across reruns

st.write(f"Clicks: {st.session_state.click_count}")
```

**Key insight:** Without caching, load_solutions() would re-read the parquet file on EVERY widget interaction, slider move, or button click. @st.cache_data is essential for performance.

### Anti-Patterns to Avoid
- **Importing computation modules in Streamlit app**: Don't import scripts/design_space/* in streamlit_app.py; this pulls in heavy dependencies (umap-learn, scikit-learn) and bloats deployment. Only load pre-computed data files.
- **Missing st.set_page_config or calling it late**: Must be first Streamlit command, before any st.write/st.title/etc. Causes cryptic errors if called later.
- **Loading data without caching**: Without @st.cache_data, parquet/pickle files reload on EVERY interaction (button, slider, widget). App becomes unusably slow.
- **use_container_width without layout="wide"**: For large scatter plots, need both st.set_page_config(layout="wide") AND st.plotly_chart(..., use_container_width=True) to use full screen.
- **Mixing color/symbol with color_discrete_sequence**: When using color_discrete_map for exact hex colors, don't also pass color_discrete_sequence. The map takes precedence.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Data caching across reruns | Global variables or manual file timestamp checking | @st.cache_data decorator | Streamlit-aware caching handles multiple sessions, TTL, invalidation, pickling; manual caching breaks with concurrent users |
| Interactive scatter plots | matplotlib with mpld3, Bokeh, custom canvas | Plotly Express px.scatter + st.plotly_chart | Plotly hover/zoom/pan built-in; Streamlit integration native; matplotlib not interactive in browser |
| Hover text formatting | Custom tooltip HTML, JavaScript injection | Plotly hover_data or hovertemplate | Plotly handles formatting, positioning, responsive behavior; custom tooltips break on mobile or with zoom |
| Page layout and responsive width | Custom CSS, HTML columns | st.set_page_config(layout="wide") + use_container_width=True | Streamlit's responsive layout handles different screen sizes automatically; custom CSS breaks on Community Cloud |
| Deployment server | Flask/FastAPI + Gunicorn + Nginx | Streamlit Community Cloud | Zero-config deployment from GitHub; auto-restarts on push; free tier sufficient for this use case |
| Click interactions on Plotly | Custom JavaScript callbacks, Dash callbacks | streamlit-plotly-events component | Only viable Streamlit option for Plotly click events; bubbles events back to Python; well-tested by community |

**Key insight:** Streamlit and Plotly have solved the "interactive data app" problem. Don't recreate their solutions. Use native primitives.

## Common Pitfalls

### Pitfall 1: Exceeding Community Cloud Free Tier Resource Limits
**What goes wrong:** App shows "Argh. This app has gone over its resource limits" error, becomes unresponsive
**Why it happens:** Free tier has limited RAM (~1GB commonly reported); loading large dependencies (umap-learn, scikit-learn, full scipy) exceeds limit
**How to avoid:** Separate requirements.txt (deployment: 5 packages, ~150-200MB) from requirements-dev.txt (full pipeline: 15+ packages, ~400MB+); pre-compute all heavy operations in Phase 0
**Warning signs:** Deployment takes >5 minutes, app crashes on first load, memory usage in app logs shows >800MB

**Verification:**
```bash
# Check deployment size BEFORE pushing
pip install --dry-run -r requirements.txt 2>&1 | grep "Successfully installed"

# Phase 1 requirements.txt should show ~5 packages
# If it shows umap-learn, scikit-learn, scipy, igraph → TOO LARGE for deployment
```

### Pitfall 2: st.set_page_config Called After Other Streamlit Commands
**What goes wrong:** "set_page_config() can only be called once per app, and must be called as the first Streamlit command" error
**Why it happens:** Any st.write(), st.title(), st.cache_data call, etc. before st.set_page_config triggers error
**How to avoid:** First import statements, then st.set_page_config as literal first Streamlit command, then data loading/caching
**Warning signs:** App runs locally but fails on deployment; error mentions "first Streamlit command"

**Correct order:**
```python
import streamlit as st
import pandas as pd
# Other imports...

st.set_page_config(...)  # FIRST Streamlit command

# NOW safe to call other commands
@st.cache_data
def load_data():
    ...
```

### Pitfall 3: Pickle Security Warnings with Untrusted Data
**What goes wrong:** Security vulnerability if loading pickle files from untrusted sources
**Why it happens:** pickle.load() can execute arbitrary code during unpickling; malicious pickle files can run malware
**How to avoid:** Only load pickle files created by Phase 0 pipeline (trusted source); never load user-uploaded pickle files
**Warning signs:** Streamlit docs show pickle security warning; community discussions mention CVEs

**Safe usage:**
```python
# SAFE: Loading pickle created by our own Phase 0 pipeline
@st.cache_data
def load_convex_hulls():
    with open(DATA_DIR / 'convex_hulls.pkl', 'rb') as f:
        return pickle.load(f)  # File created by scripts/precompute.py, trusted

# UNSAFE: Never do this
# uploaded_file = st.file_uploader("Upload pickle")
# pickle.load(uploaded_file)  # DANGEROUS: user could upload malicious pickle
```

### Pitfall 4: Requirements.txt in Wrong Location
**What goes wrong:** Community Cloud deployment fails with "Could not find a version that satisfies the requirement X"
**Why it happens:** requirements.txt must be in root of repo OR same directory as entrypoint file (streamlit_app.py)
**How to avoid:** Place requirements.txt in project root (C:/Py/DS_Viz_SL/requirements.txt) OR in streamlit_app/ directory
**Warning signs:** Deployment logs show "No requirements.txt found" or package import errors

**Correct locations:**
```
# Option 1: Root of repository (RECOMMENDED)
C:/Py/DS_Viz_SL/requirements.txt
C:/Py/DS_Viz_SL/streamlit_app/streamlit_app.py

# Option 2: Same directory as entrypoint
C:/Py/DS_Viz_SL/streamlit_app/requirements.txt
C:/Py/DS_Viz_SL/streamlit_app/streamlit_app.py

# WRONG: Subdirectory not matching entrypoint location
C:/Py/DS_Viz_SL/config/requirements.txt  # Won't be found
```

### Pitfall 5: Data Files Not Committed to Repository
**What goes wrong:** Streamlit app loads data from streamlit_app/data/ but files missing on Community Cloud; FileNotFoundError
**Why it happens:** Pre-computed data files (parquet, pickle, JSON) must be committed to git repo; Community Cloud clones repo and expects files present
**How to avoid:** Ensure streamlit_app/data/*.parquet, *.pkl, *.json are committed and pushed; verify with `git ls-files streamlit_app/data/`
**Warning signs:** App works locally but fails on deployment with "No such file or directory: 'data/df_base.parquet'"

**Verification:**
```bash
# Check that data files are tracked by git
git ls-files streamlit_app/data/

# Should show:
# streamlit_app/data/.gitkeep
# streamlit_app/data/convex_hulls.pkl
# streamlit_app/data/df_base.parquet
# streamlit_app/data/manifest.json
# streamlit_app/data/metadata.json

# If empty or missing files → git add and commit them
git add streamlit_app/data/*.parquet streamlit_app/data/*.pkl streamlit_app/data/*.json
git commit -m "feat(streamlit): add pre-computed data files"
```

### Pitfall 6: Plotly Figure Too Large (>1000 Points) Without WebGL
**What goes wrong:** Scatter plot with 1000+ points becomes slow, laggy, or crashes browser
**Why it happens:** Plotly defaults to SVG renderer which is slow for large datasets; should use WebGL for >1000 points
**How to avoid:** For this project (100 solutions × 31 participants = 3100 points), Plotly auto-enables WebGL. Verify by checking fig.data[0].mode
**Warning signs:** Hover becomes laggy, zoom/pan stutters, browser console shows performance warnings

**Verification:**
```python
# Plotly automatically uses WebGL for >1000 points
# But can force it explicitly for certainty
fig.update_traces(marker=dict(size=6), selector=dict(mode='markers'))

# Check in browser console after rendering:
# Should see: "webgl" renderer in use
# If seeing "svg", manually set:
st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': True})
```

### Pitfall 7: Mixed Dependency Managers
**What goes wrong:** Community Cloud deployment fails with "You cannot mix and match Python package managers"
**Why it happens:** Both requirements.txt AND environment.yml (or Pipfile) exist; Community Cloud only uses first one found
**How to avoid:** Use requirements.txt only; remove or rename environment.yml if present
**Warning signs:** Deployment logs show "Found multiple package files" or installs wrong versions

**Check:**
```bash
# Verify only requirements.txt exists in project root
ls -la requirements.txt environment.yml Pipfile pyproject.toml 2>/dev/null

# Should show ONLY requirements.txt
# If others exist, remove or move them
```

## Code Examples

Verified patterns from official sources and requirements:

### Minimal Streamlit App Entry Point
```python
# Source: Streamlit deployment best practices
# File: streamlit_app/streamlit_app.py
import streamlit as st
import pandas as pd
import plotly.express as px
import pickle
import json
from pathlib import Path

# MUST be first Streamlit command
st.set_page_config(
    page_title="Design Space Visualization",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="auto",
)

# Data directory relative to this file
DATA_DIR = Path(__file__).parent / 'data'

@st.cache_data
def load_solutions():
    """Load solutions DataFrame from parquet (148KB, <2s target)."""
    return pd.read_parquet(DATA_DIR / 'df_base.parquet')

@st.cache_data
def load_metadata():
    """Load participant colors, cluster symbols, IDs."""
    with open(DATA_DIR / 'metadata.json', 'r') as f:
        return json.load(f)

@st.cache_data
def load_convex_hulls():
    """Load convex hull vertices per participant."""
    with open(DATA_DIR / 'convex_hulls.pkl', 'rb') as f:
        return pickle.load(f)

# Main app
st.title("Design Space Visualization")

# Load data (cached, runs once)
df = load_solutions()
metadata = load_metadata()
hulls = load_convex_hulls()

st.write(f"Loaded {len(df)} solutions from {len(metadata['participant_ids'])} participants")

# Next: Create scatter plot (see next example)
```

### Scatter Plot with Color by Participant, Symbol by Cluster
```python
# Source: Plotly Express official docs + Phase 1 requirements
# Requirement: SCAT-01 (color by participant, cluster symbols)

# Map cluster IDs to symbols from metadata
df['cluster_symbol'] = df['cluster_id'].astype(str).map(metadata['cluster_symbols'])

# Create scatter plot
fig = px.scatter(
    df,
    x='x_emb',
    y='y_emb',
    color='ParticipantID',
    symbol='cluster_symbol',
    color_discrete_map=metadata['color_mapping'],  # Exact hex colors
    hover_data={
        'ParticipantID': True,
        'SolutionNum': True,
        'Condition': True,  # Pre/Post
        'Result': True,
        'x_emb': False,  # Hide coordinates
        'y_emb': False,
        'cluster_symbol': False,
    },
    labels={
        'x_emb': 'UMAP Dimension 1',
        'y_emb': 'UMAP Dimension 2',
        'ParticipantID': 'Participant',
    },
)

# Update layout for legend positioning
fig.update_layout(
    showlegend=True,
    legend=dict(
        orientation="v",
        yanchor="top",
        y=1,
        xanchor="left",
        x=1.02  # Place legend outside plot area
    ),
    hovermode='closest',
)

# Display with responsive width
st.plotly_chart(fig, use_container_width=True)
```

### Custom Hover Template (Alternative to hover_data)
```python
# Source: Plotly hover formatting docs
# Use when hover_data doesn't provide enough control

# Prepare custom data array for hover
custom_data_cols = ['ParticipantID', 'SolutionNum', 'Condition', 'Result']
fig = px.scatter(df, x='x_emb', y='y_emb', color='ParticipantID', symbol='cluster_symbol')

# Update hover template
fig.update_traces(
    customdata=df[custom_data_cols].values,
    hovertemplate=(
        "<b>Participant:</b> %{customdata[0]}<br>"
        "<b>Solution:</b> %{customdata[1]}<br>"
        "<b>Condition:</b> %{customdata[2]}<br>"
        "<b>Result:</b> %{customdata[3]:.2f}<br>"
        "<extra></extra>"  # Remove trace name
    )
)

st.plotly_chart(fig, use_container_width=True)
```

### Loading Parquet with Specific Columns (Optimization)
```python
# Source: pandas.read_parquet docs
# Optimization: Load only needed columns to reduce memory

@st.cache_data
def load_solutions_minimal():
    """Load only columns needed for scatter plot.
    Reduces memory footprint from full 80+ columns.
    """
    columns_needed = [
        'x_emb', 'y_emb',  # Coordinates
        'ParticipantID', 'SolutionNum',  # IDs
        'Condition', 'Result',  # Hover data
        'cluster_id',  # Symbol mapping
    ]
    return pd.read_parquet(DATA_DIR / 'df_base.parquet', columns=columns_needed)
```

### Community Cloud requirements.txt (Minimal Dependencies)
```txt
# File: requirements.txt (project root)
# Phase 1: Minimal Streamlit prototype deployment
# Target: ~150-200MB total installed size

streamlit>=1.30.0
plotly>=5.23.0
pandas>=2.2.0
numpy>=2.0.0
shapely>=2.0.0

# Phase 2+ (defer until needed):
# streamlit-plotly-events>=0.0.6  # Click interactions
```

### Development requirements.txt (Full Pipeline)
```txt
# File: requirements-dev.txt (project root)
# Include production dependencies
-r requirements.txt

# Phase 0 pipeline dependencies (NOT deployed to Community Cloud)
umap-learn>=0.5.7
scikit-learn>=1.5.2
scipy>=1.14.1
igraph>=0.11.8
gower>=0.1.2
openpyxl>=3.1.5

# Optional: Development tools
pytest>=7.0.0
black>=24.0.0
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| @st.cache (deprecated) | @st.cache_data and @st.cache_resource | Streamlit 1.18 (2023) | Clearer separation: cache_data for serializable objects, cache_resource for shared resources; better error messages |
| use_container_width=True | width="stretch", height="content" | Streamlit 1.30+ (2024) | use_container_width deprecated but still works; new width/height parameters more flexible |
| plotly.graph_objects for simple plots | Plotly Express px.scatter | Plotly 4.0+ (2019) | 5-100x less code for standard plots; auto-legend, auto-colors, cleaner API |
| Manual hover text with text parameter | hover_data and hovertemplate | Plotly 4.0+ (2019) | Declarative hover configuration, better formatting, multi-line support |
| requirements.txt only | requirements.txt + packages.txt | Community Cloud 2022+ | packages.txt for apt-get system dependencies; requirements.txt for Python only |
| streamlit_app.py in root | streamlit_app.py in subdirectory | Community Cloud 2023+ | Support for monorepo structure; app can be in streamlit_app/ subdirectory |

**Deprecated/outdated:**
- `@st.cache`: Use `@st.cache_data` for DataFrames/JSON/serializable objects, `@st.cache_resource` for database connections/ML models
- `use_container_width=True`: Deprecated in favor of `width="stretch"` (but still works in Streamlit 1.30+)
- `st.beta_*` and `st.experimental_*`: Most promoted to stable API or removed in Streamlit 1.0+

## Open Questions

1. **streamlit-plotly-events version choice**
   - What we know: Original (0.0.6, last updated 2021) is inactive; fork streamlit-plotly-events2 (0.0.7, 2024) is more recent
   - What's unclear: Which version is more stable? Does fork maintain compatibility?
   - Recommendation: Defer to Phase 2; when implementing clicks, test 0.0.6 first (more established), fall back to 0.0.7 if compatibility issues

2. **Exact Community Cloud RAM limit**
   - What we know: Community discussions mention ~1GB; official docs say "limited resources" but don't specify exact number
   - What's unclear: Is it 1GB, 2GB, or dynamic based on load?
   - Recommendation: Design for 1GB constraint (worst case); Phase 1 requirements (~150-200MB) well under limit

3. **Convex hull display in Phase 1**
   - What we know: Phase 0 created convex_hulls.pkl; requirements list shapely
   - What's unclear: Should Phase 1 display participant polygons, or just scatter points?
   - Recommendation: Phase 1 shows scatter only (meet "minimal" goal); defer polygons to Phase 2+ if needed

4. **Data file commit vs .gitignore**
   - What we know: Phase 0 committed data files; Community Cloud needs them in repo
   - What's unclear: Should data/ directory be in .gitignore, or committed?
   - Recommendation: Commit streamlit_app/data/* files (they're small: 148KB + 5.5KB); exclude source data/MASKED_DATA_analysis_v2.xlsx (large, not needed for deployment)

## Sources

### Primary (HIGH confidence)
- [Streamlit st.cache_data documentation](https://docs.streamlit.io/develop/api-reference/caching-and-state/st.cache_data) - Official caching API reference
- [Streamlit st.set_page_config documentation](https://docs.streamlit.io/develop/api-reference/configuration/st.set_page_config) - Page configuration parameters
- [Streamlit st.plotly_chart documentation](https://docs.streamlit.io/develop/api-reference/charts/st.plotly_chart) - Plotly integration, use_container_width, responsive sizing
- [Streamlit Community Cloud deployment guide](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy) - GitHub integration, requirements.txt location
- [Streamlit Community Cloud dependencies guide](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/app-dependencies) - Package manager priority, Python version, requirements.txt placement
- [Streamlit Community Cloud status and limitations](https://docs.streamlit.io/deploy/streamlit-community-cloud/status) - Resource limits, GitHub permissions, package restrictions
- [Plotly Express scatter documentation](https://plotly.com/python-api-reference/generated/plotly.express.scatter) - Parameters, color mapping, symbol mapping
- [Plotly hover text and formatting](https://plotly.com/python/hover-text-and-formatting/) - hover_data, hovertemplate, customdata usage
- [Plotly discrete colors](https://plotly.com/python/discrete-color/) - color_discrete_map, color_discrete_sequence, hex colors
- [streamlit-plotly-events GitHub](https://github.com/ethanhe42/streamlit-plotly-events) - Installation, usage, event types, return data
- Existing codebase: `streamlit_app/data/*.parquet, *.pkl, *.json` - Pre-computed data files from Phase 0

### Secondary (MEDIUM confidence)
- [Streamlit session state documentation](https://docs.streamlit.io/develop/concepts/architecture/session-state) - Rerun behavior, state persistence
- [Streamlit file organization best practices](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/file-organization) - Directory structure, working directory on Community Cloud
- [How to improve Streamlit app loading speed](https://blog.streamlit.io/how-to-improve-streamlit-app-loading-speed-f091dc3e2861) - Performance optimization, caching strategies
- [Streamlit security reminders](https://docs.streamlit.io/develop/concepts/connections/security-reminders) - Pickle security warnings
- [streamlit-plotly-events PyPI](https://pypi.org/project/streamlit-plotly-events/) - Version 0.0.6, maintenance status (inactive)
- [streamlit-plotly-events2 PyPI](https://pypi.org/project/streamlit-plotly-events2/) - Version 0.0.7, fork with 2024 updates
- [Streamlit project structure discussion](https://discuss.streamlit.io/t/streamlit-project-folder-structure-for-medium-sized-apps/5272) - Community best practices
- [Plotly vs graph_objects comparison](https://plotly.com/python/graph-objects/) - When to use Express vs low-level API

### Tertiary (LOW confidence)
- [Common Streamlit app problems: Resource limits](https://blog.streamlit.io/common-app-problems-resource-limits/) - RAM limits discussion (2021, may be outdated)
- [Streamlit Community Cloud free tier limits](https://www.genspark.ai/spark/streamlit-cloud-free-plan-limits/fbebd1b2-b000-4d29-a4d1-c689e65c38fa) - Community-reported limits (not official)
- [Pros and cons of Streamlit](https://softwaremill.com/pros-and-cons-of-using-streamlit-for-simple-demo-apps/) - Scalability and customization limitations

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - Streamlit/Plotly/pandas are industry-standard Python data app tools; all in existing requirements.txt
- Architecture: HIGH - Official docs verify all patterns (st.cache_data, st.set_page_config, px.scatter); deployment process well-documented
- Pitfalls: MEDIUM-HIGH - Resource limits not officially documented with exact numbers; pickle security verified in official docs; requirements.txt location verified

**Research date:** 2026-02-14
**Valid until:** 2026-03-16 (30 days - Streamlit releases monthly but breaking changes rare; Plotly stable)
