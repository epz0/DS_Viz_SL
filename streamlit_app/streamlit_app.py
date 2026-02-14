"""
Design Space Visualization - Streamlit App
Phase 1: Minimal prototype with cached data loading and scatter plot
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import json
from pathlib import Path

# MUST be first Streamlit command
st.set_page_config(
    page_title="Design Space Visualization",
    layout="wide",
    initial_sidebar_state="auto"
)

# Data directory relative to this file
DATA_DIR = Path(__file__).parent / 'data'


@st.cache_data
def load_solutions():
    """Load solutions DataFrame from parquet.

    Returns:
        pd.DataFrame: All 563 solutions with 117 columns including:
            - x_emb, y_emb: UMAP coordinates
            - HEX-Win: Per-participant hex colors
            - clust_symb: Per-cluster plotly symbol names
            - hovertxt: Pre-formatted HTML hover text
    """
    return pd.read_parquet(DATA_DIR / 'df_base.parquet')


@st.cache_data
def load_metadata():
    """Load participant colors, cluster symbols, and IDs.

    Returns:
        dict: Metadata with participant_ids, color_mapping, cluster_symbols
    """
    with open(DATA_DIR / 'metadata.json', 'r') as f:
        return json.load(f)


# Main app
st.title("Design Space Visualization")

# Load data (cached, runs once)
df = load_solutions()
metadata = load_metadata()

# Initialize session state for click handling
if 'selected_point_idx' not in st.session_state:
    st.session_state.selected_point_idx = None

# Sidebar: Filters and Visibility Controls
with st.sidebar:
    st.header("Filters")

    # Participant multiselect -- use OriginalID_PT (unmasked), NOT ParticipantID (masked)
    # Default: all participants selected so chart is fully populated on first load
    all_participants = metadata['participant_ids']  # 31 entries including GALL
    selected_participants = st.multiselect(
        "Participants",
        options=all_participants,
        default=all_participants,
        help="Filter scatter plot to show only selected participants",
        key='participant_filter'
    )

    st.divider()
    st.header("Display")

    # Element visibility toggles
    show_points = st.checkbox(
        "Points",
        value=True,
        help="Show/hide solution scatter points",
        key='show_points'
    )
    show_arrows = st.checkbox(
        "Arrows",
        value=True,
        help="Exploration sequence arrows (coming in Phase 5)",
        key='show_arrows',
        disabled=True  # Not implemented until Phase 5
    )
    show_areas = st.checkbox(
        "Areas",
        value=True,
        help="Convex hull areas (coming in Phase 5)",
        key='show_areas',
        disabled=True  # Not implemented until Phase 5
    )

# Filter data by selected participants
df_filtered = df[df['OriginalID_PT'].isin(selected_participants)]

# Handle empty filter state
if df_filtered.empty:
    st.warning("No data matches current filters. Select at least one participant.")
    st.stop()  # Halt execution -- no chart or detail panel to show

# Clear selection when filtering removes the selected point
if st.session_state.selected_point_idx is not None:
    if st.session_state.selected_point_idx not in df_filtered.index:
        st.session_state.selected_point_idx = None

# Create scatter plot using plotly.graph_objects
# The original Dash app uses go.Scatter with per-point color/symbol arrays.
# This is critical because:
# - 31 participants would create an unreadable legend with px.scatter
# - The original app has showlegend=False
# - Per-point HEX-Win colors already encode participant identity
# - Per-point clust_symb already maps cluster to symbol names

# Build per-point marker arrays based on selection state
# Selected point gets dramatic visual treatment: size 18, square-x-open, black border
# Unselected points: size 8, original symbols, no border
# After filtering, iterate over df_filtered rows (which preserves original index)
selected_idx = st.session_state.selected_point_idx

marker_sizes = []
marker_symbols = []
marker_line_widths = []
marker_line_colors = []

for orig_idx, row in df_filtered.iterrows():
    if orig_idx == selected_idx:
        marker_sizes.append(18)
        marker_symbols.append('square-x-open')
        marker_line_widths.append(2)
        marker_line_colors.append('black')
    else:
        marker_sizes.append(8)
        marker_symbols.append(row['clust_symb'])
        marker_line_widths.append(0)
        marker_line_colors.append(row['HEX-Win'])

# Store mapping from filtered position to original DataFrame index
# (needed for click handling even when points are hidden)
filtered_to_original = df_filtered.index.tolist()

fig = go.Figure()

# Conditionally render scatter trace based on show_points checkbox
if show_points:
    fig.add_trace(go.Scatter(
        x=df_filtered['x_emb'],
        y=df_filtered['y_emb'],
        mode='markers',
        hovertemplate=df_filtered['hovertxt'].tolist(),
        marker=dict(
            size=marker_sizes,
            color=df_filtered['HEX-Win'].tolist(),
            symbol=marker_symbols,
            line=dict(
                width=marker_line_widths,
                color=marker_line_colors
            ),
        ),
        customdata=filtered_to_original,  # Original DataFrame integer index for click mapping
        name='',
    ))
else:
    # Show info message when points are hidden
    st.info("No elements visible. Enable Points in the sidebar.")

# Update layout
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

# Two-column layout: chart on left, detail panel on right
col_chart, col_detail = st.columns([2, 1])

with col_chart:
    event = st.plotly_chart(
        fig,
        use_container_width=True,
        on_select="rerun",
        selection_mode=["points"],
        key="scatter",
    )

    # Handle click/selection events from native Streamlit API
    # pointIndex is position in filtered trace, map to original DataFrame index
    if show_points and event and event.selection and event.selection.point_indices:
        clicked_filtered_pos = event.selection.point_indices[0]
        # Map filtered position to original DataFrame index
        clicked_original_idx = filtered_to_original[clicked_filtered_pos]
        if clicked_original_idx != st.session_state.selected_point_idx:
            st.session_state.selected_point_idx = clicked_original_idx
            st.rerun()

    # Status caption showing filter state
    st.caption(
        f"Showing {len(df_filtered):,} of {len(df):,} solutions "
        f"from {len(selected_participants)} of {len(all_participants)} participants"
    )

with col_detail:
    if st.session_state.selected_point_idx is not None:
        idx = st.session_state.selected_point_idx
        row = df.iloc[idx]

        # Section 1: Participant info (DETL-01)
        st.markdown(f"**Participant:** {row['OriginalID_PT']} | **Group:** {row['OriginalID_Group']} | **Phase:** {row['OriginalID_PrePost']} intervention")

        # Section 2: Solution header (DETL-02)
        sol_num = int(row['OriginalID_Sol']) if isinstance(row['OriginalID_Sol'], float) else row['OriginalID_Sol']
        st.subheader(f"Solution {sol_num}")

        # Section 3: Result, Cost, Max Stress (DETL-03)
        cost_str = f"${row['budgetUsed']:,}" if isinstance(row['budgetUsed'], (int, float)) else str(row['budgetUsed'])
        stress_str = f"{row['maxStress']:.1f}%" if isinstance(row['maxStress'], (int, float)) else str(row['maxStress'])
        st.markdown(f"**Result:** {row['result']} | **Cost:** {cost_str} | **Max Stress:** {stress_str}")

        # Section 4: Length, Nodes, Segments (DETL-04)
        # NOTE: Original Dash app maps NSegm->nodes and NJoint->segments (counterintuitive but must match)
        try:
            tlength = f"{float(row['TLength']):.1f}"
        except (ValueError, TypeError):
            tlength = str(row['TLength'])
        st.markdown(f"**Length:** {tlength}m | **Nodes:** {row['NSegm']} | **Segments:** {row['NJoint']}")

        # Section 5: Core Attributes (DETL-05)
        st.divider()
        st.markdown("##### Core Attributes")
        st.markdown(f"**Solution:** {row['ca_sol']}")
        st.markdown(f"**Deck:** {row['ca_deck']}")
        st.markdown(f"**Structure:** {row['ca_str']}")
        st.markdown(f"**Rock Support:** {row['ca_rck']}")
        st.markdown(f"**Materials:** {row['ca_mtr']}")

        # Section 6: Screenshot (DETL-06)
        st.divider()
        image_url = row['videoPreview']
        if image_url and str(image_url) != '-' and str(image_url) != 'nan':
            try:
                st.image(image_url, caption=f"Solution {row['OriginalID_Sol']}", use_container_width=True)
            except Exception:
                st.warning("Screenshot unavailable")
        else:
            st.info("No screenshot available for this solution")
    else:
        st.info("Click a point on the scatter plot to view solution details")
