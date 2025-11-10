"""
DashSpec v1.1 Dashboard Gallery - Unified Streamlit App

Deployment-ready application showcasing multiple analytics dashboards
with tabbed interface and dataset metadata integration.

Usage:
    streamlit run app.py

Or deploy to Streamlit Cloud:
    https://share.streamlit.io/
"""

import json
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd
import streamlit as st

from dsl import StreamlitRenderer

# Dashboard configuration with metadata
DASHBOARDS = {
    "Credit Card Fraud Detection": {
        "spec": "dsl/examples/fraud_detection.yaml",
        "icon": "💳",
        "description": "Detect fraudulent transactions and analyze patterns in 283K credit card transactions",
        "category": "Finance & Risk",
        "dataset_size": "283K rows",
        "key_metrics": ["Fraud Rate", "Transaction Amount", "Feature Correlations"],
    },
    "US Air Quality & Pollution": {
        "spec": "dsl/examples/us_pollution.yaml",
        "icon": "🌍",
        "description": "Monitor air quality trends across 47 US states with 1.7M measurements (2000-2016)",
        "category": "Environmental",
        "dataset_size": "1.7M rows",
        "key_metrics": ["NO2 AQI", "O3 Levels", "Pollutant Correlations"],
    },
    "Spotify Music Analytics": {
        "spec": "dsl/examples/spotify_tracks.yaml",
        "icon": "🎵",
        "description": "Explore audio features and popularity patterns across 114K tracks and 114 genres",
        "category": "Entertainment",
        "dataset_size": "114K rows",
        "key_metrics": ["Danceability", "Energy", "Popularity"],
    },
    "Amazon Food Reviews": {
        "spec": "dsl/examples/amazon_reviews.yaml",
        "icon": "⭐",
        "description": "Analyze customer sentiment and review helpfulness in 568K product reviews",
        "category": "E-Commerce",
        "dataset_size": "568K rows",
        "key_metrics": ["Rating Distribution", "Helpfulness", "Temporal Trends"],
    },
    "IBM HR Employee Attrition": {
        "spec": "dsl/examples/ibm_hr_attrition.yaml",
        "icon": "👥",
        "description": "Predict employee attrition and analyze retention factors across 1,470 employees",
        "category": "Human Resources",
        "dataset_size": "1,470 rows",
        "key_metrics": ["Attrition Rate", "Satisfaction", "Compensation"],
    },
    "US Traffic Accidents": {
        "spec": "dsl/examples/us_accidents.yaml",
        "icon": "🚗",
        "description": "Explore accident patterns and severity across 7.7M incidents (2016-2023)",
        "category": "Public Safety",
        "dataset_size": "7.7M rows",
        "key_metrics": ["Severity", "Weather Impact", "Geographic Hotspots"],
    },
    "TMDB Movies & Box Office": {
        "spec": "dsl/examples/tmdb_movies.yaml",
        "icon": "🎬",
        "description": "Analyze box office performance and success factors for 5,000 movies",
        "category": "Entertainment",
        "dataset_size": "4,803 rows",
        "key_metrics": ["Revenue", "Budget ROI", "Rating Correlations"],
    },
    "Network Intrusion Detection": {
        "spec": "dsl/examples/network_intrusion.yaml",
        "icon": "🔒",
        "description": "Detect cybersecurity threats and analyze network traffic patterns (47K connections)",
        "category": "Cybersecurity",
        "dataset_size": "47K rows",
        "key_metrics": ["Protocol Distribution", "Error Rates", "Traffic Patterns"],
    },
    "Global Power Consumption": {
        "spec": "dsl/examples/power_consumption.yaml",
        "icon": "⚡",
        "description": "Analyze household electricity usage patterns across 2M+ measurements (2006-2010)",
        "category": "Energy & Utilities",
        "dataset_size": "2.1M rows",
        "key_metrics": ["Active Power", "Sub-Metering", "Voltage Quality"],
    },
    "Global Food Price Inflation": {
        "spec": "dsl/examples/food_price_inflation.yaml",
        "icon": "🌾",
        "description": "Track food price inflation trends with enhanced formatting and labels (v1.2)",
        "category": "Economics & Trade",
        "dataset_size": "4,798 rows",
        "key_metrics": ["Inflation Rate", "Price Volatility", "Temporal Trends"],
    },
}

# Category colors for visual organization
CATEGORY_COLORS = {
    "Finance & Risk": "#FF6B6B",
    "Environmental": "#4ECDC4",
    "Entertainment": "#95E1D3",
    "E-Commerce": "#F38181",
    "Human Resources": "#AA96DA",
    "Public Safety": "#FCBAD3",
    "Cybersecurity": "#A8E6CF",
    "Energy & Utilities": "#FFD93D",
    "Economics & Trade": "#FFA07A",
}


def load_dataset_metadata(spec_path: str) -> Optional[Dict]:
    """Load metadata from dashboard specification"""
    try:
        import yaml
        with open(spec_path) as f:
            spec = yaml.safe_load(f)
        return spec.get("dashboard", {}).get("metadata", {})
    except Exception as e:
        st.warning(f"Could not load metadata: {e}")
        return None


def count_dashboard_pages(spec_path: str) -> int:
    """Count number of pages in a dashboard"""
    try:
        import yaml
        with open(spec_path) as f:
            spec = yaml.safe_load(f)
        pages = spec.get("dashboard", {}).get("pages", [])
        return len(pages)
    except Exception:
        return 1


def render_dashboard_card(name: str, config: Dict, col):
    """Render a dashboard selection card with clickable button"""
    with col:
        # Card styling
        category_color = CATEGORY_COLORS.get(config["category"], "#CCCCCC")

        # Count pages
        num_pages = count_dashboard_pages(config["spec"])
        page_badge = f'📑 {num_pages} pages' if num_pages > 1 else ''

        st.markdown(f"""
        <div style="
            padding: 1.5rem;
            border-radius: 0.5rem;
            border-left: 4px solid {category_color};
            background-color: #f8f9fa;
            margin-bottom: 1rem;
            min-height: 240px;
        ">
            <div style="
                display: inline-block;
                background-color: {category_color};
                color: white;
                padding: 0.25rem 0.75rem;
                border-radius: 1rem;
                font-size: 0.75em;
                font-weight: 600;
                margin-bottom: 0.75rem;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            ">
                {config['category']}
            </div>
            <h3 style="margin-top: 0.5rem; margin-bottom: 0.5rem;">{config['icon']} {name}</h3>
            <p style="color: #888; font-size: 0.85em; margin-bottom: 0.75rem;">
                📦 {config['dataset_size']} {f'• {page_badge}' if page_badge else ''}
            </p>
            <p style="font-size: 0.95em; line-height: 1.5; margin-bottom: 0.75rem;">
                {config['description']}
            </p>
            <p style="font-size: 0.85em; color: #888;">
                📊 {', '.join(config['key_metrics'][:2])}
            </p>
        </div>
        """, unsafe_allow_html=True)

        # Add clickable button to navigate to dashboard
        if st.button(f"🚀 Open Dashboard", key=f"btn_{name}", use_container_width=True):
            st.session_state.current_page = "📊 Dashboards"
            st.session_state.selected_dashboard = name
            st.rerun()


def render_home_page():
    """Render the dashboard gallery home page"""
    st.title("🚀 DashSpec v1.2 Dashboard Gallery")

    st.markdown("""
    ### Welcome to the Interactive Analytics Platform

    Explore **10 production-ready dashboards** built with DashSpec v1.2, featuring:
    - 📊 **15+ advanced visualizations** (ECDF, violin plots, hexbin, KDE, correlation heatmaps)
    - 🎯 **Role-based specifications** for clearer, more semantic chart definitions
    - 💎 **Professional formatting** with currency symbols, percentages, and human-readable labels
    - 🛡️ **Data quality management** with declarative rules for outliers, missing values, and validation
    - 🔍 **Interactive filtering** and real-time data exploration
    - 📑 **Multi-page dashboards** with seamless tab navigation
    - 📈 **12.6M+ data points** across diverse domains

    ---
    """)

    # Statistics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Dashboards", "10")
    with col2:
        st.metric("Total Rows", "12.6M+")
    with col3:
        st.metric("Chart Types", "15+")
    with col4:
        st.metric("Categories", f"{len(set(d['category'] for d in DASHBOARDS.values()))}")

    st.markdown("---")
    st.subheader("📚 Dashboard Gallery")
    st.markdown("Select a dashboard below to begin exploring:")

    # Display all dashboards in 2-column grid
    dashboard_items = list(DASHBOARDS.items())

    # Create columns for cards (2 per row)
    for i in range(0, len(dashboard_items), 2):
        cols = st.columns(2)
        for j, col in enumerate(cols):
            if i + j < len(dashboard_items):
                name, config = dashboard_items[i + j]
                render_dashboard_card(name, config, col)

    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #666; padding: 2rem 0;">
        <p><strong>Powered by DashSpec v1.1</strong></p>
        <p style="font-size: 0.9em;">
            Advanced declarative dashboard specification language with
            role-based visualizations and comprehensive analytics capabilities.
        </p>
        <p style="font-size: 0.85em; margin-top: 1rem;">
            🔧 Built with: Streamlit • Plotly • Pandas • DashSpec
        </p>
    </div>
    """, unsafe_allow_html=True)


def render_about_page():
    """Render the about/documentation page"""
    st.title("📖 About DashSpec v1.1")

    st.markdown("""
    ## What is DashSpec?

    DashSpec is a **declarative dashboard specification language** that enables you to create
    rich, interactive data analytics dashboards using simple YAML configurations.

    ### Key Features

    #### 🎯 Role-Based Visualizations
    Define chart mappings using semantic roles instead of field names:

    ```yaml
    visualization:
      chart_type: "scatter"
      roles:
        x: "amount"
        y: "time"
        color: "class"
        size: "metric"
      params:
        trendline: "ols"
        alpha: 0.6
    ```

    #### 📊 15+ Advanced Chart Types

    **Level 0-1: Tables & Distributions**
    - Table, Summary Statistics
    - Histogram, ECDF
    - Box Plot, Violin Plot, KDE

    **Level 2: Relationships**
    - Scatter (with trendlines)
    - Hexbin Density Maps
    - 2D Kernel Density

    **Level 3: Categoricals**
    - Line, Bar, Pie
    - Heatmap, Correlation Heatmap

    #### 🔄 Multi-Page Layouts
    Organize complex analyses into multiple pages with shared filters and metrics.

    #### ⚡ High Performance
    - Smart data sampling for large datasets
    - Efficient aggregations
    - Logarithmic scales for skewed distributions

    ### Architecture

    ```
    YAML Spec → Parser → Validator → IR Builder → Streamlit Renderer → Interactive Dashboard
    ```

    ### Version 1.1 Enhancements

    - ✅ Role-based specifications (clearer, more semantic)
    - ✅ 15 advanced visualization types
    - ✅ Enhanced correlation analysis
    - ✅ Summary statistics with custom percentiles
    - ✅ Improved filtering and metrics
    - ✅ Dataset metadata integration
    - ✅ Full backward compatibility with v1.0

    ### Technology Stack

    - **Frontend**: Streamlit
    - **Visualizations**: Plotly Express & Graph Objects
    - **Data Processing**: Pandas, NumPy
    - **Specification**: YAML + JSON Schema
    - **Storage**: Apache Parquet (columnar)

    ### Use Cases

    DashSpec is ideal for:
    - 📈 Business intelligence dashboards
    - 🔬 Data science exploration
    - 📊 Analytics reporting
    - 🎓 Educational demonstrations
    - 🔍 Ad-hoc data analysis

    ### Getting Started

    1. Choose a dashboard from the gallery
    2. Explore the interactive visualizations
    3. Apply filters to drill down into the data
    4. Review the YAML specification for customization

    ### Documentation

    - **User Guide**: `docs/dsl_v1.1_guide.md`
    - **Implementation**: `dev_docs/dsl_v1.1_implementation.md`
    - **Gallery Guide**: `dev_docs/dashboard_gallery.md`
    - **Examples**: `dsl/examples/`

    ### Open Source

    DashSpec is built with open-source technologies and follows modern
    software engineering practices including validation, testing, and documentation.
    """)


def main():
    """Main application entry point"""

    # Page configuration
    st.set_page_config(
        page_title="DashSpec v1.2 Dashboard Gallery",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="collapsed"
    )

    # Custom CSS for better styling
    st.markdown("""
    <style>
        .stTabs [data-baseweb="tab-list"] {
            gap: 8px;
        }
        .stTabs [data-baseweb="tab"] {
            padding: 10px 20px;
            background-color: #f0f2f6;
            border-radius: 4px 4px 0 0;
        }
        .stTabs [aria-selected="true"] {
            background-color: #ffffff;
            border-bottom: 2px solid #FF4B4B;
        }
        .metric-card {
            background-color: #f8f9fa;
            padding: 1rem;
            border-radius: 0.5rem;
            border-left: 4px solid #FF4B4B;
        }
    </style>
    """, unsafe_allow_html=True)

    # Initialize session state
    if "current_page" not in st.session_state:
        st.session_state.current_page = "🏠 Gallery Home"
    if "selected_dashboard" not in st.session_state:
        st.session_state.selected_dashboard = list(DASHBOARDS.keys())[0]

    # Sidebar navigation
    with st.sidebar:
        st.title("🎛️ DashSpec")

        # Simple menu items as buttons
        st.markdown("### Navigation")

        if st.button("🏠 Gallery Home", key="nav_home", use_container_width=True,
                     type="primary" if st.session_state.current_page == "🏠 Gallery Home" else "secondary"):
            st.session_state.current_page = "🏠 Gallery Home"
            st.rerun()

        if st.button("📊 Dashboards", key="nav_dashboards", use_container_width=True,
                     type="primary" if st.session_state.current_page == "📊 Dashboards" else "secondary"):
            st.session_state.current_page = "📊 Dashboards"
            st.rerun()

        if st.button("📖 About", key="nav_about", use_container_width=True,
                     type="primary" if st.session_state.current_page == "📖 About" else "secondary"):
            st.session_state.current_page = "📖 About"
            st.rerun()

        st.markdown("---")

        if st.session_state.current_page == "📊 Dashboards":
            st.subheader("Select Dashboard")

            # Sync selectbox with session state
            dashboard_index = list(DASHBOARDS.keys()).index(st.session_state.selected_dashboard)

            dashboard_name = st.selectbox(
                "Choose a dashboard:",
                options=list(DASHBOARDS.keys()),
                index=dashboard_index,
                format_func=lambda x: f"{DASHBOARDS[x]['icon']} {x}"
            )

            # Update session state when selectbox changes
            if dashboard_name != st.session_state.selected_dashboard:
                st.session_state.selected_dashboard = dashboard_name
                st.rerun()  # Trigger immediate re-render

            # Show dashboard info
            config = DASHBOARDS[dashboard_name]
            st.markdown(f"""
            **Category:** {config['category']}

            **Size:** {config['dataset_size']}

            **Description:** {config['description']}
            """)
        else:
            dashboard_name = None

        # Additional info
        st.markdown("---")
        st.markdown("""
        ### 📊 Statistics
        - **Total Dashboards:** 10
        - **Total Data:** 12.6M+ rows
        - **Chart Types:** 15+
        - **DSL Version:** 1.2.0
        """)

        st.markdown("---")
        st.markdown("""
        <div style="font-size: 0.8em; color: #666;">
            <p><strong>DashSpec v1.2</strong></p>
            <p>Declarative Dashboard Specification Language</p>
        </div>
        """, unsafe_allow_html=True)

    # Main content area
    if st.session_state.current_page == "🏠 Gallery Home":
        render_home_page()

    elif st.session_state.current_page == "📖 About":
        render_about_page()

    elif st.session_state.current_page == "📊 Dashboards" and st.session_state.selected_dashboard:
        # Render selected dashboard
        config = DASHBOARDS[st.session_state.selected_dashboard]
        spec_path = config["spec"]

        # Check if spec file exists
        if not Path(spec_path).exists():
            st.error(f"Dashboard specification not found: {spec_path}")
            st.info("Please ensure all example dashboards are in the `dsl/examples/` directory.")
            return

        # Load and display metadata
        metadata = load_dataset_metadata(spec_path)
        if metadata:
            with st.expander("ℹ️ Dataset Information", expanded=False):
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(f"**Dataset:** {metadata.get('dataset_name', 'N/A')}")
                    st.markdown(f"**Source:** {metadata.get('source', 'N/A')}")
                    st.markdown(f"**Rows:** {metadata.get('rows', 'N/A'):,}")
                with col2:
                    st.markdown(f"**Description:** {metadata.get('description', 'N/A')}")
                    if 'use_cases' in metadata:
                        st.markdown("**Use Cases:**")
                        for uc in metadata['use_cases'][:3]:
                            st.markdown(f"- {uc}")

        # Render the dashboard with tabs for multi-page navigation
        try:
            renderer = StreamlitRenderer(spec_path, use_tabs=True)
            renderer.render()
        except Exception as e:
            st.error(f"Error rendering dashboard: {e}")
            st.exception(e)
            st.info("Check the dashboard specification for errors or missing data files.")


if __name__ == "__main__":
    main()
