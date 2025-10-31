"""
Core business logic for the Pivot Table Dashboard.
This module contains pure functions that are independent of Streamlit.
All data transformations and computations happen here.
"""

import pandas as pd
import io


def load_csv(file_obj):
    """
    Load and parse a CSV file into a pandas DataFrame.

    Args:
        file_obj: A file-like object (BytesIO or file handle) or file path

    Returns:
        pd.DataFrame: The loaded data

    Raises:
        ValueError: If the CSV is empty or invalid
        Exception: If pandas cannot parse the file
    """
    try:
        df = pd.read_csv(file_obj)

        if df.empty:
            raise ValueError("CSV file is empty")

        if len(df.columns) == 0:
            raise ValueError("CSV file has no columns")

        return df
    except pd.errors.EmptyDataError:
        raise ValueError("CSV file is empty")
    except pd.errors.ParserError as e:
        raise ValueError(f"CSV parsing error: {str(e)}")


def apply_filters(df, filter_spec):
    """
    Apply a set of filters to a DataFrame.

    Filters are combined using AND logic (all must be satisfied).

    Args:
        df: Input DataFrame
        filter_spec: Dictionary where keys are column names and values are tuples of:
                     - ("range", (min_val, max_val)) for numeric columns
                     - ("categorical", [list of values]) for categorical columns

    Returns:
        pd.DataFrame: Filtered DataFrame

    Raises:
        KeyError: If a filter column doesn't exist in the DataFrame
        TypeError: If filter_spec is not properly formatted
    """
    if not isinstance(df, pd.DataFrame):
        raise TypeError("First argument must be a DataFrame")

    if not isinstance(filter_spec, dict):
        raise TypeError("filter_spec must be a dictionary")

    filtered_df = df.copy()

    for col, (filter_type, values) in filter_spec.items():
        if col not in filtered_df.columns:
            raise KeyError(f"Column '{col}' not found in DataFrame")

        if filter_type == "range":
            min_val, max_val = values
            filtered_df = filtered_df[
                (filtered_df[col] >= min_val) & (filtered_df[col] <= max_val)
            ]
        elif filter_type == "categorical":
            filtered_df = filtered_df[filtered_df[col].isin(values)]
        else:
            raise ValueError(f"Unknown filter type: {filter_type}")

    return filtered_df


def build_pivot(df, group_by, agg_col, agg_functions):
    """
    Build a pivot table (grouped aggregation) from a DataFrame.

    Args:
        df: Input DataFrame
        group_by: List of column names to group by. Can be empty for overall aggregation.
        agg_col: Name of the column to aggregate
        agg_functions: List of aggregation function names (e.g., ["sum", "mean", "count"])
                       Supports: sum, count, mean, min, max, median, std, var

    Returns:
        pd.DataFrame: Aggregated DataFrame with group_by columns and aggregation results

    Raises:
        ValueError: If agg_col is not numeric when using numeric functions
        KeyError: If group_by or agg_col columns don't exist
        TypeError: If arguments are of wrong type
    """
    if not isinstance(df, pd.DataFrame):
        raise TypeError("First argument must be a DataFrame")

    if not isinstance(group_by, list):
        raise TypeError("group_by must be a list")

    if not isinstance(agg_col, str):
        raise TypeError("agg_col must be a string")

    if not isinstance(agg_functions, list):
        raise TypeError("agg_functions must be a list")

    # Validate columns exist
    if agg_col not in df.columns:
        raise KeyError(f"Aggregation column '{agg_col}' not found in DataFrame")

    for col in group_by:
        if col not in df.columns:
            raise KeyError(f"Group by column '{col}' not found in DataFrame")

    # Validate that agg_col is numeric for numeric aggregation functions
    numeric_agg_funcs = {"sum", "mean", "min", "max", "median", "std", "var"}
    requested_numeric_funcs = set(agg_functions) & numeric_agg_funcs

    if requested_numeric_funcs and not pd.api.types.is_numeric_dtype(df[agg_col]):
        raise ValueError(
            f"Column '{agg_col}' is not numeric but numeric aggregation functions "
            f"were requested: {requested_numeric_funcs}"
        )

    # Handle empty group_by (overall aggregation)
    if not group_by:
        result = pd.DataFrame(df[agg_col].agg(agg_functions)).T
        return result

    # Perform the groupby aggregation
    pivot_df = df.groupby(group_by, as_index=False)[agg_col].agg(agg_functions)

    return pivot_df
