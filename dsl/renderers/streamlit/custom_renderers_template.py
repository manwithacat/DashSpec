"""
Custom Visualization Renderers Template

This file provides a template for creating custom visualization renderers
that override or extend the generated DashSpec renderers.

SAFE TO MODIFY - This is your custom code that won't be overwritten!

Usage:
    1. Copy this file to custom_renderers.py
    2. Implement your custom renderer methods
    3. Import and use in your dashboard:

        from custom_renderers import CustomRenderers
        # Renderers will be auto-registered

Example Custom Renderer:
    def render_custom_gauge(df, viz, st_module):
        value = df[viz['roles']['value']].iloc[0]
        max_val = viz.get('params', {}).get('max', 100)

        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=value,
            domain={'x': [0, 1], 'y': [0, 1]},
            gauge={'axis': {'range': [None, max_val]}}
        ))
        st_module.plotly_chart(fig)

    # Register custom renderer
    CUSTOM_RENDERERS['gauge'] = render_custom_gauge
"""

from typing import Any, Dict
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# Import base renderers
from dsl.renderers.streamlit.viz_renderers import VizRenderers

# Registry for custom renderers
# chart_type -> renderer function
CUSTOM_RENDERERS = {}


# ===== Example Custom Renderers =====

def render_custom_metric_card(df: pd.DataFrame, viz: Dict[str, Any], st_module) -> None:
    """
    Example: Custom metric card with trend indicator

    Roles:
        value: field to display
        previous: field for comparison (optional)

    Params:
        format: number format string
        icon: icon name
    """
    roles = viz.get("roles", {})
    params = viz.get("params", {})

    value_field = roles.get("value")
    previous_field = roles.get("previous")

    if not value_field:
        st_module.error("Custom metric card requires 'value' role")
        return

    value = df[value_field].iloc[0] if len(df) > 0 else 0

    # Calculate delta if previous provided
    delta = None
    if previous_field and previous_field in df.columns:
        previous = df[previous_field].iloc[0] if len(df) > 0 else 0
        delta = value - previous

    # Format value
    fmt = params.get("format", "{:,.0f}")
    formatted_value = fmt.format(value)

    # Display metric
    label = viz.get("title", value_field)
    st_module.metric(label=label, value=formatted_value, delta=delta)


def render_custom_annotated_heatmap(df: pd.DataFrame, viz: Dict[str, Any], st_module) -> None:
    """
    Example: Heatmap with custom annotations

    Roles:
        x, y, z: standard heatmap roles

    Params:
        annotation_format: format string for annotations
        color_scale: plotly color scale name
    """
    roles = viz.get("roles", {})
    params = viz.get("params", {})

    x = roles.get("x")
    y = roles.get("y")
    z = roles.get("z")

    if not (x and y and z):
        st_module.error("Annotated heatmap requires 'x', 'y', and 'z' roles")
        return

    pivot = df.pivot_table(values=z, index=y, columns=x, aggfunc="mean")

    # Create annotations
    annotation_format = params.get("annotation_format", ".2f")
    annotations = []
    for i, row in enumerate(pivot.index):
        for j, col in enumerate(pivot.columns):
            val = pivot.iloc[i, j]
            if pd.notna(val):
                annotations.append(
                    dict(
                        x=col,
                        y=row,
                        text=f"{val:{annotation_format}}",
                        showarrow=False,
                        font=dict(color="white" if val < pivot.values.mean() else "black")
                    )
                )

    fig = go.Figure(data=go.Heatmap(
        z=pivot.values,
        x=pivot.columns,
        y=pivot.index,
        colorscale=params.get("color_scale", "RdBu_r")
    ))

    fig.update_layout(annotations=annotations)
    st_module.plotly_chart(fig)


# ===== Register Custom Renderers =====

# Uncomment to activate custom renderers:
# CUSTOM_RENDERERS['metric_card'] = render_custom_metric_card
# CUSTOM_RENDERERS['annotated_heatmap'] = render_custom_annotated_heatmap


# ===== Custom Data Transforms =====

def custom_transform_add_derived_fields(page: Dict[str, Any]) -> Dict[str, Any]:
    """
    Example: Add derived fields to page data

    This transform runs before visualization rendering
    """
    # Your custom logic here
    return page


def custom_transform_filter_outliers(page: Dict[str, Any]) -> Dict[str, Any]:
    """
    Example: Remove outliers from data

    This transform runs before visualization rendering
    """
    # Your custom logic here
    return page


# Registry for custom transforms
# Transforms are applied in order before rendering
CUSTOM_TRANSFORMS = [
    # Uncomment to activate:
    # custom_transform_add_derived_fields,
    # custom_transform_filter_outliers,
]


# ===== Custom Validators =====

def custom_validator_check_data_quality(spec: Dict[str, Any], df: pd.DataFrame) -> list:
    """
    Example: Custom data quality validator

    Returns:
        List of validation violations
    """
    violations = []

    # Example: Check for minimum row count
    if len(df) < 100:
        violations.append({
            "code": "INSUFFICIENT_DATA",
            "message": f"Dataset has only {len(df)} rows, minimum 100 required",
            "path": "/data",
            "repair": "Ensure dataset has sufficient data"
        })

    return violations


# Registry for custom validators
CUSTOM_VALIDATORS = [
    # Uncomment to activate:
    # custom_validator_check_data_quality,
]


# ===== Helper Functions =====

def register_all_custom_renderers():
    """
    Register all custom renderers with the main renderer

    Call this in your dashboard initialization
    """
    from dsl import streamlit_renderer

    # Register custom renderers
    streamlit_renderer.StreamlitRenderer.CUSTOM_RENDERERS.update(CUSTOM_RENDERERS)

    # Register custom transforms
    streamlit_renderer.StreamlitRenderer.CUSTOM_TRANSFORMS.extend(CUSTOM_TRANSFORMS)

    # Register custom validators
    streamlit_renderer.StreamlitRenderer.CUSTOM_VALIDATORS.extend(CUSTOM_VALIDATORS)

    print(f"Registered {len(CUSTOM_RENDERERS)} custom renderers")
    print(f"Registered {len(CUSTOM_TRANSFORMS)} custom transforms")
    print(f"Registered {len(CUSTOM_VALIDATORS)} custom validators")
