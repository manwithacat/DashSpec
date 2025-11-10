"""
Dashboard Specification Language (DSL)

A declarative YAML-based language for defining analytics dashboards
with support for multiple visualization backends.

Public API provides access to core functionality and renderers.
"""

# Core DSL functionality
from dsl.core import (
    parse,
    build_ir,
    validate,
    execute,
    Violation,
    ViolationSeverity,
    DataLoader,
    DataQualityProcessor,
    format_number,
    format_dataframe_columns,
    get_column_labels,
    get_currency_symbol,
)

# Streamlit renderer
from dsl.renderers.streamlit import StreamlitRenderer

__version__ = "1.3.0"

__all__ = [
    # Core
    "parse",
    "build_ir",
    "validate",
    "execute",
    "Violation",
    "ViolationSeverity",
    "DataLoader",
    "DataQualityProcessor",
    "format_number",
    "format_dataframe_columns",
    "get_column_labels",
    "get_currency_symbol",
    # Renderers
    "StreamlitRenderer",
]
