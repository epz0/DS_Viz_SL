# Coding Conventions

**Analysis Date:** 2026-02-14

## Naming Patterns

**Files:**
- Module files: lowercase with underscores (e.g., `dist_matrix.py`, `dspace_metrics.py`, `stats_main.py`)
- Descriptive names indicating purpose (e.g., `dspace_viz_density.py` for visualization)
- Interactive/runnable files: `interactive_tool.py`, `stats_run.py`, `test_run.py`

**Functions:**
- Lowercase with underscores separating words (snake_case)
- Descriptive action-oriented names: `plot_full()`, `calc_distmatrix()`, `export_cvxh_metrics()`, `create_embedding()`
- Primary functions use gerunds or imperative verbs: `create_`, `plot_`, `calc_`, `export_`
- Helper functions follow same snake_case convention: `jac_dist()`, `prep_density()`, `area_summary()`

**Variables:**
- Dataframe variables prefixed with `df_`: `df_base`, `df_colors`, `df_dist_metrics`, `df_ch_fs_metrics`, `df_kde`
- Matrix/array variables: `embed`, `embedding_umap`, `x_y_points`, `path_dist`
- Path variables: `dir_data`, `dir_exp`, `dir_viz`, `my_dir`
- List variables: `pt_unique`, `solutions_list`, `res_list`, `nr_clust_list`
- Abbreviated descriptors for parameters: `NN` (n_neighbors), `MD` (min_dist), `Wg` (weight), `densm` (densmap)
- Loop indices: `i`, `j`, `s_idx` (solution index)
- Short identifiers in comments: `PT` (participant), `FS` (full session), `PRE`/`POST` (intervention phases)

**Types:**
- Constant values (initial definitions): `VALID_MODE` (set of valid strings)
- Configuration parameters at module top: `GA`, `GB`, `GC` (group identifiers), `NOV` (novelty types)

## Code Style

**Formatting:**
- No linter/formatter configuration detected - code uses inconsistent indentation patterns
- Some files use `#%%` cell markers (Jupyter notebook style)
- Mixed spacing around operators in some files

**Comments:**
- Active development comments marked with `#!` to draw attention: `#! loop to create participants' cvxh`
- Implementation notes marked with `#*`: `#* error if mode is invalid`, `#* error checking`
- Descriptive inline comments on separate line: `# get list of unique participant ids`
- Multi-line comments wrapped in triple quotes for functions: `'''comment here'''`

## Import Organization

**Order:**
1. Standard library imports: `from pathlib import Path`, `import ast`, `import json`, `import math`
2. Third-party scientific imports: `import pandas as pd`, `import numpy as np`, `import matplotlib.pyplot as plt`
3. Third-party specialized imports: `from scipy.spatial import ConvexHull`, `from statsmodels.formula.api import ols`, `import plotly.express as px`
4. Local imports (relative to project): `from scripts.utils.utils import *`, `from scripts.design_space.read_data import read_analysis`
5. Blank line between sections

**Path Aliases:**
- Uses `from scripts.design_space import *` for wildcard imports
- No explicit path aliases configured; relative imports use full module paths
- Local module references always prefixed with `scripts.` from project root

## Error Handling

**Patterns:**
- Match/case statements for mode validation: `match mode:` with `case 'full':`, `case 'pre':`, `case 'post':`
- Explicit value validation with `raise ValueError()`: `if mode not in VALID_MODE: raise ValueError(...)`
- Defaults for None parameters: `if sheetname is None: df_base = pd.read_excel(...)`
- Conditional logic for optional parameters: `if gowerweight is None: gwr_wgt = ast.literal_eval(...)`
- No try/except blocks used; relies on parameter validation upfront
- File existence checks: `if Path(...).is_file() == True:` or `if my_graph.is_file():`

## Logging

**Framework:** console print statements only

**Patterns:**
- Status messages with `print()`: `print("Getting metrics' weights...")`, `print('Reading masking keys from file...')`
- Progress indicators: `print(f"Calculating participants' convex hull for the FULL SESSION, save = {save_plot}...")`
- Completion messages: `print('DFs and data retrieved!')`, `print('Unmasking the data done!')`
- Parameter feedback: `print(f'RES: {res_var:.4f} | PREVIOUS (max): {previous_n_clust} | CURRENT: {curr_n_clust}')`
- Conditional logging based on boolean flags: `if save_plot == True: print(...)`
- Loop progress: `print(f'{row["PID"]} done')`

## Function Design

**Size:** Functions range from 15-100+ lines; larger functions typically handle orchestration or multi-step processes

**Parameters:**
- Dataframes passed as first positional argument: `def func(df, ...)`
- Paths passed as `Path` objects: `dir_data` parameter appears consistently
- Optional keyword arguments with `None` defaults for features: `save_plot=False`, `mode='full'`, `mult_plot=None`
- Many functions accept optional string parameters: `embed_name=None`, `figtitle=None`, `fn=None`
- Configuration parameters passed explicitly: `NN=120`, `MD=0.3`, `Wg='W2'`

**Return Values:**
- Single return values typically tuple of related dataframes: `return df_unmasked, df_colors_unm`
- Multiple returns for related outputs: `return embedding_umap, DS_graph`, `return df_kde, lim_x, lim_y`
- No early returns observed; complete conditional logic before return statement

## Module Design

**Exports:**
- Modules export functions without explicit `__all__` declarations
- Wildcard imports used extensively: `from scripts.design_space.dist_matrix import *`
- All public functions at module level; no class-based designs

**Module Structure:**
- Docstring at top describing module purpose and listing functions
- Function definitions follow immediately after imports
- Example docstring format:
  ```
  """The module_name module does X, Y, and Z.

  Functions:
      func_name: Description of what it does.
      func2_name: Description of what it does.
  """
  ```

**Docstrings:**
- Triple-quoted docstrings for all functions with Args, Returns sections
- Args section lists parameter name, type, and description: `Args: param (type): Description.`
- Returns section lists return variable and description
- Optional parameters noted in description: `Defaults to None.`
- Type hints only in docstrings; no inline type annotations used (Python 3.8 style)

## Cell Markers

**Jupyter Style:**
- Interactive development files use `#%%` markers to denote cell boundaries
- Examples: `interactive_tool.py`, `interactive_run.py` start with `#%%`
- Allows running sections independently in IDEs like VSCode/Spyder

---

*Convention analysis: 2026-02-14*
