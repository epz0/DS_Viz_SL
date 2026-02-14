# Technology Stack

**Analysis Date:** 2026-02-14

## Languages

**Primary:**
- Python 3.12.2 - All application code, analysis pipelines, and web framework

## Runtime

**Environment:**
- Python 3.12.2 (specified in `runtime.txt`)

**Package Manager:**
- pip - Dependency management
- Lockfile: No (direct requirements.txt without lock file)

## Frameworks

**Web Framework:**
- Dash 2.18.2 - Interactive web application framework for design space visualization
- Flask 3.0.3 - Underlying WSGI application server (used by Dash)

**Data Processing & Analysis:**
- Pandas 2.2.3 - Data manipulation, Excel file reading, dataframe operations
- NumPy 2.0.2 - Numerical computations, array operations
- SciPy 1.14.1 - Scientific computing (spatial algorithms, distance matrices)
- Scikit-learn 1.5.2 - Machine learning utilities

**Visualization:**
- Plotly 5.23.0 - Interactive charts and graphs in Dash dashboards
- Matplotlib 3.9.2 - Static visualization and plot generation
- Seaborn 0.13.2 - Statistical visualization

**Dimensionality Reduction:**
- UMAP-learn 0.5.7 - 2D/3D embedding for design space visualization
- Numba 0.60.0 - JIT compilation for performance optimization

**Graph/Spatial Analysis:**
- igraph 0.11.8 - Graph data structures and algorithms
- Shapely 2.0.6 - Geometric operations and polygon processing
- Gower 0.1.2 - Distance metric calculations

**Statistical Analysis:**
- StatsModels 0.14.4 - Statistical modeling and ANCOVA tests

## Server & Deployment

**Web Server:**
- Gunicorn 23.0.0 - WSGI HTTP server for production deployment
- Procfile entry point: `web: gunicorn scripts.interactive_tool:server`

## Key Dependencies

**Critical:**
- dash 2.18.2 - Core interactive web framework for design space visualization
- pandas 2.2.3 - Data loading, transformation, and analysis (Excel files)
- plotly 5.23.0 - Interactive visualization in web interface
- umap-learn 0.5.7 - Embedding generation for design space visualization (performance-sensitive)
- scipy 1.14.1 - Spatial algorithms (Delaunay, ConvexHull, distance calculations)
- scikit-learn 1.5.2 - Machine learning utilities for data processing

**Infrastructure:**
- numpy 2.0.2 - Numerical operations, matrix computations
- matplotlib 3.9.2 - Static visualization and figure generation
- openpyxl 3.1.5 - Excel file I/O operations
- shapely 2.0.6 - Polygon and geometric computations for design space areas
- numba 0.60.0 - Performance optimization through JIT compilation
- statsmodels 0.14.4 - Statistical tests and analysis

**Utilities:**
- requests 2.32.3 - HTTP requests for external file conversion API
- pillow 11.0.0 - Image processing
- tqdm 4.67.0 - Progress bars for long-running operations
- joblib 1.4.2 - Parallel job processing

## Data Storage

**File-based:**
- Excel files (`.xlsx`) stored in `/data/` directory:
  - `MASKED_DATA_analysis_v2.xlsx` - Primary dataset with design solutions and analysis
  - `MASKING_KEYS.xlsx` - Encryption/masking keys for sensitive participant data
  - `validation_study.xlsx` - Validation dataset
- JSON files - Generated embeddings and design space data exported to `/data/json/`
- No database (no SQL, MongoDB, or other DBMS dependency)

## Configuration

**Environment:**
- No `.env` file detected - Configuration is hardcoded in scripts
- Data directory paths are specified as hardcoded `Path` objects in each script
- Key configuration variables:
  - `my_dir` - Path to data directory (e.g., `Path.cwd().joinpath('data')`)
  - `filenm` - Excel filename (e.g., `'MASKED_DATA_analysis_v2.xlsx'`)
  - `sheetnm` - Excel sheet name (e.g., `'ExpData-100R-Expanded'`)
  - `external_stylesheets` - Codepen CSS for Dash styling

**Build:**
- No build system (pure Python application)
- Deployment via Procfile (Heroku-compatible)

## Entry Points

**Interactive Web Application:**
- `scripts/interactive_tool.py` - Main Dash application with Flask server
  - Server instance: `server = app.server` (for Gunicorn)
  - Run locally: `app.run_server(debug=True)`

**Analysis Scripts:**
- `scripts/test_run.py` - Test pipeline execution
- `scripts/stats_run.py` - Statistical analysis and metrics generation
- `scripts/stats_run_mdsx.py` - Alternative statistical pipeline
- `scripts/validation_run.py` - Validation workflow
- `scripts/viz_run.py` - Visualization generation

**Variant Tools:**
- `scripts/interactive_run.py` - Alternative Dash server entry point
- `scripts/interactive_run_mp.py` - Multiprocessing variant
- `scripts/interactive_tool_quant.py` - Quantitative analysis tool variant
- `scripts/interactive_tool_rt.py` - Real-time analysis tool variant

## Platform Requirements

**Development:**
- Windows 10/11 (primary development platform)
- Linux/Ubuntu support (documented but with cross-platform RNG differences in UMAP)
- Python 3.12.2

**Production:**
- Heroku-compatible (Procfile present)
- Any platform supporting Python 3.12.2 and Gunicorn
- Minimum: 512MB RAM for typical design space analysis
- Recommended: 2GB+ RAM for large datasets (100+ participants)

## Known Limitations & Notes

**Cross-platform Replicability:**
- UMAP has known RNG-dependent differences between Windows and Linux
- Average difference in design space areas between Windows vs. Linux: ~2.7%
- See: https://github.com/lmcinnes/umap/issues/153

---

*Stack analysis: 2026-02-14*
