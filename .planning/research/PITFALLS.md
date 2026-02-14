# Domain Pitfalls: Dash-to-Streamlit Migration

**Domain:** Interactive Plotly visualization migration from Dash to Streamlit
**Researched:** 2026-02-14
**Confidence:** LOW (based on training data only - research tools restricted)

> **IMPORTANT:** This research was conducted without access to current documentation, Context7, or web search. All findings are based on training data (cutoff January 2025) and should be verified against current Streamlit and streamlit-plotly-events documentation before implementation.

## Critical Pitfalls

Mistakes that cause rewrites or major issues.

### Pitfall 1: Treating Streamlit Like Dash with Callbacks
**What goes wrong:** Developers try to recreate Dash's explicit callback model in Streamlit, leading to convoluted state management, unnecessary session state variables, and re-render loops.

**Why it happens:** Dash uses explicit `@app.callback` decorators that fire on input changes. Streamlit runs the entire script top-to-bottom on every interaction. Developers used to Dash's model try to fight Streamlit's execution model instead of embracing it.

**Consequences:**
- Code becomes harder to maintain than the original Dash version
- Excessive use of `st.session_state` that's hard to debug
- Re-render loops where state changes trigger re-runs that trigger more state changes
- Performance degradation from unnecessary computations on every re-run

**Prevention:**
- Accept that Streamlit re-runs the entire script on interaction
- Use `st.session_state` sparingly - only for data that must persist across runs
- Leverage `@st.cache_data` and `@st.cache_resource` for expensive operations
- Design the script flow to be idempotent (same inputs = same outputs)
- Put expensive computations in cached functions, not in the main script flow

**Detection:**
- Code has many `if 'variable' not in st.session_state` checks
- State variables that mirror UI widget values (usually redundant)
- Mysterious bugs where order of code execution matters unexpectedly
- Performance issues that worsen with more interactions

**Phase mapping:** Phase 1 (Architecture) must establish state management patterns upfront.

---

### Pitfall 2: Not Pre-Computing Everything Needed for Deployment
**What goes wrong:** App depends on data processing or computation that works locally but fails or is too slow on Streamlit Community Cloud due to resource constraints or missing dependencies.

**Why it happens:** Developers test locally with full data and computational resources, then deploy assuming the same environment. Streamlit Community Cloud has memory limits (~1GB), CPU limits, and cold start penalties.

**Consequences:**
- App crashes on deployment with memory errors
- Extremely slow first load (30+ seconds)
- Timeout errors during data processing
- Missing dependencies that worked locally

**Prevention:**
- Pre-compute ALL derived data, statistics, and visualizations
- Save to efficient serialization format (Parquet > CSV for large data, pickle for complex objects)
- Test data loading time - should be <2 seconds for good UX
- Include data validation checks to ensure pre-computed data has everything needed
- Document exactly what data processing must happen before deployment vs. at runtime
- Test with production data size, not toy examples

**Detection:**
- App works locally but times out on first deployment load
- Memory errors in Streamlit Cloud logs
- Long loading spinners on initial app load
- Error messages about missing columns or data that "should be there"

**Phase mapping:** Phase 0 (Data Preparation) should be a distinct phase before any UI work. Phase 2 (Deployment) should include deployment testing with realistic resource constraints.

---

### Pitfall 3: Naive Handling of Large Plotly Figures (63 traces)
**What goes wrong:** Recreating the entire Plotly figure on every interaction causes multi-second lag times, making the app unusable. Streamlit doesn't have Dash's `Patch()` for partial updates.

**Why it happens:** Dash allows partial figure updates via `Patch()` - you can update just the styling of one trace or add a single annotation without rebuilding the entire figure. Streamlit has no equivalent, so every state change that affects the figure requires regenerating and re-rendering the entire figure JSON (63 traces = large payload).

**Consequences:**
- 2-5 second lag on every interaction
- Poor user experience that feels "broken"
- High bandwidth usage (figure JSON is sent on every update)
- Browser memory issues with repeated large figure renders
- App becomes unusable on mobile or slow connections

**Prevention:**
- **Strategy 1: Lazy rendering** - Only show complex figures when user requests them, not by default
- **Strategy 2: Smart caching** - Cache figure generation with `@st.cache_data`, only invalidate when truly necessary
- **Strategy 3: Figure decomposition** - Split into multiple smaller figures if possible (e.g., separate performance chart from scatter)
- **Strategy 4: Reduce trace complexity** - Simplify hull traces (fewer points), use `simplify` options in Plotly
- **Strategy 5: Incremental reveal** - Start with base figure, add traces on user request
- **For your case:** Cache base figure, use session state to track which elements are visible, only rebuild when visibility changes

**Detection:**
- Noticeable lag (>1 second) after clicking UI elements
- Network tab shows multi-MB payloads on interactions
- Browser DevTools shows high CPU during figure rendering
- Users report app feeling "slow" or "laggy"

**Phase mapping:** Phase 1 (Architecture) must include performance strategy. Phase 3 (Optimization) should profile and optimize figure rendering.

---

### Pitfall 4: Sync'd Chart Interactions Without Proper State Management
**What goes wrong:** Click on scatter plot should update performance chart and vice versa, but state updates cause infinite re-render loops, stale data display, or clicks not registering.

**Why it happens:** `streamlit-plotly-events` returns click data on widget creation. If click data updates state, and state change triggers re-run, which recreates widget, which returns click data again... infinite loop. Also, Streamlit's top-to-bottom execution means order matters critically.

**Consequences:**
- Infinite re-render loops that crash the app
- Clicks not registering or requiring double-clicks
- Chart A updates but Chart B doesn't sync
- Race conditions where clicks are processed out of order
- State corruption where displayed data doesn't match selection

**Prevention:**
- **Pattern:** Use `st.session_state` keys for "source of truth" (selected point, selected solution)
- **Pattern:** Check if click data is different from current state before updating
- **Pattern:** Use unique keys for plotly-events widgets to prevent re-triggering
- **Pattern:** Structure code so state updates happen BEFORE figure generation
- **Pattern:** Add debug mode that shows current state values for troubleshooting
- **Code structure:**
  ```python
  # 1. Initialize state
  if 'selected_point' not in st.session_state:
      st.session_state.selected_point = None

  # 2. Capture events (with unique key)
  click_data = plotly_events(fig_scatter, key="scatter_events")

  # 3. Update state only if changed
  if click_data and click_data != st.session_state.get('last_click'):
      st.session_state.selected_point = extract_point(click_data)
      st.session_state.last_click = click_data

  # 4. Generate figures based on current state
  fig_performance = create_performance_chart(st.session_state.selected_point)
  ```

**Detection:**
- App goes into infinite re-run loop (visible in top-right "Running..." indicator)
- Clicks require multiple attempts to register
- Console shows repeated widget creation logs
- Charts don't stay in sync after interactions
- `st.session_state` inspection shows unexpected values

**Phase mapping:** Phase 1 (Architecture) must design the state management pattern. Phase 2 (Implementation) must test click handling thoroughly.

---

### Pitfall 5: GitHub URL Dependencies Breaking on Deployment
**What goes wrong:** Solution screenshots loaded from GitHub raw URLs work locally but fail intermittently on Streamlit Cloud due to rate limiting, CORS issues, or GitHub availability.

**Why it happens:** Streamlit Cloud has different network environment than localhost. GitHub raw content URLs can be rate-limited, blocked by corporate firewalls, or experience downtime. Also, CORS policies may differ.

**Consequences:**
- Images fail to load on deployment
- Intermittent errors that are hard to reproduce
- Rate limit errors after multiple users access the app
- Broken image icons in UI

**Prevention:**
- **Best:** Bundle images with the app in a `/static` or `/assets` folder
- **Alternative:** Use a CDN or Streamlit Cloud's static file serving
- **If must use GitHub:** Use GitHub API with authentication, not raw URLs
- **Fallback:** Implement graceful fallback (show placeholder if image fails to load)
- **Validation:** Test with images disabled to ensure app still functions

**Detection:**
- Images show broken image icon
- Browser console shows CORS errors
- Network errors in browser DevTools
- Works locally but fails on deployment

**Phase mapping:** Phase 0 (Data Preparation) should bundle all assets. Phase 2 (Deployment) should verify asset loading.

## Moderate Pitfalls

### Pitfall 6: Ignoring Streamlit Community Cloud Memory Limits
**What goes wrong:** App works with full dataset locally (e.g., loading all solutions, all performance data) but crashes on deployment with MemoryError.

**Prevention:**
- Profile memory usage locally with `memory_profiler`
- Keep total app memory under 800MB to be safe (Community Cloud ~1GB limit)
- Use efficient data structures (Parquet, not CSV; NumPy arrays, not lists)
- Load data lazily - only load what's currently displayed
- Test with production data size on deployment before launch

**Detection:**
- "MemoryError" in Streamlit Cloud logs
- App crashes after running for a while
- Slow garbage collection causing lag

---

### Pitfall 7: Not Handling Cold Starts
**What goes wrong:** First user to visit app after inactivity waits 30+ seconds for app to spin up, then waits again for data loading. Poor first impression.

**Prevention:**
- Optimize import statements (import only what's needed, import locally in functions)
- Use efficient data serialization (Parquet loads faster than CSV)
- Show loading progress with `st.spinner()` or `st.progress()`
- Consider using Streamlit's `@st.cache_resource` for one-time setup
- Document expected cold start time in README
- Pre-warm app by visiting it before sharing with users

**Detection:**
- First load takes >15 seconds
- Subsequent loads are much faster
- Users report "app takes forever to load"

---

### Pitfall 8: Over-Relying on Session State
**What goes wrong:** Every piece of data gets stuffed into `st.session_state`, making debugging impossible and causing memory bloat.

**Prevention:**
- Only store in `st.session_state` what MUST persist across re-runs
- Don't store data that can be recomputed from cached functions
- Don't store data that mirrors widget values (widgets already manage their own state)
- Use clear naming conventions (e.g., `selected_*`, `user_*`)
- Add session state viewer for debugging (optional debug panel)

**Detection:**
- `st.session_state` has >20 keys
- Memory usage grows over time
- Hard to track what's in state and why
- State-related bugs are difficult to reproduce

---

### Pitfall 9: Not Testing Widget Keys
**What goes wrong:** Widgets without unique keys cause Streamlit to lose track of widget state on re-runs, leading to widgets resetting unexpectedly or events firing incorrectly.

**Prevention:**
- Always use `key=` parameter for widgets that should maintain state
- Use descriptive, unique key names
- Don't generate keys dynamically based on data that changes
- Document key naming convention

**Detection:**
- Widgets reset to default values unexpectedly
- Selection state is lost on re-run
- Events fire for wrong widget

---

### Pitfall 10: Missing Deployment Configuration
**What goes wrong:** App has hardcoded paths, assumes specific file structure, or uses environment variables that aren't set on Streamlit Cloud.

**Prevention:**
- Use `pathlib.Path(__file__).parent` for relative paths
- Create `.streamlit/config.toml` for Streamlit-specific settings
- Use `secrets.toml` (local) and Streamlit Cloud secrets (deployment) for sensitive config
- Test with `streamlit run` from different directories to catch path issues

**Detection:**
- FileNotFoundError on deployment but not locally
- "No such file or directory" errors
- Environment variable errors on deployment

## Minor Pitfalls

### Pitfall 11: Inefficient Data Filtering in UI
**What goes wrong:** Filtering 30 solutions on every interaction by iterating through lists instead of using vectorized operations.

**Prevention:**
- Use pandas/NumPy for filtering, not Python loops
- Pre-filter data in cached functions
- Profile filtering operations to ensure <100ms

**Detection:** Noticeable lag when changing filters.

---

### Pitfall 12: Poor Mobile Experience
**What goes wrong:** Complex Plotly figures with 63 traces are unusable on mobile - too small, too slow, unresponsive touch interactions.

**Prevention:**
- Test on mobile early
- Consider responsive layouts with `st.columns()`
- Add simplified mobile view option
- Document minimum screen size requirements

**Detection:** Users report "doesn't work on phone".

---

### Pitfall 13: No Error Handling for Edge Cases
**What goes wrong:** App crashes when user clicks empty space on chart, selects invalid combination, or encounters missing data.

**Prevention:**
- Wrap event handlers in try/except
- Validate click data before processing
- Show user-friendly error messages with `st.error()`
- Add data validation checks at load time

**Detection:** App crashes with stack trace visible to user.

---

### Pitfall 14: Not Optimizing Plotly Figure Configuration
**What goes wrong:** Default Plotly config includes unnecessary toolbar buttons, animations that slow rendering, or excessive hover data.

**Prevention:**
- Use `config={'displayModeBar': False}` if toolbar not needed
- Disable animations: `layout.transition.duration = 0`
- Simplify hover templates to only show essential info
- Use `scattergl` instead of `scatter` for large datasets (if applicable)

**Detection:** Figures render slowly, toolbar clutters UI.

---

### Pitfall 15: Forgetting to Add requirements.txt
**What goes wrong:** App deploys but crashes immediately because dependencies aren't installed.

**Prevention:**
- Create `requirements.txt` with pinned versions
- Include: `streamlit`, `plotly`, `streamlit-plotly-events`, `pandas`, `numpy`
- Test in fresh virtual environment before deploying
- Pin major versions but allow patch updates (e.g., `streamlit>=1.31.0,<2.0.0`)

**Detection:** Import errors on deployment.

## Phase-Specific Warnings

| Phase Topic | Likely Pitfall | Mitigation |
|-------------|---------------|------------|
| Phase 0: Data Preparation | Not pre-computing derived metrics | Audit all Dash callbacks to extract what's computed at runtime vs. load time |
| Phase 1: Architecture | Fighting Streamlit's execution model | Study Streamlit execution model docs first, design with re-runs in mind |
| Phase 1: Architecture | No performance strategy for 63 traces | Decide caching strategy before implementing UI |
| Phase 2: Implementation | Click event infinite loops | Implement state management pattern first, test with simple figure |
| Phase 2: Implementation | Treating plotly-events like Dash callbacks | Read streamlit-plotly-events docs, understand return value structure |
| Phase 3: Optimization | Premature optimization | Profile first, optimize second - measure actual bottlenecks |
| Phase 4: Deployment | Testing only locally | Deploy to Streamlit Cloud early and often, catch resource issues early |
| Phase 4: Deployment | Not testing cold starts | Clear cache and test fresh load times before launch |

## Project-Specific Risks

### Risk 1: 63 Traces Performance Catastrophe
**Likelihood:** HIGH
**Impact:** CRITICAL (app unusable)
**Mitigation priority:** Phase 1 (Architecture)
**Strategy:**
- Benchmark figure generation time before building UI
- Test figure size (JSON payload)
- Implement caching strategy
- Consider if all 63 traces need to be visible simultaneously
- Profile with realistic interaction patterns (not just single clicks)

---

### Risk 2: Dash Patch() Has No Streamlit Equivalent
**Likelihood:** CERTAIN
**Impact:** HIGH (performance degradation)
**Mitigation priority:** Phase 1 (Architecture)
**Strategy:**
- Accept that figures must be regenerated
- Optimize generation speed (cache base figure, modify copies)
- Consider if partial updates can be simulated with multiple figures
- Use `st.empty()` container pattern to replace figures in place

---

### Risk 3: Complex Dual-Chart State Synchronization
**Likelihood:** HIGH
**Impact:** HIGH (core feature broken)
**Mitigation priority:** Phase 2 (Implementation)
**Strategy:**
- Design state management pattern on paper first
- Create test harness with simple 2-trace figures
- Verify state transitions work correctly before scaling to 63 traces
- Add debug mode that visualizes state changes

---

### Risk 4: Pre-Computed Data Missing Critical Fields
**Likelihood:** MEDIUM
**Impact:** CRITICAL (blocks deployment)
**Mitigation priority:** Phase 0 (Data Preparation)
**Strategy:**
- Audit all Dash callbacks to enumerate data dependencies
- Create data schema documentation
- Implement validation checks that fail fast if data is incomplete
- Test with production data size (all 30 solutions)

## Confidence Assessment

**Overall confidence:** LOW

This research was conducted without access to:
- Current Streamlit documentation (2026)
- Current streamlit-plotly-events documentation
- Streamlit Community Cloud current resource limits
- Recent GitHub issues or discussions
- Context7 library verification

**Verification needed before implementation:**
1. Streamlit Community Cloud current memory limits (assumed ~1GB)
2. `streamlit-plotly-events` current API and known issues
3. Streamlit caching decorators current syntax (`@st.cache_data` vs. older `@st.cache`)
4. Current best practices for large Plotly figures in Streamlit
5. Streamlit session state current behavior and limitations

**Sources:** Training data only (cutoff January 2025)

**Recommendation:** Before proceeding with roadmap, verify critical assumptions:
- Benchmark: Generate 63-trace figure and measure size/render time
- Test: `streamlit-plotly-events` with multi-trace figure click handling
- Verify: Streamlit Cloud resource limits and cold start behavior
- Research: Recent issues with streamlit-plotly-events on GitHub

