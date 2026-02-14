# Concerns

## Technical Debt

### Hardcoded Paths
- Multiple run scripts use absolute Windows paths: `Path(r'C:/Py/DS_Viz_Exp/data')`, `Path(r'C:/DSX_Viz/data')`
- Inconsistent paths across files — `test_run.py`, `stats_run.py`, `viz_run.py`, `validation_run.py` each reference different directories
- Dash apps use `Path.cwd()` which is more portable but fragile if working directory changes
- **Impact:** Cannot run pipeline on different machines without manual path edits

### Code Duplication
- Three near-identical Dash apps: `interactive_tool.py`, `interactive_tool_quant.py`, `interactive_tool_rt.py`
- All ~1100+ lines with the same data pipeline, layout structure, and callback patterns
- Any bug fix must be applied to all three variants
- **Impact:** Maintenance burden, divergence risk between variants

### Wildcard Imports
- Extensive use of `from module import *` in all run scripts
- Namespace pollution and unclear dependencies
- `scripts/utils/utils.py` at 82KB is imported via wildcard — imports everything into caller namespace
- **Impact:** Difficult to trace function origins, IDE completion unreliable

### Monolithic utils.py
- `scripts/utils/utils.py` is 82KB — the largest file in the project
- Likely contains a mix of unrelated utilities accumulated over time
- **Impact:** Hard to navigate, long import times, high coupling

### Inconsistent Import Paths
- Run scripts use relative imports (`from design_space.read_data import *`) requiring execution from `scripts/`
- Dash apps use absolute imports (`from scripts.design_space.read_data import read_analysis`) requiring execution from project root
- **Impact:** Confusing execution requirements, fragile path setup

## Known Issues

### Index-Based DataFrame Access
- `design_space.py` uses index-based row access (`rowsPT = rowsPT.index.tolist()`) which is fragile if DataFrame index is not sequential
- **Risk:** Silent incorrect metrics if DataFrame is filtered/reindexed

### Missing Error Handling in Dash Callbacks
- Graph click interactions in Dash apps don't robustly handle edge cases
- Potential `IndexError` or `KeyError` when clicking on unexpected graph elements
- **Risk:** App crashes on unexpected user interaction

### NaN Handling
- `OriginalID_PT` NaN values handled via string comparison: `str(row.OriginalID_PT) != 'nan'`
- Fragile — depends on string representation of NaN
- Better approach: `pd.isna()` or `pd.notna()`

## Security Concerns

### Masking Keys in Repository
- `MASKING_KEYS` sheet in data Excel file contains the lookup to unmask participant identities
- Data file is tracked in git (recently changed from v1 to v2)
- **Risk:** Participant anonymity could be compromised if repository becomes public

### No Input Validation
- Excel data read directly without schema validation
- Malformed spreadsheet could cause cascading failures
- **Risk:** Low (research tool, controlled inputs) but no defense-in-depth

## Performance Considerations

### UMAP Computation
- UMAP embedding is cached to disk (`.pkl`/`.csv`) — good practice
- But cache invalidation is by filename only, not by content or parameters
- If parameters change but filename doesn't, stale embedding is used

### Repeated Computations
- Distance matrix recalculated in each run script independently
- No shared cache across Dash app and run scripts
- Convex hull computed per participant in loops without vectorization

### Memory
- Full DataFrames loaded into memory via `pd.read_excel()`
- Multiple copies created via `.copy()` calls
- For current dataset size this is fine, but won't scale to much larger experiments

## Fragile Areas

### Sheet Name Dependencies
- Pipeline hardcodes Excel sheet names: `ExpData-100R-Expanded`, `ColorScheme`, `MASKING_KEYS`
- Any sheet rename breaks the entire pipeline silently (pandas will raise but no graceful handling)

### UMAP Cross-Platform Variance
- UMAP with Numba JIT can produce different embeddings across platforms/versions
- Research results may not be exactly reproducible on different machines
- Validation pipeline partially addresses this but doesn't enforce determinism

### Participant Count Assumptions
- Some visualization code may assume specific participant counts (symbol lists, color mappings)
- `symb_ls` in `test_run.py` has 15 symbols — breaks if more participants

### JSON Structure Assumptions
- Dash apps save/load JSON from `data/json/` with assumed structure
- No schema validation on load

## Missing Infrastructure

| Missing | Impact |
|---|---|
| Configuration system | Every path/parameter hardcoded per file |
| Logging framework | Only `print()` statements for progress tracking |
| Automated tests | No regression detection |
| CI/CD pipeline | No automated quality checks |
| Error recovery | Pipeline crashes on any unexpected data |
| Data validation | No input schema enforcement |
| Documentation site | Only module docstrings (some files) |
