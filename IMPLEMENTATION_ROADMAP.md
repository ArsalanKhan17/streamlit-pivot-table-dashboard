# AI Transform Implementation Roadmap

**Project:** Streamlit Pivot Dashboard - AI Transform Feature
**Status:** Phase 0 Complete, Ready for Phase 1
**Date Started:** 2025-11-05

---

## Overview

This document outlines the complete phased implementation of the AI Transform feature. The phased approach allows for:
- ✅ Easy rollback if breaking changes occur
- ✅ Incremental testing and validation
- ✅ Clear dependency management between phases
- ✅ Early error detection

---

## Phase Dependency Graph

```
Phase 0 (Complete)
    ↓
Phase 1 (Next)
    ↓
Phase 2
    ↓
Phase 3
    ↓
Phase 4
```

Each phase builds on the previous, but can be tested independently.

---

## Phase 0: UI Skeleton & Infrastructure ✅ COMPLETE

**Goal:** Build the UI layout and supporting infrastructure without LLM calls

**Duration:** ~2-3 hours

### Deliverables ✅

#### New Modules
| Module | Purpose | Status |
|--------|---------|--------|
| `llm_orchestrator.py` | LLM provider abstraction (not yet wired) | ✅ Ready |
| `code_sanitizer.py` | AST-based code validation | ✅ Ready |
| `sandbox_executor.py` | Safe code execution environment | ✅ Ready |
| `diff_tools.py` | Before/after DataFrame comparison | ✅ Ready |
| `transform_log.py` | Transform history & undo tracking | ✅ Ready |

#### Updated Files
| File | Changes | Status |
|------|---------|--------|
| `core.py` | Added `schema_snapshot()` | ✅ Complete |
| `app.py` | Added AI Transform tab & UI sections | ✅ Complete |
| `requirements.txt` | Added langchain, openai, python-dotenv | ✅ Complete |

#### Configuration Files
| File | Purpose | Status |
|------|---------|--------|
| `.env.template` | Config template | ✅ Complete |
| `.env` | Local dev config | ✅ Complete |
| `PHASE_0_SUMMARY.md` | Phase 0 documentation | ✅ Complete |

### UI Sections Implemented

```
AI Transform Tab
├── 1. DataFrame Context Card
│   ├── Schema information (rows, columns)
│   ├── Column types table
│   ├── Null rate analysis
│   └── Sample rows preview
├── 2. Model & Settings
│   ├── LLM vendor selector
│   ├── Model selector
│   ├── Temperature slider
│   └── Privacy warning banner
├── 3. Prompt Composer
│   ├── Text area for natural language prompt
│   ├── Quick tips panel
│   └── Column name shortcut buttons
├── 4. Generated Code
│   ├── Generate, Explain, Reset buttons
│   └── Code preview (syntax highlighted)
├── 5. Dry-Run Preview
│   ├── "Run on Sample (2%)" button
│   └── Result preview with diff summary
├── 6. Apply & Undo
│   ├── Apply to Working DataFrame button
│   ├── Undo Last button
│   └── Transform Log table
└── 7. Export
    ├── Export as JSON button
    └── Export as Python button
```

### Testing Phase 0

See `TESTING_PHASE_0.md` for detailed instructions.

**Quick Test:**
```bash
streamlit run app.py
# Upload co-emissions-per-capita.csv
# Click "AI Transform" tab
# Verify all 7 sections display correctly
```

### Known Limitations (By Design)

- "Generate Code" shows placeholder code (will be wired in Phase 1)
- Dry-run preview is static sample (will be implemented in Phase 2)
- "Apply" and "Undo" buttons don't function (Phase 3)
- Export buttons show info message (Phase 4)

---

## Phase 1: LangChain Integration & Code Generation 🚀 NEXT

**Goal:** Wire the LLM orchestrator to generate real code from prompts

**Estimated Duration:** 4-6 hours

**Depends On:** Phase 0 ✅

### Tasks

1. **Load Environment Configuration**
   - [ ] Load `.env` file with `python-dotenv`
   - [ ] Validate `OPENAI_API_KEY` is set
   - [ ] Handle missing key with user-friendly error

2. **Implement LLM Orchestrator Wiring**
   - [ ] Initialize `LLMOrchestrator` with vendor/model/temperature
   - [ ] Wire "Generate Code" button to `orchestrator.generate_code()`
   - [ ] Pass DataFrame schema as context
   - [ ] Pass user prompt

3. **Add Code Generation Logic to app.py**
   - [ ] Create `st.session_state.ai_vendor`, `ai_model`, `ai_temperature`
   - [ ] Get schema from `schema_snapshot(df)`
   - [ ] Call orchestrator on "Generate Code" click
   - [ ] Display generated code with syntax highlighting
   - [ ] Show any errors from LLM calls

4. **Error Handling**
   - [ ] Handle API key errors
   - [ ] Handle API rate limits
   - [ ] Handle invalid code structure
   - [ ] Show user-friendly error messages

5. **Testing**
   - [ ] Test with sample prompts
   - [ ] Verify code structure validation
   - [ ] Test error cases

### Code Changes

**In `app.py` render_ai_transform_tab():**

```python
# Current (placeholder):
if st.button("✨ Generate Code", key="btn_generate"):
    st.info("🚀 [PHASE 1] LLM integration coming soon...")
    st.session_state.ai_code = """def transform(df):
    result = df[df['Annual CO₂ emissions (per capita)'] > 1.0].copy()
    result['high_emitter'] = True
    return result"""

# Phase 1 will change to:
if st.button("✨ Generate Code", key="btn_generate"):
    with st.spinner("🤖 Generating code..."):
        try:
            schema = schema_snapshot(df)
            orchestrator = LLMOrchestrator(
                vendor=vendor,
                model=model,
                temperature=temperature
            )
            code = orchestrator.generate_code(prompt, schema)
            st.session_state.ai_code = code
            st.success("✅ Code generated successfully")
        except Exception as e:
            st.error(f"❌ Generation failed: {str(e)}")
```

### Exit Criteria

- ✅ User can write a prompt and generate real code
- ✅ Generated code has correct `def transform(df):` structure
- ✅ Code validation works
- ✅ Errors are handled gracefully
- ✅ Can generate 5+ different types of transforms

### What Still Won't Work

- Dry-run will still show placeholder sample (Phase 2)
- Apply/Undo buttons won't work (Phase 3)
- Export won't work (Phase 4)

---

## Phase 2: Code Safety & Dry-Run Execution 🧪

**Goal:** Validate code safety and execute on sample data

**Estimated Duration:** 4-5 hours

**Depends On:** Phase 1 ✅

### Tasks

1. **Code Sanitization**
   - [ ] Wire `code_sanitizer.validate()` after code generation
   - [ ] Show violations to user if any found
   - [ ] Display sanitizer warnings with explanations
   - [ ] Block unsafe code from proceeding

2. **Dry-Run Execution**
   - [ ] Wire "Run on Sample (2%)" button
   - [ ] Create sample (min 10 rows, max 10k)
   - [ ] Call `sandbox_executor.dry_run()`
   - [ ] Display result DataFrame
   - [ ] Show execution time

3. **Diff Display**
   - [ ] Call `compute_diff()` on sample results
   - [ ] Format using `format_diff_for_display()`
   - [ ] Show:
     - Row count changes
     - Columns added/removed/renamed
     - Type changes
     - Sample values in new columns

4. **Error Handling**
   - [ ] Handle timeout errors (10 second limit)
   - [ ] Handle memory/size warnings
   - [ ] Handle execution exceptions
   - [ ] Show user-friendly error messages with context

5. **Testing**
   - [ ] Test various transform types
   - [ ] Verify sample size handling
   - [ ] Test timeout behavior
   - [ ] Test with problematic code

### Code Changes

**In `app.py` render_ai_transform_tab():**

```python
# After code generation and before dry-run:
if st.session_state.ai_code:
    # NEW: Validate code safety
    violations = validate_code(st.session_state.ai_code)
    if violations:
        st.error("🚨 Code violates security constraints:")
        for v in violations:
            st.write(f"• {v}")
    else:
        st.success("✅ Code passed security validation")

# In dry-run section:
if st.button("▶️  Run on Sample (2%)", key="btn_dryrun"):
    try:
        with st.spinner("Running on sample..."):
            sample_df, diff = sandbox_executor.dry_run(
                st.session_state.ai_code,
                df,
                sample_frac=0.02,
                max_rows=10000
            )
        st.session_state.ai_preview_df = sample_df
        st.success("✅ Dry-run completed")
    except TimeoutException:
        st.error("⏱️  Code execution timed out (10 seconds)")
    except Exception as e:
        st.error(f"❌ Execution failed: {str(e)}")

# Display diff:
if st.session_state.ai_preview_df is not None:
    st.dataframe(st.session_state.ai_preview_df)
    diff_text = format_diff_for_display(diff)
    st.markdown(diff_text)
```

### Exit Criteria

- ✅ User can generate code, see violations, and dry-run
- ✅ Diff correctly shows row/column/type changes
- ✅ Timeouts are handled (code stopped after 10 seconds)
- ✅ Errors shown with helpful context
- ✅ Can preview 5+ different transforms

### What Still Won't Work

- Apply/Undo (Phase 3)
- Export (Phase 4)

---

## Phase 3: Apply & Undo with History ↩️

**Goal:** Apply transforms to working DataFrame with full rollback support

**Estimated Duration:** 3-4 hours

**Depends On:** Phase 2 ✅

### Tasks

1. **Apply Transformation**
   - [ ] Wire "Apply to Working DataFrame" button
   - [ ] Run full transform (not just sample)
   - [ ] Call `sandbox_executor.apply()`
   - [ ] Update `st.session_state.df` with result
   - [ ] Log to `TransformLog`

2. **Transform Logging**
   - [ ] Create `TransformLog` in session state
   - [ ] On each apply, call `transform_log.append()`
   - [ ] Store schema before/after
   - [ ] Store diff
   - [ ] Store full code for reproducibility

3. **Undo Functionality**
   - [ ] Wire "Undo Last" button
   - [ ] Call `transform_log.undo_last()`
   - [ ] Restore previous DataFrame state
   - [ ] Show success message

4. **Transform History Display**
   - [ ] Call `transform_log.to_dataframe()`
   - [ ] Display table with:
     - Timestamp
     - Prompt (first 50 chars)
     - Code hash
     - Row/column deltas
   - [ ] Make read-only table

5. **Testing**
   - [ ] Apply a transform successfully
   - [ ] Undo and verify data restored
   - [ ] Apply multiple transforms in sequence
   - [ ] Verify history table updates

### Code Changes

**In `app.py` render_ai_transform_tab():**

```python
# Initialize transform log if needed
if "transform_log" not in st.session_state:
    st.session_state.transform_log = TransformLog()

# Apply button:
if st.button("✅ Apply to Working DataFrame", key="btn_apply"):
    try:
        with st.spinner("Applying transformation..."):
            df_before = df.copy()
            result_df, diff = sandbox_executor.apply(
                st.session_state.ai_code,
                df
            )

        # Update working DataFrame
        st.session_state.datasets[first_dataset_key]["df"] = result_df

        # Log the transform
        schema_before = schema_snapshot(df_before)
        schema_after = schema_snapshot(result_df)
        st.session_state.transform_log.append(
            prompt=prompt,
            code=st.session_state.ai_code,
            diff=diff,
            schema_before=schema_before,
            schema_after=schema_after,
            df_after=result_df
        )

        st.success("✅ Applied! Use Undo Last to revert.")
        st.rerun()
    except Exception as e:
        st.error(f"❌ Failed to apply: {str(e)}")

# Undo button:
if st.button("⏮️  Undo Last", key="btn_undo"):
    prev_step_id = st.session_state.transform_log.undo_last()
    if prev_step_id:
        prev_df = st.session_state.transform_log.get_df_for_step(prev_step_id)
        st.session_state.datasets[first_dataset_key]["df"] = prev_df
        st.success("✅ Undo successful")
        st.rerun()
    else:
        st.warning("No more transforms to undo")

# Show transform history:
if len(st.session_state.transform_log) > 0:
    history_df = st.session_state.transform_log.to_dataframe()
    st.dataframe(history_df, use_container_width=True)
```

### Exit Criteria

- ✅ Apply successfully updates working DataFrame
- ✅ Undo restores previous state
- ✅ Multiple applies + undos work correctly
- ✅ Transform history displays correctly
- ✅ Other tabs still work with updated data

### What Still Won't Work

- Export (Phase 4)

---

## Phase 4: Export Functionality 💾

**Goal:** Export transform history and reproducible Python recipes

**Estimated Duration:** 2-3 hours

**Depends On:** Phase 3 ✅

### Tasks

1. **JSON Export**
   - [ ] Wire "Export as JSON" button
   - [ ] Generate manifest using `transform_log.export_manifest_json()`
   - [ ] Add download button with filename
   - [ ] Include metadata (date, version, transform count)

2. **Python Recipe Export**
   - [ ] Wire "Export as Python" button
   - [ ] Generate script using `transform_log.export_recipe_py()`
   - [ ] Include:
     - Shebang and docstring
     - All transforms as numbered functions
     - Chained `apply_all_transforms()` function
     - Example usage with CSV loading
   - [ ] Add download button with filename

3. **Download Buttons**
   - [ ] Add proper MIME types
   - [ ] Add timestamps to filenames
   - [ ] Test in browser

4. **Testing**
   - [ ] Export after multiple transforms
   - [ ] Verify JSON is valid JSON
   - [ ] Verify Python script is valid Python
   - [ ] Test downloaded files can be run standalone

### Code Changes

**In `app.py` render_ai_transform_tab():**

```python
# Export section:
col1, col2 = st.columns(2)

with col1:
    if st.button("📄 Export as JSON"):
        if len(st.session_state.transform_log) == 0:
            st.warning("No transforms to export")
        else:
            json_str = st.session_state.transform_log.export_manifest_json()
            st.download_button(
                label="📥 Download JSON",
                data=json_str,
                file_name=f"transforms_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )

with col2:
    if st.button("🐍 Export as Python"):
        if len(st.session_state.transform_log) == 0:
            st.warning("No transforms to export")
        else:
            py_str = st.session_state.transform_log.export_recipe_py()
            st.download_button(
                label="📥 Download Python",
                data=py_str,
                file_name=f"recipe_{datetime.now().strftime('%Y%m%d_%H%M%S')}.py",
                mime="text/plain"
            )
```

### Exit Criteria

- ✅ JSON export contains all transform metadata
- ✅ Python export is valid, runnable code
- ✅ Downloads work in browser
- ✅ Exported code can process new CSV files
- ✅ Exported JSON can be loaded for audit/compliance

---

## Implementation Checklist

### Phase 0 ✅ COMPLETE
- [x] Create llm_orchestrator.py
- [x] Create code_sanitizer.py
- [x] Create sandbox_executor.py
- [x] Create diff_tools.py
- [x] Create transform_log.py
- [x] Add schema_snapshot() to core.py
- [x] Create AI Transform tab in app.py
- [x] Add dependencies to requirements.txt
- [x] Create .env and .env.template
- [x] Create PHASE_0_SUMMARY.md
- [x] Create IMPLEMENTATION_ROADMAP.md (this file)

### Phase 1 🚀 NEXT
- [ ] Load and validate OPENAI_API_KEY
- [ ] Initialize LLMOrchestrator
- [ ] Wire "Generate Code" button
- [ ] Test code generation
- [ ] Test error handling

### Phase 2 🧪
- [ ] Wire code_sanitizer validation
- [ ] Wire sandbox_executor dry_run
- [ ] Display diff summary
- [ ] Handle timeouts
- [ ] Test various transforms

### Phase 3 ↩️
- [ ] Initialize TransformLog in session_state
- [ ] Wire "Apply" button
- [ ] Wire "Undo" button
- [ ] Display history table
- [ ] Test multi-transform workflow

### Phase 4 💾
- [ ] Wire JSON export
- [ ] Wire Python export
- [ ] Add download buttons
- [ ] Test exported files

---

## Risk Mitigation

### Phase 1 Risks
- **Risk:** OpenAI API changes or downtime
- **Mitigation:** Abstract provider interface, easy to swap implementations

- **Risk:** Code generation produces unexpected code
- **Mitigation:** Strict contract validation in llm_orchestrator.py

### Phase 2 Risks
- **Risk:** Timeout not working on all platforms (Windows)
- **Mitigation:** Graceful fallback, raise clear error message

- **Risk:** Code execution becomes resource-intensive
- **Mitigation:** Memory guards, size limit checks in executor

### Phase 3 Risks
- **Risk:** Running out of memory with large snapshots
- **Mitigation:** Only store DataFrame snapshots for undo (configurable), compression in v2

### Phase 4 Risks
- **Risk:** Exported code doesn't work on different environments
- **Mitigation:** Include dependencies, use only standard pd/np operations

---

## Rollback Strategy

If any phase causes breaking changes:

1. **Revert file changes:**
   ```bash
   git checkout app.py core.py requirements.txt
   ```

2. **Delete new modules:**
   ```bash
   rm llm_orchestrator.py code_sanitizer.py sandbox_executor.py diff_tools.py transform_log.py
   ```

3. **Re-test existing features:**
   - Upload/filter/pivot still works
   - No impact to other tabs

4. **Start over on phase** or pivot approach

---

## Success Metrics

- ✅ Phase 0: UI renders without errors, all 7 sections visible
- ✅ Phase 1: Generate button produces valid code 5+ times
- ✅ Phase 2: Dry-run shows correct diff for 5+ transforms
- ✅ Phase 3: Apply + Undo works for 3+ sequential transforms
- ✅ Phase 4: Exported code runs standalone on new CSV
- ✅ Final: Feature works end-to-end for typical user workflows

---

## Timeline Estimate

| Phase | Estimate | Status |
|-------|----------|--------|
| Phase 0 | 2-3 hours | ✅ Complete |
| Phase 1 | 4-6 hours | 🚀 Next |
| Phase 2 | 4-5 hours | 🧪 To Do |
| Phase 3 | 3-4 hours | ↩️ To Do |
| Phase 4 | 2-3 hours | 💾 To Do |
| **Total** | **15-21 hours** | |

---

## Questions & Decisions

**Q: Why phased approach?**
A: Allows testing each component independently and easy rollback if breaking changes occur.

**Q: Why LangChain instead of direct OpenAI?**
A: Enables easy provider switching, better error handling, future-proof for local models.

**Q: Why AST-based sanitization?**
A: Whitelist approach is more secure than blacklist, catches patterns not just names.

**Q: Why restricted globals?**
A: Prevents access to dangerous modules, file operations, and system calls.

**Q: Why in-memory transform log for v1?**
A: Simpler implementation, v2 can add persistence/compression if needed.

---

**Document Version:** 1.0
**Last Updated:** 2025-11-05
**Next Review:** After Phase 1 completion
