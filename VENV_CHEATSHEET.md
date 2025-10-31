# Virtual Environment Cheatsheet

## Quick Commands

### Activate venv
```bash
source venv/bin/activate
```
**After running this, your terminal prompt should show `(venv)` at the beginning.**

### Deactivate venv
```bash
deactivate
```
**Run this when done to return to system Python.**

### Verify venv is Active
```bash
which python
# Should show: /Users/arsalankhan/Documents/streamlit/venv/bin/python
```

### Check Installed Packages
```bash
pip list
# Should show: pandas, streamlit, plotly, and their dependencies
```

### Install/Update Dependencies
```bash
pip install -r requirements.txt
```

---

## Complete Workflow

```bash
# 1. Open terminal and navigate to project
cd /Users/arsalankhan/Documents/streamlit

# 2. Activate virtual environment
source venv/bin/activate

# 3. You should see (venv) in your prompt now
# (venv) arsalankhan@MacBook streamlit %

# 4. Run tests
python -m unittest test_core -v

# 5. Expected: All tests pass with (venv) Python
# OK
# Ran 74 tests in 0.XXs

# 6. When done, deactivate
deactivate
```

---

## Why This Matters

| Aspect | Without venv | With venv |
|--------|-------------|----------|
| Python interpreter | System Python | Project-specific |
| Dependencies | System-wide | Project-isolated |
| Reproducibility | May vary | Consistent |
| Version conflicts | Possible | Prevented |
| CI/CD compatibility | Different | Identical |
| Testing reliability | Flaky | Reliable |

---

## Platform-Specific

### macOS/Linux
```bash
source venv/bin/activate
deactivate
```

### Windows (PowerShell)
```powershell
venv\Scripts\Activate.ps1
deactivate
```

### Windows (Command Prompt)
```cmd
venv\Scripts\activate.bat
deactivate
```

---

## Troubleshooting

### Problem: `command not found: python`
**Cause**: venv not activated
```bash
source venv/bin/activate
```

### Problem: `ModuleNotFoundError: No module named 'pandas'`
**Cause**: Using system Python instead of venv
```bash
# Check which Python
which python

# If it's NOT the venv path, activate venv
source venv/bin/activate
```

### Problem: `python: command not found`
**Cause**: venv not properly activated
```bash
# Verify venv exists
ls venv/bin/python

# Activate it
source venv/bin/activate

# Verify activation
which python
```

### Problem: Packages outdated
**Solution**: Reinstall from requirements.txt
```bash
source venv/bin/activate
pip install -r requirements.txt --upgrade
```

---

## Quick Test Command

Once venv is active, run this command to verify everything works:

```bash
python -m unittest test_core.TestDataLoading.test_load_valid_csv -v
```

You should see:
```
test_load_valid_csv (test_core.TestDataLoading) ... ok

Ran 1 test in 0.XXs

OK
```

If you see errors about imports, you likely need to activate the venv.

---

## Full Testing Session Example

```bash
# Navigate to project
cd /Users/arsalankhan/Documents/streamlit

# Activate venv
source venv/bin/activate

# Verify packages
pip list | grep -E "pandas|streamlit|plotly"
# pandas     2.0.X
# streamlit  1.28.X
# plotly     5.0.X

# Run all tests
python -m unittest test_core -v

# Run specific test class
python -m unittest test_core.TestHighPriorityScenarios -v

# Run app
streamlit run app.py

# When done
deactivate
```

---

**Remember**: Always activate the venv before running tests or the app! 🐍
