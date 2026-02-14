# Phase 0: Data Preparation & Pre-Computation - Context

**Gathered:** 2026-02-14
**Status:** Ready for planning

<domain>
## Phase Boundary

All heavy computation (UMAP, distance matrix, metrics, clustering, novelty) runs locally via a pre-compute pipeline and outputs cached data files that the Streamlit app loads. Existing analysis scripts in scripts/ remain functional for local use.

</domain>

<decisions>
## Implementation Decisions

### Data Source Handling
- Hardcoded filename — pipeline always reads from a fixed path (data/MASKED_DATA_analysis_v2.xlsx)
- v2 is the final dataset — no more versions expected
- No configurable input path needed

### Pipeline Structure
- Modular steps that can be run independently, plus an "all" command to run everything
- Fail fast on errors — stop immediately, don't produce partial output
- No skip-and-continue behavior

### Output File Organization
- Pre-computed files committed to the repo (git history serves as backup)
- Streamlit Cloud loads them directly from the repo — no build step on deploy

### Recomputation Behavior
- Skip steps whose output already exists (use --force to override)
- Overwrite directly when recomputing — no backup files, git is the backup
- Auto-validate after every run as the final step (check all 80+ columns, data integrity)

### Claude's Discretion
- Script location (scripts/ vs streamlit_app/ vs project root)
- Code source — which existing scripts/Dash app logic to extract from
- Progress reporting approach (print statements vs logging module)
- Dependency management — single vs separate requirements files
- Output file split strategy (one file per concern vs consolidated)
- File format choices per data type (parquet, pickle, JSON)
- Whether to include a manifest file for traceability
- Behavior on validation failure (delete bad output vs keep for debugging)

</decisions>

<specifics>
## Specific Ideas

No specific requirements — open to standard approaches

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 00-data-preparation*
*Context gathered: 2026-02-14*
