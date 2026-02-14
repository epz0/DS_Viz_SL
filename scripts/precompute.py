#!/usr/bin/env python3
"""
Pre-computation pipeline for DS Viz SL project.

Extracts all heavy computation from the Dash app into a modular CLI pipeline
that produces cached data files for the Streamlit app to load.

Usage:
    python scripts/precompute.py all [--force]     # Run full pipeline
    python scripts/precompute.py read [--force]    # Read Excel data
    python scripts/precompute.py distance [--force] # Compute distance matrix
    python scripts/precompute.py umap [--force]     # Generate UMAP embedding
    python scripts/precompute.py unmask [--force]   # Unmask participant data
    python scripts/precompute.py features [--force] # Add computed features
    python scripts/precompute.py metrics [--force]  # Compute distance/area metrics
    python scripts/precompute.py clusters [--force] # Run clustering
    python scripts/precompute.py novelty [--force]  # Compute novelty metrics
    python scripts/precompute.py hulls [--force]    # Generate convex hulls
    python scripts/precompute.py validate          # Validate all outputs
"""

import sys
import argparse
import logging
import pickle
import json
from pathlib import Path
from datetime import datetime
import numpy as np
import pandas as pd
import shapely.geometry

# Add project root to sys.path for imports to work regardless of cwd
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Now we can import from scripts modules
from scripts.design_space.read_data import read_analysis
from scripts.design_space.dist_matrix import calc_distmatrix, create_dmatrix_from_embed
from scripts.design_space.dim_reduction import create_embedding
from scripts.design_space.dspace_dist_metrics import dist_metrics_fs, dist_metrics_pre, dist_metrics_post
from scripts.design_space.design_space import create_cvxh
from scripts.design_space.dspace_metrics import area_summary
from scripts.design_space.dspace_metric_novelty import novelty_from_density, novelty_from_neig
from scripts.design_space.dspace_viz_density import prep_density
from scripts.design_space.dspace_cluster import get_clusters
from scripts.utils.utils import unmask_data, solutions_summary, cv_hull_vertices

# Path configuration
DATA_DIR = PROJECT_ROOT / 'data'
OUTPUT_DIR = PROJECT_ROOT / 'streamlit_app' / 'data'
INTERMEDIATE_DIR = OUTPUT_DIR / 'intermediate'

# Data configuration
FILENAME = 'MASKED_DATA_analysis_v2.xlsx'
SHEET = 'ExpData-100R-Expanded'

# UMAP parameters (from interactive_tool.py line 48, but using production values)
UMAP_NN = 115
UMAP_MD = 0.15
UMAP_DENSM = 2

# Clustering resolution (standard value)
CLUSTER_RESOLUTION = 0.05

# Novelty delta (from interactive_tool.py line 188)
NOVELTY_DELTA = 0.9

# Setup logging
logger = logging.getLogger(__name__)


def step_read(force=False):
    """Step 1: Read Excel data and save base dataframes."""
    output_base = INTERMEDIATE_DIR / 'df_read.pkl'
    output_colors = INTERMEDIATE_DIR / 'df_colors.pkl'

    if output_base.exists() and output_colors.exists() and not force:
        logger.info(f"Step read: Output exists, loading from {output_base}")
        with open(output_base, 'rb') as f:
            df_base = pickle.load(f)
        with open(output_colors, 'rb') as f:
            df_colors = pickle.load(f)
        # Labels not saved separately, reconstruct from df_base
        labels = None
        return df_base, df_colors, labels

    if force:
        logger.info("Step read: --force specified, recomputing")

    logger.info(f"Step read: Reading {FILENAME} from {DATA_DIR}")
    df_base, df_colors, labels = read_analysis(DATA_DIR, FILENAME, sheetname=SHEET)

    logger.info(f"Step read: Saving outputs to {INTERMEDIATE_DIR}")
    with open(output_base, 'wb') as f:
        pickle.dump(df_base, f, protocol=5)
    with open(output_colors, 'wb') as f:
        pickle.dump(df_colors, f, protocol=5)

    logger.info(f"Step read: Complete ({len(df_base)} rows)")
    return df_base, df_colors, labels


def step_distance(df_base=None, force=False):
    """Step 2: Compute distance matrix."""
    output_file = INTERMEDIATE_DIR / 'n_distmatrix.npy'

    if output_file.exists() and not force:
        logger.info(f"Step distance: Output exists, loading from {output_file}")
        n_distmatrix = np.load(output_file)
        return n_distmatrix

    if force:
        logger.info("Step distance: --force specified, recomputing")

    if df_base is None:
        logger.info("Step distance: Loading prerequisite from step_read")
        df_base, _, _ = step_read()

    logger.info("Step distance: Computing distance matrix")
    n_distmatrix = calc_distmatrix(df_base, DATA_DIR, FILENAME)

    logger.info(f"Step distance: Saving to {output_file}")
    np.save(output_file, n_distmatrix)

    logger.info(f"Step distance: Complete (shape {n_distmatrix.shape})")
    return n_distmatrix


def step_umap(n_distmatrix=None, force=False):
    """Step 3: Generate UMAP embedding."""
    output_embedding = INTERMEDIATE_DIR / 'embedding.npy'
    output_graph = INTERMEDIATE_DIR / 'graph.pkl'

    if output_embedding.exists() and output_graph.exists() and not force:
        logger.info(f"Step umap: Output exists, loading from {output_embedding}")
        embedding = np.load(output_embedding)
        with open(output_graph, 'rb') as f:
            graph = pickle.load(f)
        return embedding, graph

    if force:
        logger.info("Step umap: --force specified, recomputing")

    if n_distmatrix is None:
        logger.info("Step umap: Loading prerequisite from step_distance")
        n_distmatrix = step_distance()

    logger.info(f"Step umap: Creating embedding (NN={UMAP_NN}, MD={UMAP_MD}, densm={UMAP_DENSM})")
    embedding, graph = create_embedding(
        DATA_DIR, n_distmatrix,
        embed_name='precompute',
        Wg='W2',
        NN=UMAP_NN,
        MD=UMAP_MD,
        densm=UMAP_DENSM
    )

    logger.info(f"Step umap: Saving to {INTERMEDIATE_DIR}")
    np.save(output_embedding, embedding)
    with open(output_graph, 'wb') as f:
        pickle.dump(graph, f, protocol=5)

    logger.info(f"Step umap: Complete (embedding shape {embedding.shape})")
    return embedding, graph


def step_unmask(df_base=None, df_colors=None, force=False):
    """Step 4: Unmask participant data."""
    output_base = INTERMEDIATE_DIR / 'df_unmask.pkl'
    output_colors = INTERMEDIATE_DIR / 'df_colors_unmask.pkl'

    if output_base.exists() and output_colors.exists() and not force:
        logger.info(f"Step unmask: Output exists, loading from {output_base}")
        with open(output_base, 'rb') as f:
            df_base = pickle.load(f)
        with open(output_colors, 'rb') as f:
            df_colors = pickle.load(f)
        return df_base, df_colors

    if force:
        logger.info("Step unmask: --force specified, recomputing")

    if df_base is None or df_colors is None:
        logger.info("Step unmask: Loading prerequisites from step_read")
        df_base, df_colors, _ = step_read()

    logger.info("Step unmask: Unmasking participant data")
    df_base, df_colors = unmask_data(DATA_DIR, 'MASKING_KEYS', df_base, df_colors)

    logger.info(f"Step unmask: Saving to {INTERMEDIATE_DIR}")
    with open(output_base, 'wb') as f:
        pickle.dump(df_base, f, protocol=5)
    with open(output_colors, 'wb') as f:
        pickle.dump(df_colors, f, protocol=5)

    logger.info("Step unmask: Complete")
    return df_base, df_colors


def step_features(df_base=None, df_colors=None, embedding=None, force=False):
    """Step 5: Add computed features (embedding coords, core attributes, solution summary)."""
    output_file = INTERMEDIATE_DIR / 'df_features.pkl'

    if output_file.exists() and not force:
        logger.info(f"Step features: Output exists, loading from {output_file}")
        with open(output_file, 'rb') as f:
            df_base = pickle.load(f)
        return df_base

    if force:
        logger.info("Step features: --force specified, recomputing")

    if df_base is None or df_colors is None:
        logger.info("Step features: Loading prerequisites from step_unmask")
        df_base, df_colors = step_unmask()

    if embedding is None:
        logger.info("Step features: Loading embedding from step_umap")
        embedding, _ = step_umap()

    logger.info("Step features: Adding embedding coordinates")
    df_base['x_emb'] = embedding[:, 0]
    df_base['y_emb'] = embedding[:, 1]

    logger.info("Step features: Merging color data")
    df_col = df_colors[['P', 'HEX-Win']].copy()
    df_base = df_base.merge(df_col, left_on='ParticipantID', right_on='P').copy()

    logger.info("Step features: Handling NaN values for gallery solutions")
    df_base['OriginalID_PT'] = df_base.apply(
        lambda row: row.OriginalID_PT if str(row.OriginalID_PT) != 'nan' else 'GALL',
        axis=1
    )
    df_base['OriginalID_Group'] = df_base.apply(
        lambda row: row.OriginalID_Group if str(row.OriginalID_Group) != 'nan' else 'GALL',
        axis=1
    )
    df_base['OriginalID_Sol'] = df_base.apply(
        lambda row: row.OriginalID_Sol if str(row.OriginalID_Sol) != 'nan' else row.SolutionID,
        axis=1
    )
    df_base['OriginalID_PrePost'] = df_base.apply(
        lambda row: row.OriginalID_PrePost if str(row.OriginalID_PrePost) != 'nan' else 'GALL',
        axis=1
    )

    logger.info("Step features: Computing core attributes")
    # Solution
    df_base['ca_sol'] = df_base.apply(
        lambda row: row.type + ' | ' + str(row.numAnchorsUsed) + ' anchors',
        axis=1
    )

    # Deck
    df_base['ca_deck'] = df_base.apply(
        lambda row: (
            row.deckType_2 + ' | shape: ' + row.deckShape_1 + ' ' + row.deckShape_2 +
            ' ' + row.deckShape_3 + ' ' + row.deckShape_4
            if row.deckType_2 == 'fully_connected' else
            row.deckType_1 + ' ' + row.deckType_2 + ' | shape: ' + row.deckShape_1 +
            ' ' + row.deckShape_2 + ' ' + row.deckShape_3 + ' ' + row.deckShape_4
        ),
        axis=1
    ).str.replace(' -', '')

    # Structure
    df_base['ca_str'] = df_base.apply(
        lambda row: (
            row.structurePosition_Top + ' ' + row.structurePosition_Rock +
            ' ' + row.structurePosition_Bottom + ' | shape: ' + row.structureShape_1 +
            ' ' + row.structureShape_2 + ' | size: ' + row.structureSize
        ),
        axis=1
    ).str.replace(' no_structure', '').str.replace('_structure', '').str.replace('-', '').str.replace('no ', '')

    # Rock support
    df_base['ca_rck'] = df_base.apply(
        lambda row: (
            row.rockSupportShape + ' | ' + row.rockSupportMat
            if row.rockSupportShape != 'no_support' else
            row.rockSupportShape
        ),
        axis=1
    )

    # Materials
    df_base['ca_road'] = df_base.apply(
        lambda row: 'road' if row.materialRoad == 'yes' else '-no-',
        axis=1
    )
    df_base['ca_rroad'] = df_base.apply(
        lambda row: 'reinforced road' if row.materialReinfRoad == 'yes' else '-no-',
        axis=1
    )
    df_base['ca_wood'] = df_base.apply(
        lambda row: 'wood' if row.materialWood == 'yes' else '-no-',
        axis=1
    )
    df_base['ca_steel'] = df_base.apply(
        lambda row: 'steel' if row.materialSteel == 'yes' else '-no-',
        axis=1
    )
    df_base['ca_mtr'] = df_base.apply(
        lambda row: (
            row.ca_road + ' ' + row.ca_rroad + ' ' + row.ca_wood + ' ' + row.ca_steel
        ),
        axis=1
    ).str.replace('-no- ', '').str.replace(' -no-', '')

    # Performance
    df_base['ca_perf'] = df_base.apply(
        lambda row: 0 if row.result == 'fail' else 1,
        axis=1
    )
    df_base['performance'] = df_base.apply(
        lambda row: row.ca_perf * (15000 / row.budgetUsed),
        axis=1
    )

    # Full ID
    df_base['fullid_orig'] = df_base.apply(
        lambda row: row.OriginalID_PT + '-' + row.OriginalID_PrePost + '-' + str(row.OriginalID_Sol),
        axis=1
    ).str.replace('.0', '')

    logger.info("Step features: Merging solution summary")
    save_dir = DATA_DIR / 'json'
    df_sol = solutions_summary(save_dir, saveExcel=False)
    df_base = df_base.merge(df_sol, how='left', on='fullid_orig')

    # Handle NaN for solution summary fields
    df_base['TLength'] = df_base.apply(
        lambda row: row.TLength if str(row.TLength) != 'nan' else 'N/A',
        axis=1
    )
    df_base['NSegm'] = df_base.apply(
        lambda row: row.NSegm if str(row.NSegm) != 'nan' else 'N/A',
        axis=1
    )
    df_base['NJoint'] = df_base.apply(
        lambda row: row.NJoint if str(row.NJoint) != 'nan' else 'N/A',
        axis=1
    )

    logger.info(f"Step features: Saving to {output_file}")
    with open(output_file, 'wb') as f:
        pickle.dump(df_base, f, protocol=5)

    logger.info("Step features: Complete")
    return df_base


def step_metrics(df_base=None, embedding=None, force=False):
    """Step 6: Compute distance and area metrics."""
    output_metrics = INTERMEDIATE_DIR / 'df_metrics.pkl'
    output_ds_area = INTERMEDIATE_DIR / 'ds_area.json'

    if output_metrics.exists() and output_ds_area.exists() and not force:
        logger.info(f"Step metrics: Output exists, loading from {output_metrics}")
        with open(output_metrics, 'rb') as f:
            df_base = pickle.load(f)
        with open(output_ds_area, 'r') as f:
            ds_area_data = json.load(f)
        return df_base, ds_area_data['DS_area']

    if force:
        logger.info("Step metrics: --force specified, recomputing")

    if df_base is None:
        logger.info("Step metrics: Loading prerequisites from step_features")
        df_base = step_features()

    if embedding is None:
        logger.info("Step metrics: Loading embedding from step_umap")
        embedding, _ = step_umap()

    logger.info("Step metrics: Computing distance metrics from embedding")
    n_distmatrix_emb = create_dmatrix_from_embed(DATA_DIR, embedding, norm=False)

    df_dist_emb, pt_unq = dist_metrics_fs(df_base, n_distmatrix_emb)
    df_dist_emb = dist_metrics_pre(df_base, df_dist_emb, pt_unq, n_distmatrix_emb)
    df_dist_emb = dist_metrics_post(df_base, df_dist_emb, pt_unq, n_distmatrix_emb)

    df_dist_emb = df_dist_emb.drop(columns=[
        'OriginalID_Group', 'maxdist_FS', 'maxdist_PRE', 'maxdist_PST',
        'dist_PRE_POST', 'avgdist_FS', 'avgdist_PRE', 'avgdist_PST'
    ])

    df_base = df_base.merge(df_dist_emb, how='left', on='OriginalID_PT')

    # Handle NaN for distance metrics
    nan_cols = df_dist_emb.columns[1:].tolist()
    for col in nan_cols:
        df_base[col] = df_base.apply(
            lambda row: row[col] if str(row[col]) != 'nan' else 'N/A',
            axis=1
        )

    logger.info("Step metrics: Computing area metrics from convex hulls")
    # Need to reload df_colors for create_cvxh
    with open(INTERMEDIATE_DIR / 'df_colors_unmask.pkl', 'rb') as f:
        df_colors = pickle.load(f)

    DS_area, pt_cvxh, df_metrics_fs, df_metrics_pre, df_metrics_post, df_ds_verts = create_cvxh(
        DATA_DIR, df_base, embedding, df_colors, save_plot=False
    )

    mode_metrics = 'all'
    df_DS_coverage = area_summary(
        df_base, DS_area, df_metrics_fs,
        mode=mode_metrics,
        df_ch_pre_metrics=df_metrics_pre,
        df_ch_post_metrics=df_metrics_post
    )
    df_DS_coverage = df_DS_coverage.drop(columns=['GroupID', 'Area-KYY', 'Area-ZSB', 'Area-FS'])

    df_base = df_base.merge(df_DS_coverage, how='left', on='ParticipantID')
    df_base = df_base.rename(columns={
        'Area-Perc-KYY': 'Area-Perc-PRE',
        'Area-Perc-ZSB': 'Area-Perc-POST'
    })

    # Handle NaN for area metrics
    df_base['Area-Perc-PRE'] = df_base.apply(
        lambda row: row['Area-Perc-PRE'] if str(row['Area-Perc-PRE']) != 'nan' else 'N/A',
        axis=1
    )
    df_base['Area-Perc-POST'] = df_base.apply(
        lambda row: row['Area-Perc-POST'] if str(row['Area-Perc-POST']) != 'nan' else 'N/A',
        axis=1
    )
    df_base['Area-Perc-FS'] = df_base.apply(
        lambda row: row['Area-Perc-FS'] if str(row['Area-Perc-FS']) != 'nan' else 'N/A',
        axis=1
    )

    logger.info(f"Step metrics: Saving to {INTERMEDIATE_DIR}")
    with open(output_metrics, 'wb') as f:
        pickle.dump(df_base, f, protocol=5)

    with open(output_ds_area, 'w') as f:
        json.dump({'DS_area': float(DS_area)}, f)

    logger.info(f"Step metrics: Complete (DS_area={DS_area:.2f})")
    return df_base, DS_area


def step_clusters(df_base=None, graph=None, force=False):
    """Step 7: Compute Leiden clustering and cluster summary."""
    output_file = INTERMEDIATE_DIR / 'df_clusters.pkl'

    if output_file.exists() and not force:
        logger.info(f"Step clusters: Output exists, loading from {output_file}")
        with open(output_file, 'rb') as f:
            df_base = pickle.load(f)
        return df_base

    if force:
        logger.info("Step clusters: --force specified, recomputing")

    if df_base is None:
        logger.info("Step clusters: Loading prerequisites from step_metrics")
        df_base, _ = step_metrics()

    if graph is None:
        logger.info("Step clusters: Loading graph from step_umap")
        _, graph = step_umap()

    logger.info("Step clusters: Running Leiden clustering")
    df_base = get_clusters(df_base, graph)

    logger.info("Step clusters: Adding cluster symbols")
    symb = list(range(1, 17))
    symb_ls = [
        'circle', 'diamond', 'cross', 'x', 'pentagon',
        'hexagon', 'star', 'hexagram', 'star-triangle-up',
        'star-triangle-down', 'star-square', 'star-diamond', 'diamond-tall',
        'diamond-wide', 'circle-open', 'square'
    ]
    df_symb = pd.DataFrame({'cluster_id': symb, 'clust_symb': symb_ls})
    df_base = df_base.merge(df_symb, how='left', on='cluster_id')

    logger.info("Step clusters: Computing per-participant cluster counts")
    ids = sorted(list(df_base['OriginalID_PT'].unique()))

    tot_clust = []
    pre_clust = []
    post_clust = []
    for pt in ids[1:]:  # Skip 'GALL'
        tot_clust.append(len(df_base[df_base['OriginalID_PT'] == pt]['cluster_id'].unique()))
        pre_clust.append(len(df_base[
            (df_base['OriginalID_PT'] == pt) &
            (df_base['OriginalID_PrePost'] == 'Pre')
        ]['cluster_id'].unique()))
        post_clust.append(len(df_base[
            (df_base['OriginalID_PT'] == pt) &
            (df_base['OriginalID_PrePost'] == 'Pst')
        ]['cluster_id'].unique()))

    df_clust_summ = pd.DataFrame({
        'OriginalID_PT': ids[1:],
        'n_clusters': tot_clust,
        'n_clusters_pre': pre_clust,
        'n_clusters_post': post_clust
    })

    df_base = df_base.merge(df_clust_summ, how='left', on='OriginalID_PT')

    logger.info("Step clusters: Creating hover text")
    df_base['hovertxt'] = df_base.apply(
        lambda row: (
            f"<b>{row['OriginalID_PT']} | Sol. {row['OriginalID_Sol']}</b><br>"
            f"{row['OriginalID_PrePost']} | {row['result']}"
        ),
        axis=1
    ).str.replace('.0', '')

    logger.info(f"Step clusters: Saving to {output_file}")
    with open(output_file, 'wb') as f:
        pickle.dump(df_base, f, protocol=5)

    logger.info(f"Step clusters: Complete ({len(df_base['cluster_id'].unique())} clusters)")
    return df_base


def step_novelty(df_base=None, embedding=None, force=False):
    """Step 8: Compute novelty metrics from density and neighbors."""
    output_file = INTERMEDIATE_DIR / 'df_novelty.pkl'

    if output_file.exists() and not force:
        logger.info(f"Step novelty: Output exists, loading from {output_file}")
        with open(output_file, 'rb') as f:
            df_base = pickle.load(f)
        return df_base

    if force:
        logger.info("Step novelty: --force specified, recomputing")

    if df_base is None:
        logger.info("Step novelty: Loading prerequisites from step_clusters")
        df_base = step_clusters()

    if embedding is None:
        logger.info("Step novelty: Loading embedding from step_umap")
        embedding, _ = step_umap()

    logger.info("Step novelty: Computing density-based novelty")
    df_kde, lim_x, lim_y = prep_density(df_base, embedding)

    df_novel = novelty_from_density(
        DATA_DIR, df_kde, lim_x, lim_y,
        prt_integral=False,
        save_metrics=False
    )
    df_novel = df_novel.drop(columns=[
        'GroupID', 'ParticipantID', 'PrePost',
        'result', 'type', 'x_emb', 'y_emb'
    ])

    df_base = df_base.merge(df_novel, how='left', on='FullID')

    logger.info(f"Step novelty: Computing neighbor-based novelty (delta={NOVELTY_DELTA})")
    novel_nn = novelty_from_neig(DATA_DIR, df_base, embedding, delta=NOVELTY_DELTA)
    novel_nn = novel_nn.drop(columns=[
        'GroupID', 'ParticipantID', 'PrePost',
        'result', 'type', 'x_emb', 'y_emb'
    ])

    df_base = df_base.merge(novel_nn, how='left', on='FullID')

    logger.info(f"Step novelty: Saving to {output_file}")
    with open(output_file, 'wb') as f:
        pickle.dump(df_base, f, protocol=5)

    logger.info("Step novelty: Complete")
    return df_base


def step_hulls(df_base=None, force=False):
    """Step 9: Generate convex hull vertices for each participant and full DS."""
    output_file = OUTPUT_DIR / 'convex_hulls.pkl'

    if output_file.exists() and not force:
        logger.info(f"Step hulls: Output exists, loading from {output_file}")
        with open(output_file, 'rb') as f:
            hulls = pickle.load(f)
        return hulls

    if force:
        logger.info("Step hulls: --force specified, recomputing")

    if df_base is None:
        logger.info("Step hulls: Loading prerequisites from step_novelty")
        df_base = step_novelty()

    logger.info("Step hulls: Computing convex hull for full design space")
    fullds_xvt, fullds_yvt, cvarea = cv_hull_vertices(
        x=df_base['x_emb'],
        y=df_base['y_emb']
    )

    hulls = {
        'full_ds': {
            'x': fullds_xvt.tolist() if hasattr(fullds_xvt, 'tolist') else list(fullds_xvt),
            'y': fullds_yvt.tolist() if hasattr(fullds_yvt, 'tolist') else list(fullds_yvt),
            'area': float(cvarea)
        }
    }

    logger.info("Step hulls: Computing per-participant convex hulls")
    ids = sorted(list(df_base['OriginalID_PT'].unique()))

    for pt in ids:
        x_vals = list(df_base[df_base['OriginalID_PT'] == pt]['x_emb'])
        y_vals = list(df_base[df_base['OriginalID_PT'] == pt]['y_emb'])

        # Use shapely as in interactive_tool.py lines 260-261
        cvh_vtx = np.array(
            shapely.geometry.MultiPoint(
                [xy for xy in zip(x_vals, y_vals)]
            ).convex_hull.exterior.coords
        )

        # Calculate area using the vertices
        if len(cvh_vtx) > 2:
            from scipy.spatial import ConvexHull
            try:
                hull = ConvexHull(cvh_vtx)
                area = hull.volume  # In 2D, volume = area
            except:
                area = 0.0
        else:
            area = 0.0

        hulls[pt] = {
            'x': cvh_vtx[:, 0].tolist(),
            'y': cvh_vtx[:, 1].tolist(),
            'area': float(area)
        }

    logger.info(f"Step hulls: Saving to {output_file}")
    with open(output_file, 'wb') as f:
        pickle.dump(hulls, f, protocol=5)

    logger.info(f"Step hulls: Complete ({len(hulls)} hulls)")
    return hulls


def step_save_final(df_base=None, force=False):
    """Step 10: Save final outputs (parquet, metadata, manifest)."""
    output_parquet = OUTPUT_DIR / 'df_base.parquet'
    output_metadata = OUTPUT_DIR / 'metadata.json'
    output_manifest = OUTPUT_DIR / 'manifest.json'

    if (output_parquet.exists() or (OUTPUT_DIR / 'df_base.pkl').exists()) and \
       output_metadata.exists() and output_manifest.exists() and not force:
        logger.info(f"Step save_final: Outputs exist, skipping")
        return

    if force:
        logger.info("Step save_final: --force specified, recomputing")

    if df_base is None:
        logger.info("Step save_final: Loading final dataframe from step_novelty")
        df_base = step_novelty()

    logger.info("Step save_final: Saving final dataframe")
    # Try parquet first, fall back to pickle if there are type issues
    try:
        # Convert any list/dict columns to JSON strings for parquet compatibility
        df_save = df_base.copy()
        for col in df_save.columns:
            if df_save[col].dtype == 'object':
                # Check if column contains lists or dicts
                sample = df_save[col].dropna().head(1)
                if len(sample) > 0:
                    val = sample.iloc[0]
                    if isinstance(val, (list, dict)):
                        df_save[col] = df_save[col].apply(lambda x: json.dumps(x) if pd.notna(x) else None)

        df_save.to_parquet(output_parquet, index=False)
        logger.info(f"Saved to {output_parquet}")
    except Exception as e:
        logger.warning(f"Failed to save as parquet ({e}), falling back to pickle")
        output_pickle = OUTPUT_DIR / 'df_base.pkl'
        with open(output_pickle, 'wb') as f:
            pickle.dump(df_base, f, protocol=5)
        logger.info(f"Saved to {output_pickle}")

    logger.info("Step save_final: Creating metadata")
    # Get color mapping
    with open(INTERMEDIATE_DIR / 'df_colors_unmask.pkl', 'rb') as f:
        df_colors = pickle.load(f)

    ids = sorted(list(df_base['OriginalID_PT'].unique()))
    color_map = {}
    for pt_id in ids:
        pt_data = df_base[df_base['OriginalID_PT'] == pt_id]
        if len(pt_data) > 0:
            color_map[pt_id] = pt_data.iloc[0]['HEX-Win']

    # Get DS area
    with open(INTERMEDIATE_DIR / 'ds_area.json', 'r') as f:
        ds_area_data = json.load(f)

    # Get cluster symbols
    symb = list(range(1, 17))
    symb_ls = [
        'circle', 'diamond', 'cross', 'x', 'pentagon',
        'hexagon', 'star', 'hexagram', 'star-triangle-up',
        'star-triangle-down', 'star-square', 'star-diamond', 'diamond-tall',
        'diamond-wide', 'circle-open', 'square'
    ]
    cluster_symbols = dict(zip(symb, symb_ls))

    metadata = {
        'participant_ids': ids,
        'color_mapping': color_map,
        'ds_area': ds_area_data['DS_area'],
        'cluster_symbols': cluster_symbols,
        'ids_list': ids
    }

    with open(output_metadata, 'w') as f:
        json.dump(metadata, f, indent=2)
    logger.info(f"Saved to {output_metadata}")

    logger.info("Step save_final: Creating manifest")
    manifest = {
        'timestamp': datetime.utcnow().isoformat() + 'Z',
        'source_file': FILENAME,
        'source_sheet': SHEET,
        'umap_params': {
            'NN': UMAP_NN,
            'MD': UMAP_MD,
            'densm': UMAP_DENSM
        },
        'cluster_resolution': CLUSTER_RESOLUTION,
        'novelty_delta': NOVELTY_DELTA,
        'output_files': [
            'df_base.parquet' if output_parquet.exists() else 'df_base.pkl',
            'metadata.json',
            'convex_hulls.pkl',
            'manifest.json'
        ]
    }

    with open(output_manifest, 'w') as f:
        json.dump(manifest, f, indent=2)
    logger.info(f"Saved to {output_manifest}")

    logger.info("Step save_final: Complete")


def step_validate():
    """Validate all outputs exist and have expected structure."""
    logger.info("Step validate: Checking all outputs")

    errors = []
    warnings = []

    # Check final outputs
    final_files = [
        OUTPUT_DIR / 'df_base.parquet',
        OUTPUT_DIR / 'df_base.pkl',  # Either parquet or pickle
        OUTPUT_DIR / 'metadata.json',
        OUTPUT_DIR / 'convex_hulls.pkl',
        OUTPUT_DIR / 'manifest.json'
    ]

    # At least one of parquet or pickle must exist
    if not (OUTPUT_DIR / 'df_base.parquet').exists() and not (OUTPUT_DIR / 'df_base.pkl').exists():
        errors.append("Missing df_base (neither parquet nor pkl exists)")

    for fpath in final_files[2:]:  # Skip df_base files (already checked)
        if not fpath.exists():
            errors.append(f"Missing {fpath.name}")

    # Check intermediate files
    intermediate_files = [
        'df_read.pkl', 'df_colors.pkl', 'n_distmatrix.npy',
        'embedding.npy', 'graph.pkl', 'df_unmask.pkl',
        'df_colors_unmask.pkl', 'df_features.pkl', 'df_metrics.pkl',
        'ds_area.json', 'df_clusters.pkl', 'df_novelty.pkl'
    ]

    for fname in intermediate_files:
        fpath = INTERMEDIATE_DIR / fname
        if not fpath.exists():
            warnings.append(f"Missing intermediate file: {fname}")

    # Validate df_base columns (all columns required by Streamlit app)
    if (OUTPUT_DIR / 'df_base.parquet').exists():
        try:
            df = pd.read_parquet(OUTPUT_DIR / 'df_base.parquet')

            # Required columns extracted from interactive_tool.py
            required_cols = [
                # Identity
                'FullID', 'ParticipantID', 'SolutionID', 'GroupID',
                # Embedding
                'x_emb', 'y_emb',
                # Original IDs (from unmask)
                'OriginalID_PT', 'OriginalID_Group', 'OriginalID_Sol', 'OriginalID_PrePost',
                # Result/cost
                'result', 'budgetUsed', 'maxStress',
                # Core attributes
                'ca_sol', 'ca_deck', 'ca_str', 'ca_rck', 'ca_mtr', 'ca_perf', 'performance',
                # Solution summary
                'TLength', 'NSegm', 'NJoint',
                # Visual
                'HEX-Win', 'hovertxt', 'clust_symb', 'videoPreview',
                # Full ID
                'fullid_orig',
                # Clustering
                'cluster_id', 'n_clusters', 'n_clusters_pre', 'n_clusters_post',
                # Distance metrics
                'totaldist_FS', 'totaldist_PRE', 'totaldist_PST',
                # Area metrics
                'Area-Perc-FS', 'Area-Perc-PRE', 'Area-Perc-POST',
                # Novelty
                'novel_nn', 'novelty_norm',
                # Design attributes (from original Excel)
                'type', 'numAnchorsUsed',
                'deckType_1', 'deckType_2',
                'deckShape_1', 'deckShape_2', 'deckShape_3', 'deckShape_4',
                'structurePosition_Top', 'structurePosition_Rock', 'structurePosition_Bottom',
                'structureShape_1', 'structureShape_2', 'structureSize',
                'rockSupportShape', 'rockSupportMat',
                'materialRoad', 'materialReinfRoad', 'materialWood', 'materialSteel'
            ]

            missing_cols = [col for col in required_cols if col not in df.columns]
            if missing_cols:
                errors.append(f"df_base.parquet missing {len(missing_cols)} required columns: {missing_cols[:10]}" +
                             (f" ... and {len(missing_cols)-10} more" if len(missing_cols) > 10 else ""))

            # Row count validation
            if len(df) == 0:
                errors.append("df_base.parquet has 0 rows")
            else:
                logger.info(f"df_base.parquet has {len(df)} rows and {len(df.columns)} columns")

        except Exception as e:
            errors.append(f"Failed to validate df_base.parquet: {e}")
    elif (OUTPUT_DIR / 'df_base.pkl').exists():
        # Also check pickle version if parquet doesn't exist
        try:
            df = pd.read_pickle(OUTPUT_DIR / 'df_base.pkl')

            # Same required columns check
            required_cols = [
                'FullID', 'ParticipantID', 'SolutionID', 'GroupID',
                'x_emb', 'y_emb',
                'OriginalID_PT', 'OriginalID_Group', 'OriginalID_Sol', 'OriginalID_PrePost',
                'result', 'budgetUsed', 'maxStress',
                'ca_sol', 'ca_deck', 'ca_str', 'ca_rck', 'ca_mtr', 'ca_perf', 'performance',
                'TLength', 'NSegm', 'NJoint',
                'HEX-Win', 'hovertxt', 'clust_symb', 'videoPreview',
                'fullid_orig',
                'cluster_id', 'n_clusters', 'n_clusters_pre', 'n_clusters_post',
                'totaldist_FS', 'totaldist_PRE', 'totaldist_PST',
                'Area-Perc-FS', 'Area-Perc-PRE', 'Area-Perc-POST',
                'novel_nn', 'novelty_norm',
                'type', 'numAnchorsUsed',
                'deckType_1', 'deckType_2',
                'deckShape_1', 'deckShape_2', 'deckShape_3', 'deckShape_4',
                'structurePosition_Top', 'structurePosition_Rock', 'structurePosition_Bottom',
                'structureShape_1', 'structureShape_2', 'structureSize',
                'rockSupportShape', 'rockSupportMat',
                'materialRoad', 'materialReinfRoad', 'materialWood', 'materialSteel'
            ]

            missing_cols = [col for col in required_cols if col not in df.columns]
            if missing_cols:
                errors.append(f"df_base.pkl missing {len(missing_cols)} required columns: {missing_cols[:10]}" +
                             (f" ... and {len(missing_cols)-10} more" if len(missing_cols) > 10 else ""))

            if len(df) == 0:
                errors.append("df_base.pkl has 0 rows")
            else:
                logger.info(f"df_base.pkl has {len(df)} rows and {len(df.columns)} columns")

        except Exception as e:
            errors.append(f"Failed to validate df_base.pkl: {e}")

    # Validate convex hulls
    if (OUTPUT_DIR / 'convex_hulls.pkl').exists():
        try:
            with open(OUTPUT_DIR / 'convex_hulls.pkl', 'rb') as f:
                hulls = pickle.load(f)

            if not isinstance(hulls, dict):
                errors.append("convex_hulls.pkl is not a dict")
            elif 'full_ds' not in hulls:
                errors.append("convex_hulls.pkl missing 'full_ds' key")
            else:
                # Check participant count (should be ~30+, there are 31 including gallery)
                participant_keys = [k for k in hulls.keys() if k != 'full_ds']
                if len(participant_keys) < 30:
                    warnings.append(f"convex_hulls.pkl has only {len(participant_keys)} participants (expected ~30+)")
                else:
                    logger.info(f"convex_hulls.pkl has {len(participant_keys)} participant hulls + full_ds")
        except Exception as e:
            errors.append(f"Failed to validate convex_hulls.pkl: {e}")

    # Validate content if files exist
    if (OUTPUT_DIR / 'metadata.json').exists():
        try:
            with open(OUTPUT_DIR / 'metadata.json', 'r') as f:
                metadata = json.load(f)

            required_keys = ['participant_ids', 'color_mapping', 'ds_area', 'cluster_symbols', 'ids_list']
            for key in required_keys:
                if key not in metadata:
                    errors.append(f"metadata.json missing key: {key}")

            # Additional checks
            if 'participant_ids' in metadata and not isinstance(metadata['participant_ids'], list):
                errors.append("metadata.json 'participant_ids' is not a list")
            elif 'participant_ids' in metadata and len(metadata['participant_ids']) == 0:
                errors.append("metadata.json 'participant_ids' is empty")

            if 'color_mapping' in metadata and not isinstance(metadata['color_mapping'], dict):
                errors.append("metadata.json 'color_mapping' is not a dict")
            elif 'color_mapping' in metadata and len(metadata['color_mapping']) == 0:
                errors.append("metadata.json 'color_mapping' is empty")

            if 'ds_area' in metadata and not isinstance(metadata['ds_area'], (int, float)):
                errors.append("metadata.json 'ds_area' is not a number")
            elif 'ds_area' in metadata and metadata['ds_area'] <= 0:
                errors.append("metadata.json 'ds_area' is not > 0")

        except Exception as e:
            errors.append(f"Failed to load metadata.json: {e}")

    if (OUTPUT_DIR / 'manifest.json').exists():
        try:
            with open(OUTPUT_DIR / 'manifest.json', 'r') as f:
                manifest = json.load(f)

            required_keys = ['timestamp', 'source_file', 'umap_params', 'output_files']
            for key in required_keys:
                if key not in manifest:
                    errors.append(f"manifest.json missing key: {key}")
        except Exception as e:
            errors.append(f"Failed to load manifest.json: {e}")

    # Report results
    if errors:
        logger.error(f"Validation FAILED with {len(errors)} error(s):")
        for err in errors:
            logger.error(f"  - {err}")
        raise ValueError("Validation failed")

    if warnings:
        logger.warning(f"Validation passed with {len(warnings)} warning(s):")
        for warn in warnings:
            logger.warning(f"  - {warn}")
    else:
        logger.info("Validation PASSED - all outputs present and valid")


def run_all_steps(force=False):
    """Run the full pipeline from read to validation."""
    logger.info("=" * 60)
    logger.info("Starting full pipeline")
    logger.info("=" * 60)

    # Run steps in order, passing data in memory
    df_base, df_colors, labels = step_read(force)
    n_distmatrix = step_distance(df_base, force)
    embedding, graph = step_umap(n_distmatrix, force)
    df_base, df_colors = step_unmask(df_base, df_colors, force)
    df_base = step_features(df_base, df_colors, embedding, force)
    df_base, ds_area = step_metrics(df_base, embedding, force)
    df_base = step_clusters(df_base, graph, force)
    df_base = step_novelty(df_base, embedding, force)
    hulls = step_hulls(df_base, force)
    step_save_final(df_base, force)

    logger.info("=" * 60)
    logger.info("Full pipeline complete, running validation")
    logger.info("=" * 60)

    step_validate()

    logger.info("=" * 60)
    logger.info("All steps complete!")
    logger.info("=" * 60)


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description='Pre-computation pipeline for DS Viz SL project',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )

    subparsers = parser.add_subparsers(dest='command', help='Pipeline step to run')

    # Add --force flag to all commands except validate
    for cmd in ['read', 'distance', 'umap', 'unmask', 'features', 'metrics', 'clusters', 'novelty', 'hulls', 'all']:
        subparser = subparsers.add_parser(cmd, help=f'Run {cmd} step')
        subparser.add_argument('--force', action='store_true',
                             help='Force recomputation even if output exists')

    # Validate command (no --force flag)
    subparsers.add_parser('validate', help='Validate all outputs')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Ensure output directories exist
    INTERMEDIATE_DIR.mkdir(parents=True, exist_ok=True)

    # Dispatch to appropriate step
    force = getattr(args, 'force', False)

    try:
        if args.command == 'read':
            step_read(force)
        elif args.command == 'distance':
            step_distance(force=force)
        elif args.command == 'umap':
            step_umap(force=force)
        elif args.command == 'unmask':
            step_unmask(force=force)
        elif args.command == 'features':
            step_features(force=force)
        elif args.command == 'metrics':
            step_metrics(force=force)
        elif args.command == 'clusters':
            step_clusters(force=force)
        elif args.command == 'novelty':
            step_novelty(force=force)
        elif args.command == 'hulls':
            step_hulls(force=force)
        elif args.command == 'validate':
            step_validate()
        elif args.command == 'all':
            run_all_steps(force)
        else:
            parser.print_help()

    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
