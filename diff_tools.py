"""
Diff Tools for AI Transform.
Compares DataFrames and generates human-readable diffs.
"""

import pandas as pd
from typing import Dict, List, Any


def schema_snapshot(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Create a snapshot of DataFrame schema.

    Args:
        df: Input DataFrame

    Returns:
        Dictionary with schema information
    """
    if df.empty:
        sample_values = {col: None for col in df.columns}
    else:
        sample_values = df.iloc[0].to_dict()

    schema = {
        "columns": df.columns.tolist(),
        "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
        "nrows": len(df),
        "null_rates": (df.isnull().sum() / len(df)).to_dict() if len(df) > 0 else {},
        "sample_values": sample_values,
    }
    return schema


def compute_diff(df_before: pd.DataFrame, df_after: pd.DataFrame) -> Dict[str, Any]:
    """
    Compute differences between two DataFrames.

    Args:
        df_before: DataFrame before transformation
        df_after: DataFrame after transformation

    Returns:
        Dictionary with diff information
    """
    schema_before = schema_snapshot(df_before)
    schema_after = schema_snapshot(df_after)

    # Row count change
    rows_delta = len(df_after) - len(df_before)

    # Column changes
    cols_before = set(schema_before["columns"])
    cols_after = set(schema_after["columns"])

    cols_added = sorted(list(cols_after - cols_before))
    cols_removed = sorted(list(cols_before - cols_after))

    # Column renamings (heuristic: same position, similar names)
    renamed = {}
    # This is a simple heuristic; could be improved
    if len(cols_removed) == len(cols_added) and len(cols_removed) == 1:
        old_name = cols_removed[0]
        new_name = cols_added[0]
        # Check if they're at similar positions
        old_idx = schema_before["columns"].index(old_name)
        new_idx = schema_after["columns"].index(new_name)
        if old_idx == new_idx:
            renamed[old_name] = new_name
            cols_removed.remove(old_name)
            cols_added.remove(new_name)

    # Dtype changes
    common_cols = cols_before & cols_after
    dtype_changes = {}
    for col in common_cols:
        if schema_before["dtypes"][col] != schema_after["dtypes"][col]:
            dtype_changes[col] = {
                "before": schema_before["dtypes"][col],
                "after": schema_after["dtypes"][col],
            }

    # New columns sample
    new_columns_sample = {}
    for col in cols_added:
        if not df_after.empty:
            new_columns_sample[col] = df_after[col].head(3).tolist()

    diff = {
        "rows_delta": rows_delta,
        "cols_added": cols_added,
        "cols_removed": cols_removed,
        "renamed": renamed,
        "dtype_changes": dtype_changes,
        "new_columns_sample": new_columns_sample,
    }

    return diff


def format_diff_for_display(diff: Dict[str, Any]) -> str:
    """
    Format diff as human-readable text.

    Args:
        diff: Diff dictionary from compute_diff

    Returns:
        Formatted text
    """
    lines = []

    # Row changes
    if diff["rows_delta"] != 0:
        symbol = "+" if diff["rows_delta"] > 0 else ""
        lines.append(f"📊 Rows: {symbol}{diff['rows_delta']}")

    # Column additions
    if diff["cols_added"]:
        lines.append(f"✨ Columns Added: {', '.join(diff['cols_added'])}")

    # Column removals
    if diff["cols_removed"]:
        lines.append(f"🗑️  Columns Removed: {', '.join(diff['cols_removed'])}")

    # Column renames
    if diff["renamed"]:
        renames = [f"{old} → {new}" for old, new in diff["renamed"].items()]
        lines.append(f"🔄 Columns Renamed: {', '.join(renames)}")

    # Dtype changes
    if diff["dtype_changes"]:
        changes = [
            f"{col}: {info['before']} → {info['after']}"
            for col, info in diff["dtype_changes"].items()
        ]
        lines.append(f"🔧 Type Changes: {', '.join(changes)}")

    # New columns sample
    if diff["new_columns_sample"]:
        lines.append("\n📌 Sample Values in New Columns:")
        for col, samples in diff["new_columns_sample"].items():
            lines.append(f"  • {col}: {samples}")

    return "\n".join(lines) if lines else "No changes detected"
