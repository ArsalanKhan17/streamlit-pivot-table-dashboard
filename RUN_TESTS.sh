#!/bin/bash
# Run Unit Tests for Pivot Table Dashboard
# This script activates the venv and runs all tests

# Navigate to project directory
cd /Users/arsalankhan/Documents/streamlit

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Verify activation
echo "✓ Virtual environment activated"
echo ""

# Display Python info
echo "📊 Python Information:"
echo "  Python: $(python --version)"
echo "  Location: $(which python)"
echo ""

# Display installed packages
echo "📦 Key Dependencies:"
python -c "import pandas as pd; import streamlit; import plotly; print(f'  pandas: {pd.__version__}'); print(f'  streamlit: {streamlit.__version__}'); print(f'  plotly: {plotly.__version__}')"
echo ""

# Run tests
echo "🧪 Running Unit Tests..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

python -m unittest test_core -v

# Capture exit code
EXIT_CODE=$?

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Check result
if [ $EXIT_CODE -eq 0 ]; then
    echo ""
    echo "✅ All tests passed!"
    echo ""
    echo "Next steps:"
    echo "  - Review changes with: git diff"
    echo "  - Run the app with: streamlit run app.py"
    echo "  - Deactivate venv with: deactivate"
else
    echo ""
    echo "❌ Some tests failed (exit code: $EXIT_CODE)"
    echo ""
    echo "Next steps:"
    echo "  - Review test output above"
    echo "  - Check TESTING_GUIDE.md for troubleshooting"
    echo "  - Deactivate venv with: deactivate"
fi

echo ""
exit $EXIT_CODE
