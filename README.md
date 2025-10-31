# 📊 Data Pivot Table Dashboard

An interactive Streamlit dashboard for creating Excel-like pivot tables with advanced filtering, aggregation, and visualization capabilities.

## Features

✨ **Key Features:**

- **CSV File Upload**: Upload your data files at runtime
- **Data Preview**: View your raw data and column information
- **Advanced Filtering**: Filter data before pivoting using range sliders and categorical multiselects
- **Pivot Table Configuration**:
  - Multiple grouping columns
  - Flexible column selection for aggregation
  - Support for 8 aggregation functions
- **8 Aggregation Functions**: sum, count, mean, min, max, median, standard deviation, variance
- **Interactive Visualizations**: Bar, line, area, and pie charts powered by Plotly
- **Export Capabilities**:
  - Download pivoted data as CSV
  - Download charts as HTML
  - Download charts as PNG (requires kaleido)

## Installation & Setup

### 1. Clone or Download the Project

Navigate to your project directory.

### 2. Create Virtual Environment

```bash
python3 -m venv venv
```

### 3. Activate Virtual Environment

**macOS/Linux:**
```bash
source venv/bin/activate
```

**Windows:**
```bash
venv\Scripts\activate
```

### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

### Optional: Install PNG Export Support

For PNG chart downloads, install kaleido:

```bash
pip install kaleido
```

## Running the Dashboard

1. Make sure your virtual environment is activated
2. Run the Streamlit app:

```bash
streamlit run app.py
```

3. The dashboard will open in your default browser at `http://localhost:8501`

## How to Use

### Step 1: Upload Data
- Click "Choose a CSV file" to upload your data
- The dashboard will display a preview and data information

### Step 2: Filter Data (Optional)
- Expand the "Add Filters" section
- Use range sliders for numeric columns
- Use multiselect dropdowns for categorical columns
- Filters are applied automatically

### Step 3: Configure Pivot Table
- **Group By (Rows)**: Select one or more columns to group your data
- **Aggregate Column**: Choose which column to aggregate
- **Aggregation Functions**: Select one or more functions (sum, count, mean, etc.)

### Step 4: View Results
- The pivot table appears automatically below the configuration
- Summary statistics are displayed
- Data is shown in an interactive table

### Step 5: Visualize Data
- Select a chart type (Bar, Line, Area, or Pie)
- Charts are generated automatically based on your pivot table
- *Note: Visualizations work best with 1-2 grouping columns*

### Step 6: Export
- **Download Pivot Table (CSV)**: Export your aggregated data
- **Download Chart (HTML)**: Export interactive chart as HTML
- **Download Chart (PNG)**: Export chart as PNG image (requires kaleido)

## Example Use Cases

### Sales Analysis
- Group by: Product, Region
- Aggregate: Revenue
- Functions: sum, mean
- Create: Bar chart of total revenue by product

### Time Series Analysis
- Group by: Date
- Aggregate: Metrics
- Functions: sum, mean, min, max
- Create: Line chart showing trends over time

### Customer Analytics
- Group by: Customer Segment
- Aggregate: Order Amount
- Functions: count, sum, mean
- Create: Pie chart showing distribution

## Data Format Requirements

Your CSV file should have:
- Headers in the first row
- Consistent data types in each column
- No merged cells

Example:
```csv
Date,Product,Region,Revenue,Quantity
2024-01-01,Widget A,North,1000,50
2024-01-01,Widget B,South,1500,75
2024-01-02,Widget A,North,1100,55
```

## Troubleshooting

### "ModuleNotFoundError" when running streamlit
- Make sure your virtual environment is activated
- Reinstall dependencies: `pip install -r requirements.txt`

### Filters not appearing
- Ensure your CSV has mixed data types (both numeric and categorical columns)
- Numeric columns show range sliders, categorical columns show multiselect

### PNG export not working
- Install kaleido: `pip install kaleido`
- If issues persist, use HTML export and convert in your browser

### Performance issues with large files
- Streamlit works best with <100K rows
- Pre-filter your data before uploading if possible
- Consider aggregating data before upload

## Technical Stack

- **Streamlit**: UI framework and web app hosting
- **Pandas**: Data manipulation and pivot table creation
- **Plotly**: Interactive data visualizations
- **Python 3.10+**: Core programming language

## Notes

- Visualizations are optimized for 1-2 grouping columns
- For 3+ grouping columns, only the pivot table is displayed
- Session state maintains your configuration while interacting with the dashboard
- All data processing happens client-side in the virtual environment

## License

Feel free to use and modify this dashboard for your needs.

## Support

For issues or feature requests, check the Streamlit documentation at https://docs.streamlit.io
