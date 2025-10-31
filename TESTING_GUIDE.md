# Quick Testing Guide

## Installation

No additional dependencies needed! The test suite uses Python's built-in `unittest` module.

Your project already has the required dependencies in `requirements.txt`:
- pandas ≥ 2.0.0
- streamlit ≥ 1.28.0
- plotly ≥ 5.0.0

## Setup: Activate Virtual Environment

**Always activate the venv before running tests!** This ensures you're using the correct dependency versions.

```bash
# Navigate to project directory
cd /Users/arsalankhan/Documents/streamlit

# Activate virtual environment
source venv/bin/activate  # On macOS/Linux
# OR on Windows:
# venv\Scripts\activate

# Verify activation (should show "venv" in prompt)
# (venv) arsalankhan@MacBook streamlit %
```

## Running Tests

### Run All Tests (with venv activated)
```bash
# Make sure venv is activated first!
python -m unittest test_core -v
```

### Run Specific Test Class
```bash
# Test data loading
python -m unittest test_core.TestDataLoading -v

# Test filtering
python -m unittest test_core.TestFiltering -v

# Test pivot/aggregation
python -m unittest test_core.TestPivotAggregation -v

# Test high-priority scenarios
python -m unittest test_core.TestHighPriorityScenarios -v

# Test edge cases
python -m unittest test_core.TestEdgeCases -v
```

### Run Single Test
```bash
python -m unittest test_core.TestDataLoading.test_load_valid_csv -v
```

### Run Quietly (No Output)
```bash
python -m unittest test_core
```

## Using Virtual Environment

### Why Use venv?
- ✅ Isolated environment specific to this project
- ✅ Reproducible dependency versions (from requirements.txt)
- ✅ Won't affect system Python or other projects
- ✅ Matches production environment
- ✅ Easy CI/CD integration

### Check venv Status

```bash
# See which Python you're using
which python

# Should show: /Users/arsalankhan/Documents/streamlit/venv/bin/python
# If it shows system Python path, venv is not activated!

# Check installed packages
pip list

# Should show: pandas, streamlit, plotly versions from requirements.txt
```

### Typical Test Workflow

```bash
# Step 1: Open new terminal and navigate to project
cd /Users/arsalankhan/Documents/streamlit

# Step 2: Activate venv
source venv/bin/activate

# Step 3: Run tests
python -m unittest test_core -v

# Step 4: Verify all pass, then make code changes

# Step 5: Run tests again to verify changes don't break anything
python -m unittest test_core -v

# Step 6: When done, deactivate venv (optional)
deactivate
```

## Expected Output

```
test_all_agg_functions (test_core.TestPivotAggregation) ... ok
test_apply_filters (test_core.TestFiltering) ... ok
test_bad_agg_func (test_core.TestHighPriorityScenarios) ... ok
...
----------------------------------------------------------------------
Ran 74 tests in 0.345s

OK
```

## Verify App Still Works

After refactoring, the app should work exactly as before:

```bash
streamlit run app.py
```

Then upload a CSV file and test:
1. Data preview loads correctly
2. Filters work
3. Pivot table calculates correctly
4. Charts generate
5. Export options work

## Test Coverage by Scenario

### 1. Data Loading (8 tests)
```
✓ Valid CSV files
✓ Type inference (numeric vs categorical)
✓ Empty file error handling
✓ Missing values (NaN)
✓ Single column CSV
✓ Large datasets (100+ rows)
```

### 2. Filtering (10 tests)
```
✓ Numeric range filters (min, max, both)
✓ Categorical multiselect
✓ Combined filters (AND logic)
✓ No filters (returns copy)
✓ Empty results
✓ Error cases (missing columns, invalid types)
```

### 3. Pivot & Aggregation (14 tests)
```
✓ Single grouping column
✓ Multiple grouping columns
✓ All aggregation functions:
  - sum, count, mean, min, max
  - median, std, var
✓ Overall aggregation (no groups)
✓ Error handling for non-numeric columns
```

### 4. High-Priority Cases (5 tests)
```
✓ Test 1: Raw → Filter → Pivot pipeline
✓ Test 2: No grouping returns single row
✓ Test 3: Two groups + two aggs exact equality
✓ Test 4: Bad aggregation function raises error
✓ Test 5: Full realistic workflow
```

### 5. Edge Cases (7 tests)
```
✓ Single row DataFrames
✓ Identical values (std=0)
✓ Very wide DataFrames
✓ Negative numbers
✓ Floating point values
✓ Boundary filtering (inclusive)
```

## Understanding Test Names

Test method names follow this pattern:
```
test_[what_is_being_tested]_[condition_or_scenario]

Examples:
- test_load_valid_csv
- test_numeric_range_filter_both_bounds
- test_pivot_no_groupby_overall_sum
- test_filters_then_pivot
```

## Interpreting Results

### Success
```
OK
Ran 74 tests in 0.XXs
```

### Failure Example
```
FAIL: test_pivot_single_group_sum
Traceback:
  ...
AssertionError: 80 != 75

FAILED (failures=1)
Ran 74 tests in 0.XXs
```

## Common Issues & Solutions

### Issue: ModuleNotFoundError or ImportError
**Solution**: Make sure venv is activated:
```bash
# Check if venv is activated (look for (venv) in your prompt)
# If not, activate it:
source venv/bin/activate

# Verify you're using venv's Python:
which python
# Should show: /Users/arsalankhan/Documents/streamlit/venv/bin/python
```

### Issue: Import Error for `core` module
**Solution**: Make sure you're in the correct directory AND venv is activated:
```bash
cd /Users/arsalankhan/Documents/streamlit
source venv/bin/activate
python -m unittest test_core -v
```

### Issue: Pandas version mismatch
**Solution**: Check your pandas version:
```bash
python -c "import pandas as pd; print(pd.__version__)"
```
Should be ≥ 2.0.0

### Issue: Test hangs or times out
**Solution**: This is unlikely. If it happens, press Ctrl+C to stop and check for:
- Infinite loops in your test data
- File I/O issues
- Memory issues with large test datasets

## Adding New Tests

To add a test to the suite:

1. Add it to the appropriate test class in `test_core.py`
2. Follow the naming convention: `test_[description]`
3. Include a docstring explaining what's being tested
4. Use assertions to verify behavior

Example:
```python
def test_my_new_feature(self):
    """Brief description of what this test verifies."""
    # Arrange
    df = pd.DataFrame({"col": [1, 2, 3]})

    # Act
    result = some_function(df)

    # Assert
    self.assertEqual(len(result), 3)
```

## Continuous Testing

For continuous development, run tests after making changes:

```bash
# Terminal 1: Run app
streamlit run app.py

# Terminal 2: Run tests in watch mode (auto-run on file change)
# Using pytest (if installed)
pytest test_core.py -v --tb=short --watch

# Or manually re-run tests after changes
python -m unittest test_core -v
```

## Next Steps

1. ✅ Read this guide
2. ✅ Run all tests to verify setup
3. ✅ Test the app (streamlit run app.py)
4. ✅ Try running specific test classes
5. ✅ Add new tests as you add features

Happy testing! 🧪
