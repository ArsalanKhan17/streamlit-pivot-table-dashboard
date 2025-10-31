import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import io
from datetime import datetime
from core import load_csv, apply_filters, build_pivot

# Page configuration
st.set_page_config(page_title="Pivot Table Dashboard", layout="wide")
st.title("📊 Data Pivot Table Dashboard")

# Initialize session state
if 'df' not in st.session_state:
    st.session_state.df = None
if 'filtered_df' not in st.session_state:
    st.session_state.filtered_df = None
if 'pivot_df' not in st.session_state:
    st.session_state.pivot_df = None

# ============================================================================
# SECTION 1: FILE UPLOAD AND DATA PREVIEW
# ============================================================================
st.header("1️⃣ Upload Your Data")
uploaded_file = st.file_uploader("Choose a CSV file", type="csv")

if uploaded_file is not None: #if file is uploaded
    try:
        st.session_state.df = load_csv(uploaded_file)
    except ValueError as e:
        st.error(f"Error loading CSV: {str(e)}")
        st.stop()


    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Data Preview")
        st.dataframe(st.session_state.df.head(10), use_container_width=True)

    with col2:
        st.subheader("Data Info")
        st.write(f"**Shape:** {st.session_state.df.shape[0]} rows × {st.session_state.df.shape[1]} columns")
        st.write("**Column Names & Types:**")
        info_df = pd.DataFrame({
            "Column": st.session_state.df.columns,
            "Type": st.session_state.df.dtypes.astype(str)
        })
        st.dataframe(info_df, use_container_width=True)

    # ========================================================================
    # SECTION 2: DATA FILTERING
    # ========================================================================
    st.header("2️⃣ Filter Your Data")

    with st.expander("Add Filters", expanded=False):
        filters = {}

        for col in st.session_state.df.columns:
            col_type = st.session_state.df[col].dtype

            # Numeric columns
            if pd.api.types.is_numeric_dtype(col_type): #checks if current column is numeric
                min_val = st.session_state.df[col].min() #finds min value of the column values
                max_val = st.session_state.df[col].max() #finds max value of the column values
                selected_range = st.slider( #create slider widget with 2 handles for values
                    f"Filter {col}",
                    min_value=float(min_val),
                    max_value=float(max_val),
                    value=(float(min_val), float(max_val)),
                    key=f"slider_{col}" #unique key for preserving slider state across reruns
                )
                filters[col] = ("range", selected_range) #add slider filter to 'filter' dict

            # Categorical/String columns
            else:
                unique_vals = st.session_state.df[col].unique().tolist()
                selected_vals = st.multiselect(
                    f"Filter {col}",
                    options=unique_vals,
                    default=unique_vals,
                    key=f"multiselect_{col}"
                )
                filters[col] = ("categorical", selected_vals)

        # Apply filters using core.apply_filters
        try:
            st.session_state.filtered_df = apply_filters(st.session_state.df, filters)
        except (KeyError, ValueError, TypeError) as e:
            st.error(f"Error applying filters: {str(e)}")
            st.session_state.filtered_df = st.session_state.df.copy()

        st.info(f"Filtered data: {st.session_state.filtered_df.shape[0]} rows (from {st.session_state.df.shape[0]} total)")

    # after upload and after (optional) filtering
    st.subheader("Filtered Data Preview")
    if st.session_state.filtered_df is not None:
        st.dataframe(st.session_state.filtered_df.head(10), use_container_width=True)
    else:
        st.dataframe(st.session_state.df.head(10), use_container_width=True)

    # ========================================================================
    # SECTION 3: PIVOT TABLE CONFIGURATION
    # ========================================================================
    st.header("3️⃣ Configure Pivot Table")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.subheader("📁 Group By (Rows)")
        group_by_cols = st.multiselect(
            "Select columns to group by",
            options=st.session_state.filtered_df.columns.tolist(),
            key="group_by"
        )

    with col2:
        st.subheader("📊 Aggregate Column")
        agg_col = st.selectbox(
            "Select column to aggregate",
            options=st.session_state.filtered_df.columns.tolist(),
            key="agg_col"
        )

    with col3:
        st.subheader("⚙️ Aggregation Functions")
        agg_functions = st.multiselect(
            "Select aggregation functions",
            options=["sum", "count", "mean", "min", "max", "median", "std", "var"],
            default=["sum"],
            key="agg_funcs"
        )

    # ========================================================================
    # SECTION 4: PIVOT TABLE CALCULATION AND DISPLAY
    # ========================================================================
    if group_by_cols and agg_col and agg_functions:
        st.header("4️⃣ Pivot Table Results")

        try:
            # Create pivot table using core.build_pivot
            pivot_df = build_pivot(st.session_state.filtered_df, group_by_cols, agg_col, agg_functions)

            st.session_state.pivot_df = pivot_df

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
                    total = st.session_state.filtered_df[agg_col].sum()
                    st.metric("Total Value", f"{total:.2f}" if isinstance(total, (int, float)) else total)

            # ================================================================
            # SECTION 5: VISUALIZATION
            # ================================================================
            st.header("5️⃣ Visualizations")

            # Only allow visualizations if we have at most 2 group_by columns
            if len(group_by_cols) <= 2:
                chart_type = st.selectbox(
                    "Select chart type",
                    options=["Bar Chart", "Line Chart", "Area Chart", "Pie Chart"],
                    key="chart_type"
                )

                # Prepare data for visualization
                if len(group_by_cols) == 1:
                    x_col = group_by_cols[0]
                    # Use the first aggregation function for visualization
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

                    st.plotly_chart(fig, use_container_width=True)

                    # ============================================================
                    # SECTION 6: DOWNLOAD OPTIONS
                    # ============================================================
                    st.header("6️⃣ Export Data & Charts")

                    col1, col2, col3 = st.columns(3)

                    with col1:
                        st.subheader("📥 Download Data")
                        # Download pivot table as CSV
                        csv = pivot_df.to_csv(index=False)
                        st.download_button(
                            label="Download Pivot Table (CSV)",
                            data=csv,
                            file_name=f"pivot_table_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                            mime="text/csv"
                        )

                    with col2:
                        st.subheader("📊 Download Chart")
                        # Download chart as HTML
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

                    st.plotly_chart(fig, use_container_width=True)

                    # Export section for 2D pivots
                    st.header("6️⃣ Export Data & Charts")

                    col1, col2, col3 = st.columns(3)

                    with col1:
                        st.subheader("📥 Download Data")
                        csv = pivot_df.to_csv(index=False)
                        st.download_button(
                            label="Download Pivot Table (CSV)",
                            data=csv,
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

        except Exception as e:
            st.error(f"Error creating pivot table: {str(e)}")

    elif not group_by_cols or not agg_col or not agg_functions:
        st.info("👈 Please configure the pivot table settings to generate results")

else:
    st.info("👆 Upload a CSV file to get started!")
