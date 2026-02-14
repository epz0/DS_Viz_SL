# Testing

## Current State

**No automated testing framework is in place.** The project has no pytest, unittest, or other test runner configuration.

## Manual Testing Approach

### test_run.py
- `scripts/test_run.py` — Acts as a manual integration test by running the full pipeline
- Executes: data read → distance matrix → UMAP embedding → unmask → metrics → visualization
- Contains commented-out sections that can be toggled for selective testing
- Must be run from the `scripts/` directory due to relative imports
- Uses hardcoded paths (`C:/Py/DS_Viz_Exp/data`) that differ from the Dash app paths

### validation_run.py
- `scripts/validation_run.py` — Runs validation procedures for metric sensitivity
- Tests distance metric weights, area sensitivity, and visual placement of solutions
- More structured than test_run.py but still manual execution
- Compares metric outputs across different parameter configurations

### Interactive Testing
- Dash apps (`interactive_tool*.py`) are tested by running and interacting manually in browser
- No automated callback testing or integration tests for the web interface

## Test Data

- Primary test data: `data/MASKED_DATA_analysis_v2.xlsx`
- Contains masked participant/group identifiers
- Sheet `ExpData-100R-Expanded` holds the main analysis data
- Sheet `ColorScheme` provides participant color assignments
- Sheet `MASKING_KEYS` contains the masking/unmasking lookup

## Coverage Gaps

| Area | Status | Impact |
|---|---|---|
| Distance matrix calculation | No tests | Core pipeline — errors cascade to all metrics |
| UMAP embedding consistency | No tests | Stochastic output; cross-platform variance possible |
| Convex hull metrics | No tests | Key research output — correctness critical |
| Novelty/clustering metrics | No tests | Used in statistical comparisons |
| ANCOVA statistics | No tests | Direct research conclusions depend on this |
| Dash callbacks | No tests | User-facing interactions untested |
| Data masking/unmasking | No tests | Security-relevant transformation |
| Excel export | No tests | Research deliverable format |
| Edge cases (NaN handling, empty participants) | No tests | Silent failures possible |

## Validation as Proxy for Testing

The `scripts/validation/` modules serve as the closest thing to systematic testing:
- `validation_distmetric.py` (29KB) — Extensive distance metric weight comparisons, Procrustes analysis, Spearman correlations, MSE computations
- `validation_areametric.py` — Area metric sensitivity analysis across weight configurations
- `validation_viz.py` — Visual comparison of solution placements under different parameters

These validate research methodology rather than code correctness.

## Recommendations for Future Testing

1. **pytest setup** with fixtures for sample DataFrames and distance matrices
2. **Deterministic UMAP tests** using fixed random seeds
3. **Convex hull property tests** (area > 0, vertices on hull, etc.)
4. **Snapshot tests** for statistical output format
5. **Dash callback tests** using `dash.testing`
