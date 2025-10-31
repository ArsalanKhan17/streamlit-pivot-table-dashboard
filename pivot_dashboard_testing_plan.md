# Testing Plan for the Pivot Table Dashboard

Test the logic, not the Streamlit widgets.

## 1. Data loading/parsing
- CSV with headers loads to a DataFrame.
- Empty or invalid CSV is handled gracefully.
- Columns are inferred as expected.

## 2. Filtering engine
- Numeric filter returns rows within bounds.
- Categorical multiselect returns the expected set (intersection or union, as defined).
- Mixed filters combine correctly (AND).
- No-filter path returns the original DataFrame.

## 3. Pivot/core aggregation
- Given a DataFrame, `group_by=["A", "B"]`, `agg_col="value"`, `agg_func=["sum", "mean"]` returns the expected table.
- Test 1 grouping column vs 2+ grouping columns.
- Non-numeric `agg_col` with numeric functions is raised/handled.
- All aggregations supported in the app produce correct results.

## 4. Chart generation layer
- Given a small pivot DataFrame, the chart builder returns a Plotly figure object.
- Unsupported chart types fail predictably.
- Multiindex / wide pivot does not crash the figure builder.

## 5. Export helpers
- CSV export returns bytes/string with the correct header order.
- Other export functions return content even for small DataFrames.
- Mock external dependencies (e.g. PNG/Kaleido).

## 6. Session state isolation
- With no upload, the app does not access `st.session_state.df`.
- After upload, changing filters updates `filtered_df` but not the original DataFrame.

## 7. Error/edge cases
- Empty DataFrame after filtering shows a “no data” state but does not crash.
- Missing columns selected in pivot (e.g. user re-uploaded a different file) is handled.
- Very wide CSV still builds pivot configuration options.

## 8. Dependency-sensitive tests
- Pin versions in tests to match `requirements.txt` to avoid API drift (Streamlit, Plotly, Pandas).

## 9. Structure for testability
- Move pure logic to a separate module (e.g. `core.py`):
  - `load_csv(file) -> df`
  - `apply_filters(df, filter_spec) -> df`
  - `build_pivot(df, group_by, agg_col, agg_funcs) -> df`
  - `build_chart(pivot_df, chart_type, config) -> fig`
- Unit test the pure functions.
- Write a single integration test for the Streamlit app to ensure it runs.

## 10. High-priority test cases
1. **filters_then_pivot**: raw → filter → pivot matches a hand-built DataFrame.
2. **no_groupby_sum**: pivot with no groups returns a single-row aggregation.
3. **two_groups_two_aggs**: assert exact DataFrame equality.
4. **bad_agg_func**: raises `ValueError`.

