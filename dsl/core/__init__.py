"""
Core DSL functionality (visualization-agnostic)

This module contains the core logic for the Dashboard Specification Language (DSL),
including validation, intermediate representation, execution, data loading, data quality,
and formatting. All code here is independent of any specific visualization library.
"""

from dsl.core.adapter import (
    parse,
    build_ir,
    validate,
    execute,
    Violation,
    ViolationSeverity,
)
from dsl.core.data_loader import DataLoader
from dsl.core.data_quality import DataQualityProcessor
from dsl.core.formatting import (
    format_number,
    format_dataframe_columns,
    get_column_labels,
    get_currency_symbol,
)

__all__ = [
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
]
