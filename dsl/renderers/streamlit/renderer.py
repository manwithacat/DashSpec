"""
Streamlit Renderer for DashSpec v1.1

Renders dashboard specifications as interactive Streamlit applications

Version: 1.1.0
Compatible with DSL versions: 1.0.x, 1.1.x

For custom visualizations:
    - Create dsl/custom_renderers.py (copy from custom_renderers_template.py)
    - Implement custom render functions
    - They will be automatically registered

Generated renderers are in dsl/viz_renderers.py
DO NOT modify viz_renderers.py - regenerate from DSL spec instead
"""

from pathlib import Path
from typing import Any, Dict

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from dsl.core.adapter import parse, build_ir, execute, validate
from dsl.renderers.streamlit.viz_renderers import get_renderer, list_supported_charts

# Try to import custom renderers if they exist
try:
    from .custom_renderers import (
        CUSTOM_RENDERERS,
        CUSTOM_TRANSFORMS,
        CUSTOM_VALIDATORS,
    )
except ImportError:
    CUSTOM_RENDERERS = {}
    CUSTOM_TRANSFORMS = []
    CUSTOM_VALIDATORS = []


class StreamlitRenderer:
    """Renders DashSpec specifications in Streamlit"""

    # Class-level registries for custom extensions
    CUSTOM_RENDERERS = CUSTOM_RENDERERS
    CUSTOM_TRANSFORMS = CUSTOM_TRANSFORMS
    CUSTOM_VALIDATORS = CUSTOM_VALIDATORS

    # DSL version compatibility
    DSL_VERSION = "1.3.0"
    SUPPORTED_VERSIONS = ["1.0", "1.1", "1.2", "1.3"]

    def __init__(self, spec_path: str, use_tabs: bool = False):
        """
        Initialize renderer with a dashboard specification

        Args:
            spec_path: Path to the YAML dashboard specification file
            use_tabs: If True, use tabs for page navigation instead of sidebar selectbox
        """
        self.spec_path = Path(spec_path)
        self.spec = None
        self.ir = None
        self.use_tabs = use_tabs
        self.load_spec()

    def load_spec(self):
        """Load and validate the dashboard specification"""
        with open(self.spec_path) as f:
            spec_yaml = f.read()

        # Parse
        self.spec = parse(spec_yaml)

        # Validate
        violations = validate(self.spec)
        if violations:
            st.error("Dashboard specification has errors:")
            for v in violations:
                st.error(f"[{v['code']}] {v['message']}")
                st.info(f"Repair hint: {v['repair']}")
            st.stop()

        # Build IR
        self.ir = build_ir(self.spec)

    def render(self):
        """Render the complete dashboard"""
        dashboard = self.spec.get("dashboard", {})

        # Page title - only set page config in standalone mode
        if not self.use_tabs:
            st.set_page_config(page_title=dashboard.get("title", "Dashboard"), layout="wide")
            st.title(dashboard.get("title", "Dashboard"))

            if dashboard.get("description"):
                st.markdown(dashboard["description"])
        else:
            # In gallery mode with tabs, show a smaller title
            st.subheader(dashboard.get("title", "Dashboard"))

        # Page navigation
        pages = dashboard.get("pages", [])

        if len(pages) > 1:
            if self.use_tabs:
                # Use tabs for multi-page navigation in gallery mode
                page_titles = [p.get("title", f"Page {i+1}") for i, p in enumerate(pages)]
                tabs = st.tabs(page_titles)

                for idx, tab in enumerate(tabs):
                    with tab:
                        self.render_page(pages[idx], idx)
            else:
                # Use sidebar selectbox for standalone dashboards
                page_titles = [p.get("title", f"Page {i+1}") for i, p in enumerate(pages)]
                selected_page_title = st.sidebar.selectbox("Select Page", page_titles)
                selected_page_idx = page_titles.index(selected_page_title)
                self.render_page(pages[selected_page_idx], selected_page_idx)
        else:
            # Single page - render directly
            selected_page_idx = 0
            if pages:
                self.render_page(pages[selected_page_idx], selected_page_idx)

    def render_page(self, page: Dict[str, Any], page_idx: int):
        """
        Render a single page

        Args:
            page: Page specification
            page_idx: Page index
        """
        st.header(page.get("title", f"Page {page_idx + 1}"))

        if page.get("description"):
            st.markdown(page["description"])

        # Render filters
        filter_values = {}
        if page.get("filters"):
            st.subheader("Filters")
            filter_cols = st.columns(min(len(page["filters"]), 3))

            for idx, filter_spec in enumerate(page["filters"]):
                col = filter_cols[idx % len(filter_cols)]
                with col:
                    filter_value = self.render_filter(filter_spec)
                    if filter_value is not None:
                        filter_values[filter_spec["id"]] = filter_value

        # Execute with filter values (with graceful error handling)
        inputs = {"filters": filter_values}
        try:
            results = execute(self.ir, inputs)
            page_results = results["pages"][page_idx]
        except Exception as e:
            st.error("❌ Dashboard Execution Failed")

            with st.expander("🔍 Error Details", expanded=True):
                st.markdown(f"**Error Type:** `{type(e).__name__}`")
                st.markdown(f"**Error Message:** {str(e)}")

                # Context-aware repair hints
                repair_hints = []
                error_str = str(e).lower()

                if "keyerror" in type(e).__name__.lower() or "not found" in error_str:
                    repair_hints.append("**Missing Field:** A field referenced in the dashboard spec doesn't exist in the data")
                    repair_hints.append("- Check that all field names in metrics, filters, and visualizations match the data schema")
                    repair_hints.append("- Verify the data file exists and is accessible")

                if "typeerror" in type(e).__name__.lower():
                    repair_hints.append("**Type Mismatch:** Operation attempted on incompatible data type")
                    repair_hints.append("- Check that numeric operations are only on numeric fields")
                    repair_hints.append("- Verify aggregation functions match field types")

                if "valueerror" in type(e).__name__.lower():
                    repair_hints.append("**Invalid Value:** A value doesn't meet expected constraints")
                    repair_hints.append("- Check filter ranges are within data bounds")
                    repair_hints.append("- Verify date formats if using date filters")

                if "filenotfounderror" in type(e).__name__.lower() or "no such file" in error_str:
                    repair_hints.append("**Data File Missing:** The data source file cannot be found")
                    repair_hints.append("- Verify the `data_source.path` in the YAML spec")
                    repair_hints.append("- Run the ETL pipeline if the data hasn't been processed yet")

                if not repair_hints:
                    repair_hints.append("**General Troubleshooting:**")
                    repair_hints.append("- Verify all field names match between spec and data")
                    repair_hints.append("- Check data types are compatible with operations")
                    repair_hints.append("- Ensure data file exists and is readable")

                st.markdown("### 💡 Repair Hints")
                for hint in repair_hints:
                    st.markdown(hint)

                # Show traceback for debugging
                st.markdown("### 🐛 Technical Details")
                import traceback
                st.code(traceback.format_exc(), language="python")

            # Log for server-side debugging
            logger.error(f"Dashboard execution error: {e}", exc_info=True)
            return  # Stop rendering this page

        # Render metrics
        if page.get("metrics"):
            self.render_metrics(page, page_results)

        # Render layout
        if page.get("layout"):
            self.render_layout(page["layout"], page_results)

    def render_filter(self, filter_spec: Dict[str, Any]) -> Any:
        """
        Render a filter widget

        Args:
            filter_spec: Filter specification

        Returns:
            Selected filter value
        """
        label = filter_spec.get("label", filter_spec["field"])
        filter_type = filter_spec["type"]
        default = filter_spec.get("default")

        # Load data to get filter options
        data_path = self.spec["dashboard"]["data_source"]["path"]
        df = pd.read_parquet(data_path)
        field = filter_spec["field"]

        if filter_type == "range":
            min_val = float(df[field].min())
            max_val = float(df[field].max())
            default_range = default if default else [min_val, max_val]
            # Convert default range to floats
            default_range = [float(default_range[0]), float(default_range[1])]
            # Calculate appropriate step size based on range
            range_size = max_val - min_val
            step = range_size / 1000.0 if range_size > 0 else 0.01
            return st.slider(label, min_val, max_val, default_range, step=step)

        elif filter_type == "slider":
            min_val = float(df[field].min())
            max_val = float(df[field].max())
            default_val = default if default is not None else min_val
            # Calculate appropriate step size based on range
            range_size = max_val - min_val
            step = range_size / 1000.0 if range_size > 0 else 0.01
            return st.slider(label, min_val, max_val, default_val, step=step)

        elif filter_type == "select":
            options = sorted(df[field].unique())
            default_val = default if default in options else options[0]
            return st.selectbox(label, options, index=options.index(default_val))

        elif filter_type == "multiselect":
            options = sorted(df[field].unique())
            default_vals = default if default else []
            return st.multiselect(label, options, default=default_vals)

        elif filter_type == "date_range":
            min_date = pd.to_datetime(df[field]).min()
            max_date = pd.to_datetime(df[field]).max()
            return st.date_input(label, [min_date, max_date])

        return None

    def render_metrics(self, page: Dict[str, Any], page_results: Dict[str, Any]):
        """
        Render metrics section

        Args:
            page: Page specification
            page_results: Computed page results
        """
        metrics = page.get("metrics", [])
        if not metrics:
            return

        st.subheader("Key Metrics")

        # Group metrics for display
        metric_cols = st.columns(min(len(metrics), 4))

        for idx, metric_spec in enumerate(metrics):
            col = metric_cols[idx % len(metric_cols)]
            metric_id = metric_spec["id"]
            value = page_results["metrics"].get(metric_id)

            with col:
                label = metric_spec.get("label", metric_id)
                format_spec = metric_spec.get("format", "")

                if value is not None:
                    # Use v1.2 formatting if available
                    if format_spec:
                        try:
                            from .formatting import format_number
                            dashboard_metadata = self.spec.get("dashboard", {}).get("metadata", {})
                            formatted_value = format_number(
                                value, format_spec,
                                field_name=metric_spec.get("field", ""),
                                dashboard_metadata=dashboard_metadata
                            )
                        except:
                            # Fallback to simple string conversion
                            formatted_value = str(value)
                    else:
                        # Auto-format based on type
                        if isinstance(value, float):
                            formatted_value = f"{value:,.2f}"
                        elif isinstance(value, int):
                            formatted_value = f"{value:,}"
                        else:
                            formatted_value = str(value)

                    st.metric(label, formatted_value)
                else:
                    st.metric(label, "N/A")

    def render_layout(self, layout: Dict[str, Any], page_results: Dict[str, Any]):
        """
        Render page layout

        Args:
            layout: Layout specification
            page_results: Computed page results
        """
        layout_type = layout.get("type", "single")
        components = layout.get("components", [])

        if layout_type == "single":
            for component in components:
                self.render_component(component, page_results)

        elif layout_type == "grid":
            # Group components by width
            for component in components:
                width = component.get("width", "full")

                if width == "full":
                    self.render_component(component, page_results)
                elif width == "half":
                    col1, col2 = st.columns(2)
                    with col1:
                        self.render_component(component, page_results)
                elif width == "third":
                    cols = st.columns(3)
                    # Find position
                    idx = components.index(component)
                    with cols[idx % 3]:
                        self.render_component(component, page_results)

        elif layout_type == "tabs":
            tab_names = [c.get("title", f"Tab {i+1}") for i, c in enumerate(components)]
            tabs = st.tabs(tab_names)

            for tab, component in zip(tabs, components):
                with tab:
                    self.render_component(component, page_results)

    def render_component(self, component: Dict[str, Any], page_results: Dict[str, Any]):
        """
        Render a single component

        Args:
            component: Component specification
            page_results: Computed page results
        """
        comp_type = component.get("type")
        title = component.get("title")

        if comp_type == "visualization":
            if title:
                st.subheader(title)
            self.render_visualization(component.get("visualization", {}), page_results)

        elif comp_type == "metric_card":
            metric_id = component.get("metric_id")
            value = page_results["metrics"].get(metric_id)
            if title and value is not None:
                st.metric(title, value)

        elif comp_type == "text":
            if title:
                st.subheader(title)
            text = component.get("text", "")
            st.markdown(text)

        elif comp_type == "divider":
            st.divider()

    def render_visualization(self, viz: Dict[str, Any], page_results: Dict[str, Any]):
        """
        Render a visualization using pluggable renderer system

        Renderer priority:
            1. Custom renderers (CUSTOM_RENDERERS dict)
            2. Generated renderers (viz_renderers.py)
            3. Legacy renderers (backward compatibility)

        Args:
            viz: Visualization specification
            page_results: Computed page results
        """
        chart_type = viz.get("chart_type")
        df = page_results["data"]

        # Apply limit
        limit = viz.get("limit") or viz.get("params", {}).get("limit")
        if limit and len(df) > limit:
            df = df.head(limit)

        # Apply sorting
        if viz.get("sort"):
            sort_field = viz["sort"].get("field")
            sort_order = viz["sort"].get("order", "asc")
            ascending = sort_order == "asc"
            if sort_field in df.columns:
                df = df.sort_values(by=sort_field, ascending=ascending)

        # Priority 1: Check for custom renderer
        if chart_type in self.CUSTOM_RENDERERS:
            try:
                self.CUSTOM_RENDERERS[chart_type](df, viz, st)
                return
            except Exception as e:
                st.error(f"Custom renderer for '{chart_type}' failed: {e}")
                st.exception(e)
                return

        # Priority 2: Check for generated renderer
        renderer = get_renderer(chart_type)
        if renderer:
            try:
                # Get dashboard metadata and data_source formatting for context
                dashboard = self.spec.get("dashboard", {})
                dashboard_metadata = dashboard.get("metadata", {})
                data_source = dashboard.get("data_source", {})
                default_formatting = data_source.get("default_formatting", {})
                formatting = data_source.get("formatting", {})
                column_labels = data_source.get("column_labels", {})

                # Enrich metadata with formatting info for renderers
                rendering_context = {
                    **dashboard_metadata,
                    "default_formatting": default_formatting,
                    "formatting": formatting,
                    "column_labels": column_labels
                }

                # Try calling with metadata, fall back to old signature if needed
                import inspect
                sig = inspect.signature(renderer)
                if len(sig.parameters) >= 4:
                    renderer(df, viz, st, rendering_context)
                else:
                    renderer(df, viz, st)
                return
            except Exception as e:
                st.error(f"Generated renderer for '{chart_type}' failed: {e}")
                st.exception(e)
                return

        # Priority 3: Legacy renderers (for backward compatibility with v1.0)
        if chart_type == "line":
            fig = px.line(
                df, x=viz.get("x_field"), y=viz.get("y_field"), color=viz.get("color_field")
            )
            st.plotly_chart(fig)

        elif chart_type == "bar":
            fig = px.bar(
                df, x=viz.get("x_field"), y=viz.get("y_field"), color=viz.get("color_field")
            )
            st.plotly_chart(fig)

        elif chart_type == "scatter":
            fig = px.scatter(
                df,
                x=viz.get("x_field"),
                y=viz.get("y_field"),
                color=viz.get("color_field"),
                size=viz.get("size_field"),
            )
            st.plotly_chart(fig)

        elif chart_type == "histogram":
            fig = px.histogram(df, x=viz.get("x_field"), color=viz.get("color_field"))
            st.plotly_chart(fig)

        elif chart_type == "box":
            fig = px.box(
                df, x=viz.get("x_field"), y=viz.get("y_field"), color=viz.get("color_field")
            )
            st.plotly_chart(fig)

        elif chart_type == "pie":
            # Group data for pie chart
            x_field = viz.get("x_field")
            if x_field:
                pie_data = df[x_field].value_counts().reset_index()
                pie_data.columns = ["category", "count"]
                fig = px.pie(pie_data, names="category", values="count")
                st.plotly_chart(fig)

        elif chart_type == "table":
            st.dataframe(df)

        elif chart_type == "heatmap":
            # Create pivot table for heatmap
            x_field = viz.get("x_field")
            y_field = viz.get("y_field")
            color_field = viz.get("color_field")

            if x_field and y_field and color_field:
                pivot = df.pivot_table(
                    values=color_field, index=y_field, columns=x_field, aggfunc="mean"
                )
                fig = px.imshow(pivot)
                st.plotly_chart(fig)

        else:
            # Chart type not found in any renderer
            st.error(f"Unknown chart type: '{chart_type}'")
            st.info(f"Supported chart types: {', '.join(sorted(list_supported_charts()))}")
            st.info(
                "To add custom chart types:\n"
                "1. Copy dsl/custom_renderers_template.py to dsl/custom_renderers.py\n"
                "2. Implement your renderer function\n"
                "3. Add to CUSTOM_RENDERERS dict"
            )


def render_dashboard(spec_path: str):
    """
    Render a dashboard from a specification file

    Args:
        spec_path: Path to YAML dashboard specification
    """
    renderer = StreamlitRenderer(spec_path)
    renderer.render()
