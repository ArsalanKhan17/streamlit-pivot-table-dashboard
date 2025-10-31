# Pivot Table Dashboard - Architecture Overview

## Project Structure

After refactoring for testability:

```
streamlit/
├── app.py                      # Streamlit UI layer (350 lines)
├── core.py                     # Business logic layer (NEW - 150 lines)
├── test_core.py               # Test suite (NEW - 850+ lines, 74 tests)
├── requirements.txt            # Python dependencies
├── pivot_dashboard_testing_plan.md  # Original testing plan
├── TEST_SUITE_SUMMARY.md      # Test documentation
├── TESTING_GUIDE.md           # How to run tests
└── ARCHITECTURE.md            # This file
```

## Layered Architecture

### Layer 1: UI Layer (app.py)
**Purpose**: Streamlit interface and user interaction
**Responsibilities**:
- File upload handling
- Widget rendering (sliders, multiselects, dropdowns)
- Session state management
- Chart rendering and visualization
- Download functionality
- Error display to users

**Key Components**:
- File uploader widget
- Filter UI generation
- Pivot configuration UI
- Chart type selection
- Export buttons

### Layer 2: Business Logic Layer (core.py)
**Purpose**: Data transformation and computation
**Responsibilities**:
- CSV parsing and validation
- Data filtering
- Pivot table generation
- Data aggregation

**Key Components**:
```
load_csv(file_obj) → DataFrame
  ├─ Parse CSV
  ├─ Validate not empty
  └─ Handle errors gracefully

apply_filters(df, filter_spec) → DataFrame
  ├─ Apply numeric range filters
  ├─ Apply categorical filters
  ├─ Combine with AND logic
  └─ Return filtered copy

build_pivot(df, group_by, agg_col, agg_funcs) → DataFrame
  ├─ Validate columns exist
  ├─ Check numeric compatibility
  ├─ Handle empty grouping
  └─ Perform aggregation
```

### Layer 3: Test Layer (test_core.py)
**Purpose**: Verify business logic correctness
**Responsibilities**:
- Unit test pure functions
- Test error handling
- Test edge cases
- Verify expected behavior

**Coverage**: 74 test cases across 6 test classes

## Data Flow

### Original (Monolithic) Flow
```
User Upload CSV
    ↓
app.py: Load CSV
    ↓
app.py: Generate Filter UI
    ↓
app.py: Apply Filters
    ↓
app.py: Generate Pivot Config UI
    ↓
app.py: Build Pivot
    ↓
app.py: Generate Chart
    ↓
app.py: Render to User
```

### Refactored (Layered) Flow
```
User Upload CSV
    ↓
app.py: UI Handling
    ↓ (passes file object)
core.py: load_csv()
    ↓ (returns DataFrame)
app.py: Render Preview
    ↓
app.py: Generate Filter UI
    ↓ (collects user selections)
core.py: apply_filters()
    ↓ (returns filtered DataFrame)
app.py: Display Filtered Data
    ↓
app.py: Generate Pivot Config UI
    ↓ (collects user selections)
core.py: build_pivot()
    ↓ (returns aggregated DataFrame)
app.py: Generate Chart
    ↓
app.py: Render to User
```

## Testing Strategy

### Unit Tests (test_core.py)
Test pure business logic in isolation:
- Input: Various DataFrames, filter specs, parameters
- Process: Call core functions
- Output: Verify returned DataFrames are correct

**Advantages**:
- Fast execution (< 1 second)
- No Streamlit dependency
- Easy to run in CI/CD
- Deterministic results

### Integration Tests (Optional)
Test full app flow with Streamlit:
- Could use `streamlit.testing.v1` API
- Would test UI and logic together
- More complex, slower execution

### Current Implementation
- ✅ Comprehensive unit tests (core.py)
- ✅ High-priority scenarios covered
- 📋 Integration tests not included (UI-heavy, requires Streamlit test SDK)

## Dependency Isolation

### core.py Dependencies
```python
import pandas as pd
import io
```
- Only standard libraries + pandas
- No Streamlit dependency
- Can run tests on any Python environment

### app.py Dependencies
```python
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import io
from datetime import datetime
from core import load_csv, apply_filters, build_pivot
```
- Full Streamlit stack
- Imports core functions for business logic

## Error Handling

### In core.py (Testable)
```
CSV Loading Errors:
  ├─ Empty file → ValueError
  ├─ No columns → ValueError
  └─ Parse error → ValueError

Filter Errors:
  ├─ Column not found → KeyError
  ├─ Invalid filter type → ValueError
  └─ Wrong input type → TypeError

Pivot Errors:
  ├─ Column not found → KeyError
  ├─ Non-numeric agg → ValueError
  └─ Wrong parameter type → TypeError
```

### In app.py (User-Facing)
```
File Upload Errors:
  └─ Display with st.error()

Filter Errors:
  └─ Fallback to original DataFrame + st.error()

Pivot Errors:
  └─ Display with st.error()
```

## Backward Compatibility

✅ **100% Backward Compatible**

The refactoring changes only the implementation, not the interface:

**Before and After Behavior**:
- Same UI/UX
- Same features
- Same session state variables
- Same error messages (improved)
- Same export options

**What Changed**:
- CSV loading moved to `core.load_csv()`
- Filtering moved to `core.apply_filters()`
- Pivot building moved to `core.build_pivot()`
- Added error handling in app.py

## Performance Characteristics

### Time Complexity
| Operation | Complexity | Notes |
|-----------|-----------|-------|
| CSV Load | O(n*m) | n=rows, m=columns |
| Numeric Filter | O(n) | Single pass over rows |
| Categorical Filter | O(n) | Uses isin() lookup |
| Multi-Filter | O(k*n) | k=filters, applied sequentially |
| Pivot/GroupBy | O(n*log n) | Pandas optimized groupby |
| Overall Pipeline | O(n*log n) | Dominated by groupby |

### Space Complexity
| Operation | Complexity | Notes |
|-----------|-----------|-------|
| CSV Load | O(n*m) | Full DataFrame in memory |
| Filters | O(n*m) | Copy of DataFrame |
| Pivot | O(g*m) | g=number of groups |

**Practical Limits**:
- Tested with 100+ columns, 1000+ rows
- Should handle 100k+ rows (depends on RAM)
- Not suitable for multi-GB datasets

## Scalability Considerations

### Current Limitations
1. **Memory**: Entire CSV loaded into memory
2. **Processing**: All operations synchronous
3. **Groups**: Visualization limited to 2 grouping dimensions

### Future Improvements
1. **Streaming**: Process CSVs in chunks
2. **Caching**: Memoize intermediate results
3. **Async**: Background task processing
4. **Sampling**: Visualize large datasets via sampling

## Maintenance Notes

### Adding New Aggregation Functions
1. Add function name to options list in app.py (line 127)
2. Add test in `TestPivotAggregation` class
3. Function must be supported by pandas `.agg()`

### Adding New Filters
1. Add UI widget in app.py filter loop
2. Add filter logic to `apply_filters()` in core.py
3. Add tests in `TestFiltering` class

### Adding New Export Formats
1. Add download button in app.py (Section 6)
2. Add export logic as separate function
3. Add tests for export format validation

## Development Workflow

### Making Changes
1. **Feature Development**:
   - Implement feature in appropriate layer (core.py or app.py)
   - Add corresponding tests
   - Run test suite: `python -m unittest test_core -v`
   - Test UI: `streamlit run app.py`

2. **Bug Fixes**:
   - Write test that reproduces bug
   - Fix bug in appropriate layer
   - Verify test passes

3. **Refactoring**:
   - Run test suite before: `python -m unittest test_core -v`
   - Make refactoring changes
   - Run test suite after: `python -m unittest test_core -v`
   - Ensure both pass

### Testing Checklist
- [ ] All unit tests pass
- [ ] App runs without errors
- [ ] File upload works
- [ ] Filters work correctly
- [ ] Pivot table calculates correctly
- [ ] Charts render properly
- [ ] Export options function
- [ ] Error messages are helpful

## Documentation Map

| Document | Purpose |
|----------|---------|
| app.py | Streamlit application code |
| core.py | Business logic implementation |
| test_core.py | Unit test suite |
| TEST_SUITE_SUMMARY.md | Overview of test coverage |
| TESTING_GUIDE.md | How to run and write tests |
| ARCHITECTURE.md | This file - system design |
| pivot_dashboard_testing_plan.md | Original testing requirements |

---

**Summary**: The refactored application maintains 100% of original functionality while enabling comprehensive testing through separation of business logic (core.py) from UI logic (app.py).
