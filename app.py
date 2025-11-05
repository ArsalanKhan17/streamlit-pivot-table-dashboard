import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import io
from datetime import datetime
from core import (
    read_csv_safe,
    sanitize_columns,
    get_unique_values,
    filter_dataframe,
    detect_numeric_columns,
    to_csv_bytes,
    build_pivot,
)

# Page configuration
st.set_page_config(page_title="Pivot Table Dashboard", layout="wide")
st.title("📊 Data Pivot Table Dashboard")

# ============================================================================
# INITIALIZE SESSION STATE
# ============================================================================
if "datasets" not in st.session_state:
    st.session_state.datasets = {}


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================


def sanitize_filename(filename):
    """Create a safe key from filename for use as session state key."""
    return filename.replace(" ", "_").replace(".", "_").lower()


def render_data_preview(df):
    """Display data preview and info."""
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Data Preview")
        st.dataframe(df.head(10), use_container_width=True)

    with col2:
        st.subheader("Data Info")
        st.write(f"**Shape:** {df.shape[0]} rows × {df.shape[1]} columns")
        st.write("**Column Names & Types:**")
        info_df = pd.DataFrame({
            "Column": df.columns,
            "Type": df.dtypes.astype(str)
        })
        st.dataframe(info_df, use_container_width=True)


def render_filter_section(df, file_key):
    """Render the filtering UI and return filtered dataframe."""
    with st.expander("Add Filters", expanded=False):
        # Step 1: Select which columns to filter on (optional)
        columns_to_filter = st.multiselect(
            "Select columns to filter (optional)",
            options=df.columns.tolist(),
            default=[],
            key=f"filter_cols_{file_key}"
        )

        filters = {}

        # Step 2: Create filter widgets only for selected columns
        for col in columns_to_filter:
            col_type = df[col].dtype

            # Numeric columns
            if pd.api.types.is_numeric_dtype(col_type):
                min_val = float(df[col].min())
                max_val = float(df[col].max())
                selected_range = st.slider(
                    f"Filter {col}",
                    min_value=min_val,
                    max_value=max_val,
                    value=(min_val, max_val),
                    key=f"slider_{file_key}_{col}"
                )
                # Convert range to categorical-style for our filter_dataframe function
                in_range_vals = df[(df[col] >= selected_range[0]) & (df[col] <= selected_range[1])][col].astype(str).unique().tolist()
                filters[col] = in_range_vals

            # Categorical/String columns
            else:
                unique_vals = get_unique_values(df, col, as_str=True)
                selected_vals = st.multiselect(
                    f"Filter {col}",
                    options=unique_vals,
                    default=unique_vals,
                    key=f"multiselect_{file_key}_{col}"
                )
                filters[col] = selected_vals

        # Apply filters
        try:
            filtered_df = filter_dataframe(df, filters)
        except (KeyError, ValueError, TypeError) as e:
            st.error(f"Error applying filters: {str(e)}")
            filtered_df = df.copy()

        st.info(f"Filtered data: {filtered_df.shape[0]} rows (from {df.shape[0]} total)")

    # Display filtered data preview
    with st.expander("Filtered Data Preview", expanded=False):
        st.dataframe(filtered_df.head(10), use_container_width=True)

    return filtered_df


def render_pivot_section(filtered_df, file_key):
    """Render the pivot table configuration and return pivot result."""
    st.header("3️⃣ Configure Pivot Table")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.subheader("📁 Group By (Rows)")
        group_by_cols = st.multiselect(
            "Select columns to group by",
            options=filtered_df.columns.tolist(),
            key=f"group_by_{file_key}"
        )

    with col2:
        st.subheader("📊 Aggregate Column")
        agg_col = st.selectbox(
            "Select column to aggregate",
            options=filtered_df.columns.tolist(),
            key=f"agg_col_{file_key}"
        )

    numeric_cols = detect_numeric_columns(filtered_df)
    if not numeric_cols:
        st.warning("⚠️ No numeric columns found. Aggregation limited to 'count'.")

    with col3:
        st.subheader("⚙️ Aggregation Functions")
        available_aggs = ["sum", "count", "mean", "min", "max", "median", "std", "var"]
        agg_functions = st.multiselect(
            "Select aggregation functions",
            options=available_aggs,
            default=["sum"],
            key=f"agg_funcs_{file_key}"
        )

    return group_by_cols, agg_col, agg_functions


def render_pivot_results(filtered_df, group_by_cols, agg_col, agg_functions, file_key):
    """Render pivot table results and visualizations."""
    if not group_by_cols or not agg_col or not agg_functions:
        st.info("👈 Please configure the pivot table settings to generate results")
        return None

    st.header("4️⃣ Pivot Table Results")

    try:
        # Create pivot table using core.build_pivot
        pivot_df = build_pivot(filtered_df, group_by_cols, agg_col, agg_functions)

        # Display pivot table
        st.subheader("Pivoted Data")
        st.dataframe(pivot_df, use_container_width=True)

        # Display summary statistics
        st.subheader("Summary Statistics")
        summary_col1, summary_col2, summary_col3 = st.columns(3)
        with summary_col1:
            st.metric("Total Rows", len(pivot_df))
        with summary_col2:
            st.metric("Total Groups", len(pivot_df))
        with summary_col3:
            if "sum" in agg_functions:
                total = filtered_df[agg_col].sum()
                st.metric("Total Value", f"{total:.2f}" if isinstance(total, (int, float)) else total)

        # Check for wide pivots
        if len(pivot_df.columns) > 20:
            st.warning(f"⚠️ Wide pivot detected ({len(pivot_df.columns)} columns). Charts may be difficult to read.")

        # ================================================================
        # SECTION 5: VISUALIZATION
        # ================================================================
        st.header("5️⃣ Visualizations")

        # Only allow visualizations if we have at most 2 group_by columns
        if len(group_by_cols) <= 2:
            chart_type = st.selectbox(
                "Select chart type",
                options=["Bar Chart", "Line Chart", "Area Chart", "Pie Chart"],
                key=f"chart_type_{file_key}"
            )

            fig = None

            # Prepare data for visualization
            if len(group_by_cols) == 1:
                x_col = group_by_cols[0]
                y_col = agg_functions[0]

                # Create chart based on selection
                if chart_type == "Bar Chart":
                    fig = px.bar(
                        pivot_df,
                        x=x_col,
                        y=y_col,
                        title=f"{y_col.capitalize()} by {x_col}",
                        labels={x_col: x_col, y_col: f"{y_col.capitalize()}({agg_col})"}
                    )
                elif chart_type == "Line Chart":
                    fig = px.line(
                        pivot_df,
                        x=x_col,
                        y=y_col,
                        title=f"{y_col.capitalize()} by {x_col}",
                        labels={x_col: x_col, y_col: f"{y_col.capitalize()}({agg_col})"},
                        markers=True
                    )
                elif chart_type == "Area Chart":
                    fig = px.area(
                        pivot_df,
                        x=x_col,
                        y=y_col,
                        title=f"{y_col.capitalize()} by {x_col}",
                        labels={x_col: x_col, y_col: f"{y_col.capitalize()}({agg_col})"}
                    )
                else:  # Pie Chart
                    fig = px.pie(
                        pivot_df,
                        names=x_col,
                        values=y_col,
                        title=f"{y_col.capitalize()} Distribution by {x_col}"
                    )

            elif len(group_by_cols) == 2:
                x_col = group_by_cols[0]
                color_col = group_by_cols[1]
                y_col = agg_functions[0]

                # For 2 group by columns, create grouped chart
                if chart_type == "Bar Chart":
                    fig = px.bar(
                        pivot_df,
                        x=x_col,
                        y=y_col,
                        color=color_col,
                        title=f"{y_col.capitalize()} by {x_col} and {color_col}",
                        barmode="group"
                    )
                elif chart_type == "Line Chart":
                    fig = px.line(
                        pivot_df,
                        x=x_col,
                        y=y_col,
                        color=color_col,
                        title=f"{y_col.capitalize()} by {x_col} and {color_col}",
                        markers=True
                    )
                elif chart_type == "Area Chart":
                    fig = px.area(
                        pivot_df,
                        x=x_col,
                        y=y_col,
                        color=color_col,
                        title=f"{y_col.capitalize()} by {x_col} and {color_col}"
                    )
                else:  # Pie Chart - only use first dimension
                    fig = px.pie(
                        pivot_df,
                        names=x_col,
                        values=y_col,
                        title=f"{y_col.capitalize()} Distribution"
                    )

            if fig:
                st.plotly_chart(fig, use_container_width=True)

                # ============================================================
                # SECTION 6: DOWNLOAD OPTIONS
                # ============================================================
                st.header("6️⃣ Export Data & Charts")

                col1, col2, col3 = st.columns(3)

                with col1:
                    st.subheader("📥 Download Data")
                    csv_data = to_csv_bytes(pivot_df)
                    st.download_button(
                        label="Download Pivot Table (CSV)",
                        data=csv_data,
                        file_name=f"pivot_table_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv"
                    )

                with col2:
                    st.subheader("📊 Download Chart")
                    html_chart = fig.to_html(include_plotlyjs='cdn')
                    st.download_button(
                        label="Download Chart (HTML)",
                        data=html_chart,
                        file_name=f"chart_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html",
                        mime="text/html"
                    )

                with col3:
                    st.subheader("🖼️ Download as PNG")
                    try:
                        img_bytes = fig.to_image(format="png")
                        st.download_button(
                            label="Download Chart (PNG)",
                            data=img_bytes,
                            file_name=f"chart_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png",
                            mime="image/png"
                        )
                    except:
                        st.info("⚠️ PNG export requires kaleido. Install with: pip install kaleido")

        else:
            st.warning("📊 Visualization limited to maximum 2 grouping columns. Current: " + str(len(group_by_cols)))

        return pivot_df

    except Exception as e:
        st.error(f"Error creating pivot table: {str(e)}")
        return None


# ============================================================================
# MAIN APP
# ============================================================================

# SIDEBAR: File upload
st.sidebar.header("📁 File Management")
uploaded_files = st.sidebar.file_uploader(
    "Upload CSV files",
    type=["csv"],
    accept_multiple_files=True,
    help="Upload one or more CSV files to analyze"
)

# Load files into datasets
if uploaded_files:
    for uploaded_file in uploaded_files:
        file_key = sanitize_filename(uploaded_file.name)

        if file_key not in st.session_state.datasets:
            try:
                df = read_csv_safe(uploaded_file)
                df = sanitize_columns(df)
                st.session_state.datasets[file_key] = {
                    "name": uploaded_file.name,
                    "df": df,
                    "filtered_df": df.copy()
                }
            except ValueError as e:
                st.sidebar.error(f"Error loading {uploaded_file.name}: {str(e)}")

    # Remove datasets that are no longer in the upload list
    current_files = {sanitize_filename(f.name) for f in uploaded_files}
    stale_keys = [k for k in st.session_state.datasets if k not in current_files]
    for k in stale_keys:
        del st.session_state.datasets[k]

    # Reset button
    if st.sidebar.button("🔄 Reset All Data"):
        st.session_state.datasets = {}
        st.rerun()

    # Display uploaded files info
    st.sidebar.success(f"✅ {len(st.session_state.datasets)} file(s) loaded")

    # ============================================================================
    # MAIN CONTENT: TABS FOR EACH FILE
    # ============================================================================

    if st.session_state.datasets:
        tab_names = [st.session_state.datasets[k]["name"] for k in st.session_state.datasets]
        tabs = st.tabs(tab_names)

        for tab, (file_key, dataset) in zip(tabs, st.session_state.datasets.items()):
            with tab:
                df = dataset["df"]

                st.header(f"1️⃣ Data Preview: {dataset['name']}")
                render_data_preview(df)

                st.header("2️⃣ Filter Your Data")
                filtered_df = render_filter_section(df, file_key)

                group_by_cols, agg_col, agg_functions = render_pivot_section(filtered_df, file_key)

                render_pivot_results(filtered_df, group_by_cols, agg_col, agg_functions, file_key)

                # Additional download for filtered data
                st.header("📥 Export Filtered Data")
                col1, col2 = st.columns(2)
                with col1:
                    filtered_csv = to_csv_bytes(filtered_df)
                    st.download_button(
                        label="Download Filtered Data (CSV)",
                        data=filtered_csv,
                        file_name=f"filtered_{dataset['name']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv",
                        key=f"filtered_download_{file_key}"
                    )

else:
    st.info("👆 Upload one or more CSV files to get started!")
