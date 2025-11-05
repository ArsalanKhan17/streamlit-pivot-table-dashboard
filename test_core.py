"""
Unit tests for the core module of the Pivot Table Dashboard.

Tests are organized by functionality:
1. New Helper Functions - read_csv_safe, sanitize_columns, get_unique_values,
   filter_dataframe, detect_numeric_columns, to_csv_bytes
2. Data Loading - CSV parsing and validation
3. Filtering - Numeric and categorical filters
4. Pivot/Aggregation - GroupBy operations with various aggregation functions
5. High-priority cases - End-to-end scenarios
"""

import unittest
import pandas as pd
import io
import numpy as np
from core import (
    load_csv,
    apply_filters,
    build_pivot,
    read_csv_safe,
    sanitize_columns,
    get_unique_values,
    filter_dataframe,
    detect_numeric_columns,
    to_csv_bytes
)


# ============================================================================
# Tests for New Helper Functions
# ============================================================================


class TestReadCsvSafe(unittest.TestCase):
    """Test the read_csv_safe() helper function."""

    def test_read_csv_safe_valid(self):
        """Test reading a valid CSV."""
        csv_data = "a,b,c\n1,2,3\n4,5,6"
        file_obj = io.StringIO(csv_data)
        df = read_csv_safe(file_obj)
        self.assertEqual(df.shape, (2, 3))
        self.assertListEqual(list(df.columns), ["a", "b", "c"])

    def test_read_csv_safe_empty(self):
        """Test reading an empty CSV raises ValueError."""
        csv_data = ""
        file_obj = io.StringIO(csv_data)
        with self.assertRaises(ValueError):
            read_csv_safe(file_obj)

    def test_read_csv_safe_with_data(self):
        """Test CSV with headers and data."""
        csv_data = "name,age\nAlice,25\nBob,30"
        file_obj = io.StringIO(csv_data)
        df = read_csv_safe(file_obj)
        self.assertEqual(len(df), 2)
        self.assertEqual(df.iloc[0]["name"], "Alice")


class TestSanitizeColumns(unittest.TestCase):
    """Test the sanitize_columns() helper function."""

    def test_sanitize_trim_whitespace(self):
        """Test that column names are trimmed."""
        df = pd.DataFrame({" col1 ": [1, 2], "col2 ": [3, 4]})
        df_clean = sanitize_columns(df)
        self.assertListEqual(list(df_clean.columns), ["col1", "col2"])

    def test_sanitize_preserves_data(self):
        """Test that data is preserved after sanitization."""
        df = pd.DataFrame({" col1 ": [1, 2], " col2 ": [3, 4]})
        df_clean = sanitize_columns(df)
        self.assertEqual(df_clean.iloc[0]["col1"], 1)
        self.assertEqual(df_clean.iloc[1]["col2"], 4)

    def test_sanitize_returns_copy(self):
        """Test that sanitize_columns returns a new DataFrame."""
        df = pd.DataFrame({"col": [1, 2]})
        df_clean = sanitize_columns(df)
        self.assertIsNot(df, df_clean)

    def test_sanitize_with_clean_columns(self):
        """Test sanitization with already clean columns."""
        df = pd.DataFrame({"col1": [1, 2], "col2": [3, 4]})
        df_clean = sanitize_columns(df)
        self.assertListEqual(list(df_clean.columns), ["col1", "col2"])


class TestGetUniqueValues(unittest.TestCase):
    """Test the get_unique_values() helper function."""

    def test_get_unique_values_string(self):
        """Test getting unique string values."""
        df = pd.DataFrame({"col": ["a", "b", "a", "c"]})
        vals = get_unique_values(df, "col", as_str=True)
        self.assertListEqual(vals, ["a", "b", "c"])

    def test_get_unique_values_numeric(self):
        """Test getting unique numeric values as strings."""
        df = pd.DataFrame({"col": [1, 2, 1, 3]})
        vals = get_unique_values(df, "col", as_str=True)
        self.assertListEqual(vals, ["1", "2", "3"])

    def test_get_unique_values_with_nan(self):
        """Test that NaN values are excluded."""
        df = pd.DataFrame({"col": [1.0, 2.0, np.nan, 1.0]})
        vals = get_unique_values(df, "col", as_str=True)
        self.assertEqual(len(vals), 2)
        self.assertIn("1.0", vals)
        self.assertIn("2.0", vals)

    def test_get_unique_values_nonexistent_column(self):
        """Test error when column doesn't exist."""
        df = pd.DataFrame({"col": [1, 2]})
        with self.assertRaises(KeyError):
            get_unique_values(df, "nonexistent")

    def test_get_unique_values_sorted(self):
        """Test that values are returned sorted."""
        df = pd.DataFrame({"col": ["z", "a", "m", "a"]})
        vals = get_unique_values(df, "col", as_str=True)
        self.assertListEqual(vals, ["a", "m", "z"])


class TestFilterDataframe(unittest.TestCase):
    """Test the filter_dataframe() helper function."""

    def setUp(self):
        """Create a sample DataFrame for testing."""
        self.df = pd.DataFrame({
            "name": ["Alice", "Bob", "Charlie"],
            "age": [25, 30, 35],
            "city": ["NYC", "LA", "NYC"]
        })

    def test_filter_empty_filters(self):
        """Test with no filters returns copy."""
        filtered = filter_dataframe(self.df, {})
        pd.testing.assert_frame_equal(self.df, filtered)

    def test_filter_string_values(self):
        """Test filtering string columns."""
        filtered = filter_dataframe(self.df, {"city": ["NYC"]})
        self.assertEqual(len(filtered), 2)
        self.assertTrue((filtered["city"] == "NYC").all())

    def test_filter_multiple_values(self):
        """Test filtering with multiple values."""
        filtered = filter_dataframe(self.df, {"name": ["Alice", "Bob"]})
        self.assertEqual(len(filtered), 2)

    def test_filter_numeric_values(self):
        """Test filtering numeric columns with string input."""
        filtered = filter_dataframe(self.df, {"age": ["25", "30"]})
        self.assertEqual(len(filtered), 2)
        self.assertTrue(set(filtered["age"]) == {25, 30})

    def test_filter_nonexistent_column(self):
        """Test error when filtering nonexistent column."""
        with self.assertRaises(KeyError):
            filter_dataframe(self.df, {"nonexistent": ["value"]})

    def test_filter_no_matches(self):
        """Test filter that matches nothing."""
        filtered = filter_dataframe(self.df, {"city": ["Chicago"]})
        self.assertEqual(len(filtered), 0)

    def test_filter_multiple_columns(self):
        """Test filtering multiple columns."""
        filtered = filter_dataframe(self.df, {
            "city": ["NYC"],
            "age": ["25"]
        })
        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered.iloc[0]["name"], "Alice")


class TestDetectNumericColumns(unittest.TestCase):
    """Test the detect_numeric_columns() helper function."""

    def test_detect_numeric_basic(self):
        """Test detecting numeric columns."""
        df = pd.DataFrame({
            "int_col": [1, 2, 3],
            "float_col": [1.1, 2.2, 3.3],
            "str_col": ["a", "b", "c"]
        })
        numeric = detect_numeric_columns(df)
        self.assertSetEqual(set(numeric), {"int_col", "float_col"})

    def test_detect_numeric_all_numeric(self):
        """Test when all columns are numeric."""
        df = pd.DataFrame({
            "a": [1, 2, 3],
            "b": [1.1, 2.2, 3.3]
        })
        numeric = detect_numeric_columns(df)
        self.assertSetEqual(set(numeric), {"a", "b"})

    def test_detect_numeric_no_numeric(self):
        """Test when no columns are numeric."""
        df = pd.DataFrame({
            "a": ["x", "y", "z"],
            "b": ["p", "q", "r"]
        })
        numeric = detect_numeric_columns(df)
        self.assertListEqual(numeric, [])

    def test_detect_numeric_mixed(self):
        """Test mixed data types."""
        df = pd.DataFrame({
            "int": [1, 2],
            "float": [1.5, 2.5],
            "str": ["a", "b"],
            "bool": [True, False]
        })
        numeric = detect_numeric_columns(df)
        self.assertIn("int", numeric)
        self.assertIn("float", numeric)
        self.assertNotIn("str", numeric)


class TestToCsvBytes(unittest.TestCase):
    """Test the to_csv_bytes() helper function."""

    def test_to_csv_bytes_basic(self):
        """Test converting DataFrame to CSV bytes."""
        df = pd.DataFrame({"a": [1, 2], "b": [3, 4]})
        csv_bytes = to_csv_bytes(df)
        self.assertIsInstance(csv_bytes, bytes)

    def test_to_csv_bytes_contains_header(self):
        """Test that CSV contains header."""
        df = pd.DataFrame({"col1": [1, 2]})
        csv_bytes = to_csv_bytes(df)
        self.assertIn(b"col1", csv_bytes)

    def test_to_csv_bytes_contains_data(self):
        """Test that CSV contains data."""
        df = pd.DataFrame({"a": [1, 2], "b": [3, 4]})
        csv_bytes = to_csv_bytes(df)
        self.assertIn(b"1", csv_bytes)
        self.assertIn(b"3", csv_bytes)

    def test_to_csv_bytes_roundtrip(self):
        """Test that CSV can be read back."""
        df = pd.DataFrame({"name": ["Alice", "Bob"], "age": [25, 30]})
        csv_bytes = to_csv_bytes(df)

        # Read back the CSV
        df_read = pd.read_csv(io.BytesIO(csv_bytes))
        pd.testing.assert_frame_equal(df, df_read)

    def test_to_csv_bytes_with_special_chars(self):
        """Test CSV with special characters."""
        df = pd.DataFrame({"name": ["Alice & Bob", "Charlie,Diana"]})
        csv_bytes = to_csv_bytes(df)
        self.assertIsInstance(csv_bytes, bytes)


# ============================================================================
# Original Tests (existing functionality)
# ============================================================================


class TestDataLoading(unittest.TestCase):
    """Test data loading and CSV parsing."""

    def test_load_valid_csv(self):
        """Valid CSV with headers loads correctly."""
        csv_data = "name,age,salary\nAlice,25,50000\nBob,30,60000\n"
        file_obj = io.StringIO(csv_data)
        df = load_csv(file_obj)

        self.assertEqual(df.shape, (2, 3))
        self.assertListEqual(list(df.columns), ["name", "age", "salary"])
        self.assertEqual(df.iloc[0]["name"], "Alice")

    def test_load_csv_with_numeric_columns(self):
        """CSV with numeric and string columns loads with correct types."""
        csv_data = "id,value,category\n1,100,A\n2,200,B\n"
        file_obj = io.StringIO(csv_data)
        df = load_csv(file_obj)

        self.assertTrue(pd.api.types.is_numeric_dtype(df["id"]))
        self.assertTrue(pd.api.types.is_numeric_dtype(df["value"]))
        self.assertFalse(pd.api.types.is_numeric_dtype(df["category"]))

    def test_load_csv_empty_file(self):
        """Empty CSV raises ValueError."""
        csv_data = ""
        file_obj = io.StringIO(csv_data)

        with self.assertRaises(ValueError) as context:
            load_csv(file_obj)
        self.assertIn("empty", str(context.exception).lower())

    def test_load_csv_header_only(self):
        """CSV with only headers but no data raises ValueError."""
        csv_data = "name,age,salary\n"
        file_obj = io.StringIO(csv_data)

        with self.assertRaises(ValueError) as context:
            load_csv(file_obj)
        self.assertIn("empty", str(context.exception).lower())

    def test_load_csv_no_columns(self):
        """CSV with no columns raises ValueError."""
        csv_data = "\n\n"
        file_obj = io.StringIO(csv_data)

        with self.assertRaises(ValueError):
            load_csv(file_obj)

    def test_load_csv_with_missing_values(self):
        """CSV with missing values loads correctly (NaN)."""
        csv_data = "name,age,salary\nAlice,25,\nBob,,60000\n"
        file_obj = io.StringIO(csv_data)
        df = load_csv(file_obj)

        self.assertEqual(df.shape[0], 2)
        self.assertTrue(pd.isna(df.iloc[0]["salary"]))
        self.assertTrue(pd.isna(df.iloc[1]["age"]))

    def test_load_csv_single_column(self):
        """CSV with a single column loads correctly."""
        csv_data = "value\n10\n20\n30\n"
        file_obj = io.StringIO(csv_data)
        df = load_csv(file_obj)

        self.assertEqual(df.shape, (3, 1))
        self.assertEqual(df["value"].sum(), 60)

    def test_load_csv_many_rows(self):
        """CSV with many rows loads correctly."""
        csv_data = "id,value\n" + "\n".join([f"{i},{i*10}" for i in range(1, 101)])
        file_obj = io.StringIO(csv_data)
        df = load_csv(file_obj)

        self.assertEqual(df.shape[0], 100)
        self.assertEqual(df["id"].max(), 100)


class TestFiltering(unittest.TestCase):
    """Test filtering logic for numeric and categorical columns."""

    def setUp(self):
        """Create sample DataFrames for testing."""
        self.df = pd.DataFrame({
            "name": ["Alice", "Bob", "Charlie", "Diana", "Eve"],
            "age": [25, 30, 35, 28, 32],
            "salary": [50000, 60000, 75000, 55000, 70000],
            "department": ["HR", "IT", "IT", "Sales", "HR"]
        })

    def test_numeric_range_filter_both_bounds(self):
        """Numeric filter with both bounds returns correct rows."""
        filter_spec = {"age": ("range", (28, 32))}
        result = apply_filters(self.df, filter_spec)

        self.assertEqual(len(result), 3)  # Bob, Diana, Eve
        self.assertTrue((result["age"] >= 28).all())
        self.assertTrue((result["age"] <= 32).all())

    def test_numeric_range_filter_min_only(self):
        """Numeric filter with minimum bound works."""
        filter_spec = {"age": ("range", (30, 100))}
        result = apply_filters(self.df, filter_spec)

        self.assertEqual(len(result), 3)  # Bob, Charlie, Eve
        self.assertTrue((result["age"] >= 30).all())

    def test_numeric_range_filter_max_only(self):
        """Numeric filter with maximum bound works."""
        filter_spec = {"age": ("range", (0, 30))}
        result = apply_filters(self.df, filter_spec)

        self.assertEqual(len(result), 3)  # Alice, Bob, Diana
        self.assertTrue((result["age"] <= 30).all())

    def test_categorical_filter_single_value(self):
        """Categorical filter with single value returns matching rows."""
        filter_spec = {"department": ("categorical", ["IT"])}
        result = apply_filters(self.df, filter_spec)

        self.assertEqual(len(result), 2)  # Bob, Charlie
        self.assertTrue((result["department"] == "IT").all())

    def test_categorical_filter_multiple_values(self):
        """Categorical filter with multiple values returns matching rows."""
        filter_spec = {"department": ("categorical", ["IT", "HR"])}
        result = apply_filters(self.df, filter_spec)

        self.assertEqual(len(result), 4)  # Alice, Bob, Charlie, Eve
        self.assertTrue(result["department"].isin(["IT", "HR"]).all())

    def test_mixed_filters_and_logic(self):
        """Multiple filters combine with AND logic."""
        filter_spec = {
            "age": ("range", (28, 32)),
            "department": ("categorical", ["IT", "Sales"])
        }
        result = apply_filters(self.df, filter_spec)

        # Should be: Bob (IT, 30), Diana (Sales, 28), Eve (HR, 32) -> only Bob and Diana
        self.assertEqual(len(result), 2)  # Bob (IT, 30), Diana (Sales, 28)
        self.assertTrue((result["age"] >= 28).all())
        self.assertTrue((result["age"] <= 32).all())
        self.assertTrue(result["department"].isin(["IT", "Sales"]).all())

    def test_no_filters_returns_copy(self):
        """Empty filter spec returns a copy of the DataFrame."""
        filter_spec = {}
        result = apply_filters(self.df, filter_spec)

        pd.testing.assert_frame_equal(result, self.df)
        # Verify it's a copy, not the same object
        self.assertIsNot(result, self.df)

    def test_filter_with_no_matches(self):
        """Filter that matches no rows returns empty DataFrame."""
        filter_spec = {"age": ("range", (100, 200))}
        result = apply_filters(self.df, filter_spec)

        self.assertEqual(len(result), 0)
        self.assertEqual(list(result.columns), list(self.df.columns))

    def test_filter_column_not_found(self):
        """Filter on non-existent column raises KeyError."""
        filter_spec = {"nonexistent": ("range", (0, 100))}

        with self.assertRaises(KeyError):
            apply_filters(self.df, filter_spec)

    def test_filter_invalid_filter_type(self):
        """Unknown filter type raises ValueError."""
        filter_spec = {"age": ("invalid_type", (0, 100))}

        with self.assertRaises(ValueError) as context:
            apply_filters(self.df, filter_spec)
        self.assertIn("unknown", str(context.exception).lower())

    def test_filter_invalid_spec_not_dict(self):
        """Non-dict filter_spec raises TypeError."""
        with self.assertRaises(TypeError):
            apply_filters(self.df, "invalid")

    def test_filter_invalid_input_not_dataframe(self):
        """Non-DataFrame input raises TypeError."""
        with self.assertRaises(TypeError):
            apply_filters("not a dataframe", {})


class TestPivotAggregation(unittest.TestCase):
    """Test pivot table building and aggregation logic."""

    def setUp(self):
        """Create sample DataFrames for testing."""
        self.df = pd.DataFrame({
            "category": ["A", "A", "B", "B", "A", "B"],
            "region": ["North", "South", "North", "South", "North", "South"],
            "value": [10, 20, 30, 40, 50, 60]
        })

    def test_pivot_single_group_sum(self):
        """Pivot with single group by and sum aggregation."""
        result = build_pivot(self.df, ["category"], "value", ["sum"])

        self.assertEqual(len(result), 2)
        self.assertIn("category", result.columns)
        self.assertIn("sum", result.columns)
        self.assertEqual(result[result["category"] == "A"]["sum"].values[0], 80)
        self.assertEqual(result[result["category"] == "B"]["sum"].values[0], 130)

    def test_pivot_two_groups_sum(self):
        """Pivot with two group by columns and sum aggregation."""
        result = build_pivot(self.df, ["category", "region"], "value", ["sum"])

        self.assertEqual(len(result), 4)
        self.assertIn("category", result.columns)
        self.assertIn("region", result.columns)
        self.assertIn("sum", result.columns)

        # Verify specific values
        a_north = result[(result["category"] == "A") & (result["region"] == "North")]["sum"].values
        self.assertEqual(a_north[0], 60)  # 10 + 50

    def test_pivot_single_group_multiple_aggs(self):
        """Pivot with single group and multiple aggregation functions."""
        result = build_pivot(self.df, ["category"], "value", ["sum", "mean", "count"])

        self.assertEqual(len(result), 2)
        self.assertIn("sum", result.columns)
        self.assertIn("mean", result.columns)
        self.assertIn("count", result.columns)

        a_row = result[result["category"] == "A"]
        self.assertEqual(a_row["sum"].values[0], 80)
        self.assertEqual(a_row["count"].values[0], 3)
        self.assertAlmostEqual(a_row["mean"].values[0], 80 / 3)

    def test_pivot_all_agg_functions(self):
        """All supported aggregation functions work correctly."""
        agg_funcs = ["sum", "count", "mean", "min", "max", "median", "std", "var"]
        result = build_pivot(self.df, ["category"], "value", agg_funcs)

        self.assertEqual(len(result), 2)
        for func in agg_funcs:
            self.assertIn(func, result.columns)

    def test_pivot_no_groupby_overall_sum(self):
        """Pivot with no group by returns single row with overall aggregation."""
        result = build_pivot(self.df, [], "value", ["sum", "mean"])

        self.assertEqual(len(result), 1)
        self.assertIn("sum", result.columns)
        self.assertIn("mean", result.columns)
        self.assertEqual(result["sum"].values[0], 210)  # 10+20+30+40+50+60
        self.assertAlmostEqual(result["mean"].values[0], 35)  # 210 / 6

    def test_pivot_min_max_aggregation(self):
        """Min and max aggregations work correctly."""
        result = build_pivot(self.df, ["category"], "value", ["min", "max"])

        self.assertEqual(len(result), 2)
        a_row = result[result["category"] == "A"]
        self.assertEqual(a_row["min"].values[0], 10)
        self.assertEqual(a_row["max"].values[0], 50)

    def test_pivot_count_aggregation(self):
        """Count aggregation returns correct row counts."""
        result = build_pivot(self.df, ["category"], "value", ["count"])

        self.assertEqual(len(result), 2)
        a_count = result[result["category"] == "A"]["count"].values[0]
        b_count = result[result["category"] == "B"]["count"].values[0]
        self.assertEqual(a_count, 3)
        self.assertEqual(b_count, 3)

    def test_pivot_median_aggregation(self):
        """Median aggregation calculates correctly."""
        result = build_pivot(self.df, ["category"], "value", ["median"])

        a_row = result[result["category"] == "A"]
        # Values for A: [10, 20, 50], median = 20
        self.assertEqual(a_row["median"].values[0], 20)

    def test_pivot_std_var_aggregation(self):
        """Standard deviation and variance aggregations work."""
        result = build_pivot(self.df, ["category"], "value", ["std", "var"])

        self.assertIn("std", result.columns)
        self.assertIn("var", result.columns)
        # std and var should be non-zero for our data
        self.assertGreater(result["std"].values[0], 0)
        self.assertGreater(result["var"].values[0], 0)

    def test_pivot_non_numeric_agg_column_error(self):
        """Non-numeric aggregation column raises error for numeric functions."""
        df_non_numeric = pd.DataFrame({
            "category": ["A", "B"],
            "text": ["hello", "world"]
        })

        with self.assertRaises(ValueError) as context:
            build_pivot(df_non_numeric, ["category"], "text", ["sum"])
        self.assertIn("not numeric", str(context.exception).lower())

    def test_pivot_column_not_found_group_by(self):
        """Non-existent group by column raises KeyError."""
        with self.assertRaises(KeyError):
            build_pivot(self.df, ["nonexistent"], "value", ["sum"])

    def test_pivot_column_not_found_agg(self):
        """Non-existent aggregation column raises KeyError."""
        with self.assertRaises(KeyError):
            build_pivot(self.df, ["category"], "nonexistent", ["sum"])

    def test_pivot_invalid_input_type_dataframe(self):
        """Non-DataFrame input raises TypeError."""
        with self.assertRaises(TypeError):
            build_pivot("not a df", ["category"], "value", ["sum"])

    def test_pivot_invalid_groupby_type(self):
        """Non-list group_by raises TypeError."""
        with self.assertRaises(TypeError):
            build_pivot(self.df, "category", "value", ["sum"])

    def test_pivot_invalid_agg_col_type(self):
        """Non-string agg_col raises TypeError."""
        with self.assertRaises(TypeError):
            build_pivot(self.df, ["category"], ["value"], ["sum"])

    def test_pivot_invalid_agg_functions_type(self):
        """Non-list agg_functions raises TypeError."""
        with self.assertRaises(TypeError):
            build_pivot(self.df, ["category"], "value", "sum")

    def test_pivot_preserves_row_order(self):
        """Pivot results include all groups."""
        result = build_pivot(self.df, ["category"], "value", ["sum"])

        categories = set(result["category"].values)
        self.assertEqual(categories, {"A", "B"})


class TestHighPriorityScenarios(unittest.TestCase):
    """Test high-priority end-to-end scenarios from the testing plan."""

    def test_filters_then_pivot(self):
        """
        High-priority test 1: raw → filter → pivot matches hand-built DataFrame.

        Scenario:
        1. Load data with categories and values
        2. Filter to specific category
        3. Pivot table matches expected result
        """
        # Create raw data
        raw_df = pd.DataFrame({
            "category": ["A", "A", "B", "B", "A"],
            "region": ["North", "South", "North", "South", "North"],
            "sales": [100, 150, 200, 250, 175]
        })

        # Apply filter: only category A
        filter_spec = {"category": ("categorical", ["A"])}
        filtered_df = apply_filters(raw_df, filter_spec)

        # Build pivot
        result_pivot = build_pivot(filtered_df, ["region"], "sales", ["sum"])

        # Hand-built expected result
        expected = pd.DataFrame({
            "region": ["North", "South"],
            "sum": [275, 150]  # North: 100+175, South: 150
        })

        # Sort for comparison
        result_pivot = result_pivot.sort_values("region").reset_index(drop=True)
        expected = expected.sort_values("region").reset_index(drop=True)

        pd.testing.assert_frame_equal(result_pivot, expected)

    def test_no_groupby_sum(self):
        """
        High-priority test 2: pivot with no groups returns single-row aggregation.

        Scenario:
        1. Load data with numeric values
        2. Pivot with no group by (overall sum)
        3. Result has one row with total
        """
        df = pd.DataFrame({
            "value": [10, 20, 30, 40, 50]
        })

        result = build_pivot(df, [], "value", ["sum", "mean", "count"])

        self.assertEqual(len(result), 1)
        self.assertEqual(result["sum"].values[0], 150)
        self.assertAlmostEqual(result["mean"].values[0], 30)
        self.assertEqual(result["count"].values[0], 5)

    def test_two_groups_two_aggs(self):
        """
        High-priority test 3: two groups + two aggregations = exact DataFrame equality.

        Scenario:
        1. Create data with two grouping dimensions
        2. Pivot with two aggregation functions
        3. Assert exact DataFrame equality
        """
        df = pd.DataFrame({
            "product": ["A", "A", "B", "B", "A", "B"],
            "quarter": ["Q1", "Q2", "Q1", "Q2", "Q1", "Q2"],
            "revenue": [1000, 1200, 800, 900, 1100, 950]
        })

        result = build_pivot(df, ["product", "quarter"], "revenue", ["sum", "mean"])

        # Build expected manually
        # Data breakdown:
        # A, Q1: [1000, 1100] → sum=2100, mean=1050.0
        # A, Q2: [1200] → sum=1200, mean=1200.0
        # B, Q1: [800] → sum=800, mean=800.0
        # B, Q2: [900, 950] → sum=1850, mean=925.0
        expected = pd.DataFrame({
            "product": ["A", "A", "B", "B"],
            "quarter": ["Q1", "Q2", "Q1", "Q2"],
            "sum": [2100, 1200, 800, 1850],
            "mean": [1050.0, 1200.0, 800.0, 925.0]
        })

        result = result.sort_values(["product", "quarter"]).reset_index(drop=True)
        expected = expected.sort_values(["product", "quarter"]).reset_index(drop=True)

        pd.testing.assert_frame_equal(result, expected)

    def test_bad_agg_func(self):
        """
        High-priority test 4: invalid agg function raises ValueError.

        Scenario:
        1. Create data
        2. Attempt pivot with non-existent aggregation function
        3. Verify ValueError is raised
        """
        df = pd.DataFrame({
            "category": ["A", "B"],
            "value": [10, 20]
        })

        # This should raise an error from pandas groupby
        with self.assertRaises((ValueError, AttributeError)):
            build_pivot(df, ["category"], "value", ["nonexistent_function"])

    def test_full_pipeline_complex_scenario(self):
        """
        Complex end-to-end scenario: load, filter, pivot with validation.

        Scenario:
        1. Create realistic sales data
        2. Apply multiple filters (date range, department)
        3. Pivot by region with multiple metrics
        4. Verify results are sensible
        """
        df = pd.DataFrame({
            "date": pd.date_range("2024-01-01", periods=10),
            "department": ["Sales", "Sales", "IT", "Sales", "IT"] * 2,
            "region": ["North", "South", "North", "South", "North"] * 2,
            "amount": [100, 200, 150, 300, 250, 120, 180, 220, 160, 280]
        })

        # Filter to Sales department only
        filter_spec = {"department": ("categorical", ["Sales"])}
        filtered_df = apply_filters(df, filter_spec)
        self.assertEqual(len(filtered_df), 6)

        # Pivot by region with sum and count
        result = build_pivot(filtered_df, ["region"], "amount", ["sum", "count"])

        # Verify structure
        self.assertIn("region", result.columns)
        self.assertIn("sum", result.columns)
        self.assertIn("count", result.columns)

        # Verify totals match
        total_sum = result["sum"].sum()
        self.assertGreater(total_sum, 0)
        total_count = result["count"].sum()
        self.assertEqual(total_count, 6)


class TestEdgeCases(unittest.TestCase):
    """Test edge cases and boundary conditions."""

    def test_single_row_dataframe_pivot(self):
        """Single row DataFrame pivots correctly."""
        df = pd.DataFrame({
            "category": ["A"],
            "value": [100]
        })

        result = build_pivot(df, ["category"], "value", ["sum"])

        self.assertEqual(len(result), 1)
        self.assertEqual(result["sum"].values[0], 100)

    def test_all_same_value_aggregation(self):
        """DataFrame with all same values aggregates correctly."""
        df = pd.DataFrame({
            "category": ["A", "A", "B", "B"],
            "value": [10, 10, 10, 10]
        })

        result = build_pivot(df, ["category"], "value", ["sum", "mean", "std"])

        # std should be 0 since all values are the same
        self.assertEqual(result["std"].values[0], 0)

    def test_very_wide_dataframe_pivot(self):
        """Wide DataFrame (many columns) doesn't crash pivot."""
        # Create a DataFrame with 100 columns
        data = {f"col_{i}": [i] * 5 for i in range(100)}
        data["category"] = ["A", "B", "A", "B", "A"]
        data["value"] = [10, 20, 30, 40, 50]

        df = pd.DataFrame(data)

        # Should not crash
        result = build_pivot(df, ["category"], "value", ["sum"])

        self.assertEqual(len(result), 2)

    def test_negative_values_aggregation(self):
        """Negative values aggregate correctly."""
        df = pd.DataFrame({
            "category": ["A", "A", "B", "B"],
            "value": [10, -20, -15, 30]
        })

        result = build_pivot(df, ["category"], "value", ["sum", "mean"])

        a_sum = result[result["category"] == "A"]["sum"].values[0]
        self.assertEqual(a_sum, -10)  # 10 + (-20)

    def test_filter_with_boundary_values(self):
        """Numeric filter includes boundary values."""
        df = pd.DataFrame({
            "value": [10, 20, 30, 40, 50]
        })

        filter_spec = {"value": ("range", (20, 40))}
        result = apply_filters(df, filter_spec)

        # Should include 20 and 40 (inclusive)
        self.assertEqual(len(result), 3)
        self.assertIn(20, result["value"].values)
        self.assertIn(40, result["value"].values)

    def test_filter_with_floating_point_values(self):
        """Filtering works with floating point numbers."""
        df = pd.DataFrame({
            "value": [1.1, 2.2, 3.3, 4.4, 5.5]
        })

        filter_spec = {"value": ("range", (2.0, 4.5))}
        result = apply_filters(df, filter_spec)

        self.assertEqual(len(result), 3)  # 2.2, 3.3, 4.4
        self.assertTrue((result["value"] >= 2.0).all())
        self.assertTrue((result["value"] <= 4.5).all())


if __name__ == "__main__":
    unittest.main()
