"""
Sandbox Executor for AI Transform.
Safely executes generated code with restricted globals and timeouts.
"""

import pandas as pd
import numpy as np
from typing import Tuple, Dict, Any
import signal
from contextlib import contextmanager
import io
from diff_tools import compute_diff


class TimeoutException(Exception):
    """Raised when code execution times out."""
    pass


@contextmanager
def timeout_handler(seconds: int):
    """
    Context manager for enforcing timeouts.

    Args:
        seconds: Timeout duration in seconds

    Raises:
        TimeoutException: If code execution exceeds timeout
    """
    def timeout_handler_fn(signum, frame):
        raise TimeoutException(f"Code execution timed out after {seconds} seconds")

    signal.signal(signal.SIGALRM, timeout_handler_fn)
    signal.alarm(seconds)
    try:
        yield
    finally:
        signal.alarm(0)  # Cancel the alarm


def dry_run(
    code: str,
    df: pd.DataFrame,
    sample_frac: float = 0.02,
    max_rows: int = 10000,
    timeout_sec: int = 10,
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Dry-run code on a sample of the DataFrame.

    Args:
        code: Python code with `def transform(df):` function
        df: Input DataFrame
        sample_frac: Fraction of rows to sample (e.g., 0.02 = 2%)
        max_rows: Maximum number of rows to include in sample
        timeout_sec: Timeout in seconds

    Returns:
        Tuple of (result_df, diff_dict)

    Raises:
        Exception: If code execution fails
    """
    # Create sample
    sample_size = min(int(len(df) * sample_frac), max_rows)
    sample_size = max(1, sample_size)  # At least 1 row
    df_sample = df.sample(n=min(sample_size, len(df)), random_state=42)

    try:
        result_df, _ = apply(code, df_sample, timeout_sec)
        diff = compute_diff(df_sample, result_df)
        return result_df, diff
    except Exception as e:
        raise Exception(f"Dry-run execution failed: {str(e)}")


def apply(
    code: str,
    df: pd.DataFrame,
    timeout_sec: int = 10,
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Apply code to full DataFrame.

    Args:
        code: Python code with `def transform(df):` function
        df: Input DataFrame
        timeout_sec: Timeout in seconds

    Returns:
        Tuple of (result_df, diff_dict)

    Raises:
        Exception: If code execution fails
    """
    # Create safe namespace with restricted globals
    safe_globals = {
        "pd": pd,
        "pandas": pd,
        "np": np,
        "numpy": np,
        "__builtins__": {
            "len": len,
            "range": range,
            "sum": sum,
            "min": min,
            "max": max,
            "abs": abs,
            "round": round,
            "str": str,
            "int": int,
            "float": float,
            "bool": bool,
            "list": list,
            "dict": dict,
            "tuple": tuple,
            "sorted": sorted,
            "reversed": reversed,
            "enumerate": enumerate,
            "zip": zip,
            "map": map,
            "filter": filter,
            "any": any,
            "all": all,
            "isinstance": isinstance,
            "type": type,
            "hasattr": hasattr,
            "getattr": getattr,
            "print": print,  # Allow print for debugging
        }
    }

    safe_locals = {}

    # Capture stderr to suppress unwanted output
    old_stderr = None
    try:
        old_stderr = io.StringIO()  # For now, we'll just let errors bubble up

        # Execute code with timeout (Unix-only)
        try:
            with timeout_handler(timeout_sec):
                exec(code, safe_globals, safe_locals)
        except TimeoutException:
            raise

        # Get the transform function
        if "transform" not in safe_locals:
            raise Exception("Code did not define 'transform' function")

        transform_fn = safe_locals["transform"]

        # Call the function
        result_df = transform_fn(df.copy())

        # Validate result
        if not isinstance(result_df, pd.DataFrame):
            raise Exception(
                f"transform() must return a DataFrame, got {type(result_df).__name__}"
            )

        # Check for extreme size changes (possible infinite loops or memory bombs)
        if len(result_df) > len(df) * 100:
            raise Exception(
                f"Result DataFrame is suspiciously large "
                f"({len(result_df)} rows vs input {len(df)} rows)"
            )

        # Compute diff
        diff = compute_diff(df, result_df)

        return result_df, diff

    except Exception as e:
        raise Exception(f"Code execution failed: {str(e)}")


def validate_execution_result(df_before: pd.DataFrame, df_after: pd.DataFrame) -> None:
    """
    Validate that the transformation is reasonable.

    Args:
        df_before: Original DataFrame
        df_after: Transformed DataFrame

    Raises:
        Exception: If result is invalid
    """
    if not isinstance(df_after, pd.DataFrame):
        raise Exception(f"Result must be a DataFrame, got {type(df_after)}")

    if df_after.empty and not df_before.empty:
        raise Exception("Transformation resulted in empty DataFrame")

    # Check for NaN explosion
    nan_ratio_before = df_before.isnull().sum().sum() / (
        len(df_before) * len(df_before.columns)
    ) if len(df_before) > 0 else 0
    nan_ratio_after = df_after.isnull().sum().sum() / (
        len(df_after) * len(df_after.columns)
    ) if len(df_after) > 0 else 0

    if nan_ratio_after > 0.9:
        raise Exception(
            f"Transformation produced DataFrame with {nan_ratio_after:.0%} NaN values"
        )
