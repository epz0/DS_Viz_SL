# External Integrations

**Analysis Date:** 2026-02-14

## APIs & External Services

**File Conversion Service:**
- Polyutils - External service for converting design solution files
  - URL: `https://polyutils.dumbserg.al/ace/mode-json.js`
  - SDK/Client: `requests` (Python HTTP library)
  - Purpose: Convert `.slot` files (design solution format) to JSON
  - Usage: `scripts/convert_save.py` - One-off utility script, not used in main pipeline
  - Implementation: Simple HTTP POST with file upload

**Web Styling:**
- CodePen CSS - External stylesheet for Dash UI styling
  - URL: `https://codepen.io/chriddyp/pen/bWLwgP.css`
  - Purpose: Provides baseline CSS styling for web interface
  - Implementation: Loaded via `external_stylesheets` parameter in Dash initialization
  - Location: `scripts/interactive_tool.py` line 34

## Data Storage

**Databases:**
- None - No database system detected
- Data storage: Local filesystem only (Excel files in `/data/`)

**File Storage:**
- Local filesystem only
- Primary data: `/data/MASKED_DATA_analysis_v2.xlsx`
- Masking keys: `/data/MASKING_KEYS.xlsx`
- Validation data: `/data/validation_study.xlsx`
- Generated outputs: `/data/json/` (design space embeddings and metrics)
- Visualizations: `/viz/` directory structure

**Caching:**
- None - No caching layer (Redis, Memcached, etc.)
- Embeddings are computed once and stored as JSON files
- No in-memory caching mechanism in web application

## Authentication & Identity

**Auth Provider:**
- None - No authentication system
- Application is not multi-user
- No login, session management, or access control
- Single-user or shared-instance deployment model

## Monitoring & Observability

**Error Tracking:**
- None - No error tracking service (Sentry, Rollbar, etc.)
- Errors are logged to console/stdout

**Logs:**
- Console-based logging only
- `print()` statements throughout codebase for debug output
- No structured logging framework
- No log aggregation service

## CI/CD & Deployment

**Hosting:**
- Heroku-ready (via Procfile)
- Can deploy to any platform supporting Python 3.12.2 with Gunicorn
- No cloud provider-specific integrations (AWS, Azure, GCP)

**CI Pipeline:**
- None - No CI/CD system detected (.github/workflows, .gitlab-ci.yml, etc.)
- Manual deployment process

## Environment Configuration

**Required env vars:**
- None detected - No environment variables used
- All configuration is hardcoded in script files

**Secrets location:**
- No secrets management system in use
- Encryption keys stored locally: `data/MASKING_KEYS.xlsx`
- No external key management (AWS Secrets Manager, HashiCorp Vault, etc.)

## Data Processing External Dependencies

**Distance Calculation Libraries:**
- Gower 0.1.2 - Distance metric computation
- SciPy spatial module - Convex hull, Delaunay triangulation, distance matrices

**Dimensionality Reduction:**
- UMAP-learn 0.5.7 - 2D embedding generation
  - No external API calls - all computation local
  - CPU-intensive operation with NUMBA JIT compilation

**Spatial/Geometric Operations:**
- Shapely 2.0.6 - Polygon operations, intersection calculations
- No external geometry service used

## Webhooks & Callbacks

**Incoming:**
- None - No webhook endpoints

**Outgoing:**
- None - No outbound webhook calls

## Network & Connectivity

**Internet Requirements:**
- Required for:
  - Loading external CSS stylesheet from CodePen (on application startup)
  - One-off file conversion API calls (if using `convert_save.py`)
- Not required for:
  - Main analysis and visualization pipeline
  - Web application serving (once CSS is cached)

**Data Export:**
- Excel file export via Pandas (local filesystem)
- JSON export for design space data (local filesystem)
- No cloud storage integration

## Version Control & Collaboration

**Repository:**
- GitHub repository: https://github.com/epz0/DS_Viz
- No automated deployment from GitHub (manual process)

---

*Integration audit: 2026-02-14*
