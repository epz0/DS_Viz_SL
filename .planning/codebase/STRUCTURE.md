# Structure

## Directory Layout

```
DS_Viz_SL/
├── __init__.py                          # Package root (empty)
├── Procfile                             # Heroku deployment: web: gunicorn ...
├── README.md                            # Project readme
├── requirements.txt                     # Python dependencies
├── runtime.txt                          # Python version (Heroku)
├── data/                                # Input data directory
│   ├── MASKED_DATA_analysis_v2.xlsx     # Main experimental data spreadsheet
│   └── json/                            # JSON exports from Dash app
├── scripts/                             # All source code
│   ├── __init__.py
│   ├── design_space/                    # Core analysis modules
│   │   ├── __init__.py
│   │   ├── read_data.py                 # Excel data reader
│   │   ├── dist_matrix.py              # Pairwise distance calculation
│   │   ├── dim_reduction.py            # UMAP dimensionality reduction
│   │   ├── design_space.py             # Convex hull computation (28KB)
│   │   ├── dspace_metrics.py           # Coverage & alternative metrics (15KB)
│   │   ├── dspace_dist_metrics.py      # Distance-based metrics
│   │   ├── dspace_metric_novelty.py    # Novelty metrics
│   │   ├── dspace_cluster.py           # Clustering via igraph
│   │   ├── dspace_viz_arrows.py        # Arrow exploration plots (25KB)
│   │   ├── dspace_viz_density.py       # KDE density plots (22KB)
│   │   └── dspace_viz_landscape.py     # Landscape visualization
│   ├── stats/                           # Statistical analysis (ANCOVA)
│   │   ├── __init__.py
│   │   ├── stats_main.py               # ANCOVA wrapper
│   │   ├── stats_mt1_fluency.py        # Fluency comparisons
│   │   ├── stats_mt2_variety.py        # Variety comparisons
│   │   └── stats_mt3_mt4_novelty.py    # Novelty comparisons
│   ├── utils/                           # Shared utilities
│   │   ├── __init__.py
│   │   ├── utils.py                     # Main utilities (82KB — largest file)
│   │   └── dataset.py                   # Dataset helpers
│   ├── validation/                      # Metric validation
│   │   ├── __init__.py
│   │   ├── validation_distmetric.py     # Distance metric validation (29KB)
│   │   ├── validation_areametric.py     # Area sensitivity validation
│   │   └── validation_viz.py            # Visualization validation
│   ├── experimental/                    # Experimental/prototype code
│   │   └── __init__.py
│   ├── interactive_tool.py              # Main Dash dashboard app
│   ├── interactive_tool_quant.py        # Quantitative Dash variant
│   ├── interactive_tool_rt.py           # Real-time Dash variant
│   ├── interactive_run.py               # Dash app launcher
│   ├── interactive_run_mp.py            # Multiprocessing Dash launcher
│   ├── test_run.py                      # Full pipeline test script
│   ├── stats_run.py                     # Statistics runner
│   ├── stats_run_mdsx.py               # Stats runner variant (MDSX)
│   ├── viz_run.py                       # Visualization runner
│   ├── validation_run.py               # Validation runner
│   ├── abstract_screenshots.py          # Screenshot utility
│   ├── convert_save.py                  # Data conversion utility
│   └── realtime.py                      # Real-time processing
├── export/                              # Generated output files
├── viz/                                 # Generated visualization images
├── validation/                          # Validation output files
├── experimental/                        # Experimental output files
└── venv/                                # Python virtual environment
```

## Key Locations

| What | Where |
|---|---|
| Core analysis pipeline | `scripts/design_space/` |
| Interactive dashboards | `scripts/interactive_tool*.py` |
| Statistical analysis | `scripts/stats/` |
| Validation framework | `scripts/validation/` |
| Shared utilities | `scripts/utils/utils.py` (82KB) |
| Input data | `data/*.xlsx` |
| Generated visualizations | `viz/` |
| Statistical exports | `export/stats/` |
| UMAP cached embeddings | `export/DS_*.pkl`, `export/DS_*.csv` |

## Naming Conventions

### Files
- **Modules**: `snake_case.py` — descriptive names prefixed by domain (`dspace_`, `stats_`, `validation_`)
- **Runner scripts**: `*_run.py` — entry points that orchestrate pipeline execution
- **Interactive tools**: `interactive_tool*.py` — Dash web applications

### Functions
- `snake_case` throughout
- Pipeline functions: verb-first (`create_embedding`, `calc_distmatrix`, `plot_embedding`)
- Metric functions: domain-prefixed (`dist_metrics_fs`, `dist_metrics_pre`)
- Session-segmented: `*_fs` (full session), `*_pre` (pre-intervention), `*_post` (post-intervention)

### Variables
- DataFrames: `df_` prefix (`df_base`, `df_colors`, `df_cvxh_metrics`)
- Directories: `dir_` or `my_dir` prefix
- Masked group IDs: 2-letter uppercase (`VZ`, `XX`, `NI`)
- Unmasked group IDs: `*_U` suffix (`GA_U`, `GB_U`)

### Data Columns
- Participant: `ParticipantID`, `OriginalID_PT`
- Session: `OriginalID_PrePost` (KYY=pre, ZSB=post)
- Metrics: `CH_Area`, `CH_Perim`, `AreaFS`, `AreaPRE`, `AreaPOST`

## Import Patterns

Two import patterns coexist:
1. **From project root** (Dash apps): `from scripts.design_space.read_data import read_analysis`
2. **From scripts/ directory** (run scripts): `from design_space.read_data import *`

Wildcard imports (`from module import *`) are used extensively in run scripts.
