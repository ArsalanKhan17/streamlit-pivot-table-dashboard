# Phase 0: AI Transform Tab Skeleton - Completed

**Date:** 2025-11-05
**Status:** ✅ Complete - Ready for Phase 1

## What Was Built

### 1. **New Python Modules**

#### `llm_orchestrator.py`
- LLM orchestration with LangChain
- OpenAI provider integration (foundation for local/other vendors)
- Prompt building with schema context
- Code extraction from markdown blocks
- Code structure validation
- **Status:** Ready for Phase 1 implementation

#### `code_sanitizer.py`
- AST-based code security validation
- Allow-list for pandas/numpy/python operations
- Blocks: imports, file I/O, dunder methods, dangerous functions
- Returns detailed violation messages
- **Status:** Ready for use in Phase 2

#### `sandbox_executor.py`
- Safe code execution with restricted globals
- Timeout handler (Unix-only signal-based)
- `dry_run()` - Execute on sample (2% default)
- `apply()` - Execute on full DataFrame
- Extreme size change detection
- **Status:** Ready for use in Phase 2

#### `diff_tools.py`
- `schema_snapshot()` - Capture DataFrame schema (also added to core.py)
- `compute_diff()` - Compare before/after DataFrames
- Detects: row count changes, column additions/removals, renames, dtype changes
- `format_diff_for_display()` - Human-readable diff output
- **Status:** Ready for use in Phase 2

#### `transform_log.py`
- `TransformStep` - Dataclass for tracking individual transforms
- `TransformLog` - History management with snapshot storage
- `undo_last()` - Revert previous transformation
- `export_manifest_json()` - Export logs as JSON
- `export_recipe_py()` - Export as executable Python script
- **Status:** Ready for use in Phase 3

### 2. **Updated Core Files**

#### `core.py`
- Added `schema_snapshot()` function for DataFrame schema capture
- Used by AI Transform to provide context to LLM
- Follows existing code style and architecture

#### `app.py`
- Added `render_ai_transform_tab()` function
- New "AI Transform" tab in main interface
- 7-section UI layout:
  1. DataFrame Context Card (schema, types, null rates, samples)
  2. Model & Settings (vendor, model, temperature, warnings)
  3. Prompt Composer (text area, quick tips, column shortcuts)
  4. Code Generation & Preview (placeholder for Phase 1)
  5. Dry-Run Preview (placeholder for Phase 2)
  6. Apply & Undo (placeholder for Phase 3)
  7. Export (JSON & Python - placeholder for Phase 4)

### 3. **Configuration Files**

#### `requirements.txt`
Added:
- `langchain>=0.1.0`
- `openai>=1.0.0`
- `python-dotenv>=1.0.0`

#### `.env.template`
Template for configuration with placeholders for:
- AI_VENDOR, OPENAI_API_KEY, OPENAI_MODEL
- Sandbox timeouts and memory limits
- Dry-run sampling configuration

#### `.env`
Local development configuration file (should be git-ignored)

## Current State

✅ **What Works:**
- UI tab structure and layout visible when app runs
- Session state initialization for AI Transform
- Schema context display with real data
- Model selection dropdowns
- Placeholder code generation with sample output
- All supporting modules are structured and ready

⏳ **What's Next:**

### Phase 1: Real LLM Integration
1. Configure OpenAI API client in `llm_orchestrator.py`
2. Wire "Generate Code" button to real LLM calls
3. Add error handling and retry logic
4. Add prompt engineering refinements
5. Test with sample CSV

### Phase 2: Code Safety & Execution
1. Wire "Run on Sample" button to `sandbox_executor.py`
2. Integrate `code_sanitizer.py` validation before execution
3. Display diff using `format_diff_for_display()`
4. Handle execution errors gracefully
5. Add progress indicators for long-running operations

### Phase 3: Apply & Undo
1. Integrate `transform_log.py` for history tracking
2. Wire "Apply" button to persist transforms
3. Wire "Undo" button with rollback
4. Display transform history table
5. Store DataFrame snapshots for rollback

### Phase 4: Export
1. Wire JSON export using `transform_log.export_manifest_json()`
2. Wire Python export using `transform_log.export_recipe_py()`
3. Add download buttons with proper formatting
4. Add recipe documentation

## File Structure

```
streamlit/
├── app.py                      # Updated with AI Transform tab
├── core.py                     # Updated with schema_snapshot()
├── llm_orchestrator.py         # New - LLM provider integration
├── code_sanitizer.py           # New - Security validation
├── sandbox_executor.py         # New - Safe code execution
├── diff_tools.py               # New - Diff generation
├── transform_log.py            # New - Transform history
├── requirements.txt            # Updated with dependencies
├── .env.template               # New - Config template
├── .env                        # New - Local config (git-ignored)
├── PHASE_0_SUMMARY.md         # This file
├── co-emissions-per-capita.csv # Sample data
└── [existing files...]
```

## Testing Phase 0

To verify Phase 0 is complete:

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run the app
streamlit run app.py

# 3. Upload the sample CSV file
# co-emissions-per-capita.csv (already in root)

# 4. Navigate to "AI Transform" tab
# You should see:
# - DataFrame context with schema and sample data
# - Model settings section
# - Prompt composer
# - Placeholder code generation

# 5. Click "Generate Code" button
# You should see placeholder code appear
```

## Key Design Decisions

1. **LangChain for Provider Abstraction**
   - Enables easy switching between OpenAI, local models, etc.
   - Cleaner error handling and retry logic

2. **Signal-based Timeouts**
   - `signal.alarm()` for Unix-only timeout handling
   - Falls back gracefully on Windows

3. **AST-based Code Validation**
   - Whitelist approach: explicitly allow safe operations
   - Blocks all imports and dangerous patterns
   - Can be enhanced with more sophisticated analysis

4. **Restricted Globals in Executor**
   - Only `pd`, `np`, and safe builtins available
   - Prevents access to `__builtins__` or file operations
   - Can expand allowed builtins as needed

5. **In-Memory Transform Log**
   - No persistence to disk (v1 requirement)
   - DataFrame snapshots stored for undo
   - Can add persistence in v2

6. **Session State Organization**
   - `ai_code` - Latest generated code
   - `ai_preview_df` - Last dry-run result
   - Easy to add more state variables as needed

## Dependencies Added

```
langchain>=0.1.0         # LLM orchestration framework
openai>=1.0.0            # OpenAI SDK
python-dotenv>=1.0.0     # Environment variable loading
```

No breaking changes to existing dependencies.

## Next Steps

1. Get OpenAI API key ready
2. Review Phase 1 implementation plan
3. Test LLM integration with sample prompts
4. Fine-tune code generation prompts
5. Add more sophisticated security validations

---

**Created:** 2025-11-05
**Phase:** 0 / 4
**Status:** ✅ Ready for Phase 1
