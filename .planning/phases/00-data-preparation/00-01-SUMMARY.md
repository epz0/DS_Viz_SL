---
phase: 00-data-preparation
plan: 01
subsystem: data-pipeline
tags: [python, umap, leiden-clustering, pandas, numpy, pickle, parquet, cli, argparse]

# Dependency graph
requires:
  - phase: none (initial phase)
    provides: []
provides:
  - Complete pre-computation pipeline script with CLI interface
  - Modular step execution (read, distance, umap, unmask, features, metrics, clusters, novelty, hulls)
  - Skip-if-exists caching with force override
  - Output directory structure for Streamlit app data
  - Fail-fast error handling for pipeline integrity
affects: [00-02, streamlit-app, data-loading]

# Tech tracking
tech-stack:
  added: [argparse, logging, pickle-protocol-5, pathlib]
  patterns: [cli-pipeline, step-functions, skip-if-exists, fail-fast, in-memory-passthrough]

key-files:
  created:
    - scripts/precompute.py
    - streamlit_app/data/.gitkeep
    - streamlit_app/data/intermediate/.gitkeep
  modified: []

key-decisions:
  - "Modular CLI with individual steps + 'all' command for flexibility"
  - "Skip-if-exists logic with --force override to avoid redundant computation"
  - "Fail-fast error handling (no silent catches) for pipeline integrity"
  - "In-memory data passing for 'all' command, disk loading for individual steps"
  - "Production UMAP params: NN=115, MD=0.15, densm=2 (not dev values from interactive_tool.py)"

patterns-established:
  - "Pipeline step functions: check cache → load prerequisites → compute → save → return"
  - "Path configuration: SCRIPT_DIR, PROJECT_ROOT, DATA_DIR, OUTPUT_DIR, INTERMEDIATE_DIR"
  - "Logging: module-level logger with structured format"
  - "Pickle protocol 5 for large objects (graph, dataframes)"

# Metrics
duration: 5min
completed: 2026-02-14
---

# Phase 00 Plan 01: Pre-Computation Pipeline Summary

**935-line CLI pipeline extracting all computation logic from Dash app into modular, cacheable steps with skip-if-exists and fail-fast error handling**

## Performance

- **Duration:** 5 min
- **Started:** 2026-02-14T17:28:42Z
- **Completed:** 2026-02-14T17:33:48Z
- **Tasks:** 1
- **Files modified:** 3

## Accomplishments
- Complete pre-computation pipeline with 11 steps (read through validate)
- CLI with argparse supporting individual step execution and full pipeline
- Skip-if-exists logic preventing redundant computation unless --force specified
- Fail-fast error handling ensuring no partial outputs on failure
- Output directory structure created for Streamlit app cached data

## Task Commits

Each task was committed atomically:

1. **Task 1: Create precompute.py pipeline script with all computation steps** - `f7c5331b` (feat)

## Files Created/Modified
- `scripts/precompute.py` - 935-line CLI pipeline with all computation steps from interactive_tool.py
- `streamlit_app/data/.gitkeep` - Output directory marker for final cached data
- `streamlit_app/data/intermediate/.gitkeep` - Intermediate outputs directory marker

## Decisions Made

1. **Modular CLI structure**: Individual subcommands for each step plus 'all' command allows flexible execution and debugging of specific stages

2. **Skip-if-exists with --force**: Each step checks for existing output before running, significantly reducing development iteration time while allowing forced recomputation

3. **Fail-fast error handling**: No try/except around pipeline steps in run_all_steps ensures immediate failure propagation, preventing partial/corrupted outputs

4. **In-memory vs disk data passing**: 'all' command passes data between steps in memory for efficiency; individual steps load prerequisites from disk for modularity

5. **Production UMAP parameters**: Used NN=115, MD=0.15, densm=2 instead of dev values (NN=85, MD=0.25, densm=3) found in interactive_tool.py line 48

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None - all computation logic successfully extracted from interactive_tool.py with appropriate imports, path handling, and output structure.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

Pipeline script complete and ready for execution testing (Plan 02). All steps implemented:
- Step 1 (read): Excel data loading
- Step 2 (distance): Distance matrix computation
- Step 3 (umap): UMAP embedding generation
- Step 4 (unmask): Participant data unmasking
- Step 5 (features): Core attributes and solution summary
- Step 6 (metrics): Distance and area metrics
- Step 7 (clusters): Leiden clustering
- Step 8 (novelty): Density and neighbor-based novelty
- Step 9 (hulls): Convex hull vertices
- Step 10 (save_final): Parquet/pickle, metadata, manifest
- Step 11 (validate): Output validation

---
*Phase: 00-data-preparation*
*Completed: 2026-02-14*

## Self-Check: PASSED

All files and commits verified:
- FOUND: scripts/precompute.py
- FOUND: streamlit_app/data/.gitkeep
- FOUND: streamlit_app/data/intermediate/.gitkeep
- FOUND: commit f7c5331b
