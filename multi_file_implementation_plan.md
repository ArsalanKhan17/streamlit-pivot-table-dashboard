
# Multi‑File Support with Tabbed UI — Implementation Plan

## Objectives
- Enable uploading and working with **multiple files concurrently**.
- Provide an intuitive **tabbed UI** where each file has isolated filters, pivots, and plots.
- Maintain compatibility with current single‑file workflows in `app.py` and logic helpers in `core.py`.
- Keep the codebase modular, testable, and easy to extend (XLSX/Parquet later).

---

## Scope
In scope:
- UI to upload many CSVs at once.
- One tab per file with independent preview → filter → pivot → plot flow.
- Shared “core” utilities reused across tabs.
- Robust validation and failure states.

Out of scope (for now):
- XLSX/Parquet ingestion.
- Cross‑file joins or comparisons.
- Persistent storage across sessions.

---

## High‑Level Design
**Inputs:** One or more CSV files.  
**State:** `st.session_state.datasets: Dict[str, pd.DataFrame]`, per‑tab UI state keys namespaced by filename.  
**UI:** Sidebar multi-file uploader. Main area renders `st.tabs([...])` matching filenames.  
**Processing:** Reuse helpers in `core.py` for pivoting, type inference, and safe plotting hooks.  
**Outputs:** On‑screen tables and charts. Optional CSV export of filtered/pivoted data.

---

## UI/UX Specification
1. **Sidebar**
   - `st.file_uploader(..., accept_multiple_files=True, type=["csv"])`.
   - “Reset all” button clears session state.
2. **Main**
   - Tabs named by original filenames. Sanitized for Streamlit keys.
   - Each tab includes:
     1) Preview (head with row count).
     2) Filter builder:
        - Multiselect of columns to filter.
        - For each selected column, a multiselect of unique values.
        - Treat all values as strings for selection to avoid dtype mismatches.
     3) Pivot builder:
        - Rows, Columns multiselects.
        - Values multiselect for numeric columns.
        - Aggregation select: `sum, mean, count, min, max, median, nunique`.
        - Display pivot as a flat table.
        - “Download CSV” for pivot result.
     4) Chart builder:
        - Data source toggle: `Filtered data` or `Pivot table`.
        - X and Y selectors.
        - Chart type: bar, line, scatter.
        - Render via Plotly.
3. **Empty/Failure States**
   - No files → show info box to upload.
   - Pivot errors → show `st.error` with exception.
   - No numeric columns → disable values dropdown and suggest `count`.

---

## State Management
- All tab-specific widgets use keys namespaced with the sanitized filename:
  - `f"filter_cols_{name}"`, `f"filter_vals_{name}_{col}"`, `f"rows_{name}"`, etc.
- `st.session_state.datasets` holds the canonical DataFrames.
- On upload refresh, remove datasets not present in the latest selection to avoid ghost tabs.

---

## File Handling
- CSV only. Use `pd.read_csv` with fallback to `encoding_errors="ignore"`.
- Strip BOM if present. Trim whitespace in column names.
- Reject files larger than a configured size threshold with a clear message.

---

## Core API Changes (`core.py`)
Add or confirm the following helpers to keep `app.py` thin:
- `read_csv_safe(file) -> pd.DataFrame`
- `sanitize_columns(df) -> pd.DataFrame`
- `unique_values(df, col, as_str=True) -> List[str]`
- `filter_dataframe(df, filters: Dict[col, List[str]]) -> pd.DataFrame`
- `pivot_table(df, rows, cols, values, agg) -> pd.DataFrame`
- `detect_numeric(df) -> List[str]`
- `to_csv_bytes(df) -> bytes` (for `st.download_button`)

These should be pure functions with unit tests.

---

## Changes to `app.py`
1. Initialize `st.session_state.datasets = {}` if missing.
2. Sidebar multi-uploader with `accept_multiple_files=True`.
3. Load each file to `datasets[name]` and drop stale entries not in current upload.
4. Build tabs with `st.tabs(list(datasets.keys()))`.
5. For each tab:
   - Preview with row count and column summary.
   - Filters → call `core.filter_dataframe`.
   - Pivot → call `core.pivot_table`.
   - Plot → use filtered or pivoted data. Detect numeric columns with `core.detect_numeric`.
   - Add “Download filtered CSV” and “Download pivot CSV” buttons when data exists.

---

## Validation & Error Handling
- Empty file → error.
- Duplicate column names → auto‑dedupe with suffixes.
- Non‑UTF8 → fallback decode.
- Pivot with non‑numeric values → force `count` only or warn.
- Large cardinality columns in Columns axis → warn about wide pivots.
- Missing values → fill with 0 for pivot display, document behavior.

---

## Performance Considerations
- Read files once. Store DataFrames in session.
- Avoid expensive `unique()` on very large columns unless a filter is opened.
- Consider lazy computation for pivot/plot, triggered by parameter changes.
- Limit preview to first N rows; provide total row count.

---

## Accessibility
- Clear section headings and helper text.
- Keyboard‑navigable widgets.
- Color‑agnostic charts by default; avoid encoding with color only.

---

## Testing Strategy
### Unit tests (`core.py`)
- `read_csv_safe` handles BOM and bad encodings.
- `sanitize_columns` trims and dedupes.
- `filter_dataframe` correct inclusion logic and dtype coercion.
- `pivot_table` all aggregations, missing values, multi-index shapes.
- `detect_numeric` correctness across mixed types.
- `to_csv_bytes` newline consistency across platforms.

### Integration tests (`app.py`)
- Upload two files → two tabs visible.
- Per‑tab state isolation (filters in Tab A do not alter Tab B).
- Pivot and plot actions run without error on sample CSVs.

### Manual QA checklist
- Upload 1, then 2, then remove 1 → tabs update correctly.
- Filtering string vs numeric columns works.
- Counts match expected after filters.
- Chart renders for each chart type.
- Downloaded CSVs open and match on‑screen data.

---

## Backward Compatibility & Migration
- Keep a single‑file path: if one file is uploaded, UX mirrors current behavior.
- Existing functions in `core.py` stay stable; only additive changes.
- No data persistence change.

---

## Security
- No file writes to server disk by default.
- Validate file extension and size.
- Never execute user content.

---

## Deliverables
- Updated `core.py` with helpers and tests.
- Updated `app.py` with multi‑file tabs and per‑tab flows.
- Sample CSVs for testing.
- README updates and screenshots.

---

## Acceptance Criteria
- Multiple CSVs can be uploaded at once.
- Each file gets its own tab with independent filter, pivot, and plot.
- No cross‑tab state leakage.
- All error states display actionable guidance.
- Unit and integration tests pass locally.
- README documents usage and limitations.

---

## Pseudocode
```python
# sidebar
files = st.file_uploader(..., accept_multiple_files=True)
datasets = {}
for f in files:
    df = core.read_csv_safe(f)
    df = core.sanitize_columns(df)
    datasets[f.name] = df
st.session_state.datasets = datasets

tabs = st.tabs(list(datasets.keys()))
for tab, name in zip(tabs, datasets):
    with tab:
        df = datasets[name]
        # preview
        st.dataframe(df.head(50))
        # filters
        selected_cols = st.multiselect(... key=f"filter_cols_{name}")
        filters = {}
        for c in selected_cols:
            vals = st.multiselect(... key=f"filter_vals_{name}_{c}")
            filters[c] = vals
        fdf = core.filter_dataframe(df, filters)
        # pivot
        rows = st.multiselect(... key=f"rows_{name}")
        cols = st.multiselect(... key=f"cols_{name}")
        values = st.multiselect(... key=f"vals_{name}")
        agg = st.selectbox(... key=f"agg_{name}")
        pvt = core.pivot_table(fdf, rows, cols, values, agg)
        st.dataframe(pvt_reset)
        # plot
        source = st.radio(... key=f"plot_src_{name}")
        plot_df = pvt_reset if source == "Pivot table" else fdf
        x = st.selectbox(... key=f"x_{name}")
        y = st.selectbox(... key=f"y_{name}")
        chart = st.selectbox(... key=f"chart_{name}")
        plot(plot_df, x, y, chart)
```

---

## Task Breakdown
- [ ] Add helpers in `core.py`.
- [ ] Write unit tests for helpers.
- [ ] Refactor `app.py` to session‑managed multi‑file tabs.
- [ ] Add CSV download buttons for filtered and pivot outputs.
- [ ] Add warnings for wide pivots and missing numerics.
- [ ] Write integration tests and a short QA script.
- [ ] Update README with screenshots and usage steps.

---

## Future Extensions
- XLSX/Parquet ingestion with `openpyxl` and `pyarrow`.
- Cross‑file joins and comparisons in separate tabs.
- Saved views and presets via query params or session export.
- Caching of heavy operations for large datasets.
