"""
DashSpec Formatting Utilities v1.2

Handles number, currency, date formatting and column label mapping for visualizations.
"""

from typing import Any, Dict, Optional, Union
import pandas as pd
import numpy as np
from datetime import datetime, date


# Currency symbols mapping (ISO 4217)
CURRENCY_SYMBOLS = {
    'USD': '$', 'EUR': '€', 'GBP': '£', 'JPY': '¥', 'CNY': '¥',
    'INR': '₹', 'AUD': 'A$', 'CAD': 'C$', 'CHF': 'CHF', 'SEK': 'kr',
    'NOK': 'kr', 'DKK': 'kr', 'RUB': '₽', 'BRL': 'R$', 'ZAR': 'R',
    'KRW': '₩', 'MXN': 'Mex$', 'SGD': 'S$', 'HKD': 'HK$', 'NZD': 'NZ$',
    'TRY': '₺', 'PLN': 'zł', 'THB': '฿', 'IDR': 'Rp', 'MYR': 'RM',
    'PHP': '₱', 'CZK': 'Kč', 'ILS': '₪', 'CLP': 'CLP$', 'TWD': 'NT$',
    'SAR': 'SR', 'AED': 'AED', 'NGN': '₦', 'EGP': 'E£', 'PKR': 'Rs',
    'VND': '₫', 'ARS': 'AR$', 'COP': 'COL$', 'PEN': 'S/',
}


def get_currency_symbol(currency_code: str) -> str:
    """Get currency symbol from ISO 4217 code"""
    return CURRENCY_SYMBOLS.get(currency_code.upper(), currency_code + ' ')


def resolve_field_formatting(
    field_name: str,
    formatting: Optional[Dict[str, Dict]] = None,
    default_formatting: Optional[Dict] = None
) -> Optional[Dict]:
    """
    Resolve formatting for a field using inheritance

    Priority:
    1. Field-specific formatting (highest priority)
    2. Default formatting (fallback)
    3. None (no formatting)

    Args:
        field_name: Name of the field
        formatting: Dict of field-specific formatting rules
        default_formatting: Default formatting to apply to all fields

    Returns:
        Resolved formatting dict or None
    """
    # Check field-specific formatting first
    if formatting and field_name in formatting:
        field_format = formatting[field_name]
        # If default formatting exists, merge them (field-specific overrides defaults)
        if default_formatting:
            merged = {**default_formatting, **field_format}
            return merged
        return field_format

    # Fall back to default formatting
    if default_formatting:
        return default_formatting

    return None


def infer_currency_from_context(
    field_name: str,
    dashboard_metadata: Optional[Dict] = None,
    country: Optional[str] = None
) -> Optional[str]:
    """
    Infer currency code from context

    Priority:
    1. Dashboard metadata currency
    2. Field name patterns (price, cost, revenue, etc.)
    3. Country-based inference
    """
    # Check dashboard metadata first
    if dashboard_metadata and 'currency' in dashboard_metadata:
        return dashboard_metadata['currency']

    # Field name patterns suggest currency
    field_lower = field_name.lower()
    currency_keywords = ['price', 'cost', 'revenue', 'income', 'salary',
                        'payment', 'amount', 'total', 'balance', 'fee']

    is_monetary = any(keyword in field_lower for keyword in currency_keywords)

    if not is_monetary:
        return None

    # Country-based inference
    country_currency_map = {
        'United States': 'USD', 'USA': 'USD', 'US': 'USD',
        'United Kingdom': 'GBP', 'UK': 'GBP', 'Britain': 'GBP',
        'Canada': 'CAD', 'Australia': 'AUD', 'New Zealand': 'NZD',
        'Japan': 'JPY', 'China': 'CNY', 'India': 'INR',
        'Germany': 'EUR', 'France': 'EUR', 'Italy': 'EUR', 'Spain': 'EUR',
        'Brazil': 'BRL', 'South Africa': 'ZAR', 'Mexico': 'MXN',
        'South Korea': 'KRW', 'Singapore': 'SGD', 'Hong Kong': 'HKD',
    }

    if country:
        for country_key, currency in country_currency_map.items():
            if country_key.lower() in country.lower():
                return currency

    # Default to USD for monetary fields without specific context
    return 'USD'


def format_number(
    value: Union[int, float],
    format_spec: Union[str, Dict],
    field_name: Optional[str] = None,
    dashboard_metadata: Optional[Dict] = None
) -> str:
    """
    Format a number according to specification

    Args:
        value: Number to format
        format_spec: Either a string (legacy) or FieldFormat dict
        field_name: Name of field (for currency inference)
        dashboard_metadata: Dashboard metadata for context

    Returns:
        Formatted string
    """
    if pd.isna(value):
        return 'N/A'

    # Handle legacy string formats
    if isinstance(format_spec, str):
        return _format_legacy(value, format_spec)

    # Enhanced formatting
    if not isinstance(format_spec, dict):
        return str(value)

    format_type = format_spec.get('type', 'number')
    precision = format_spec.get('precision')
    use_thousands = format_spec.get('use_thousands_separator', True)
    significant_digits = format_spec.get('significant_digits')
    currency_code = format_spec.get('currency_code')

    # Handle different format types
    if format_type == 'integer':
        formatted = f"{int(value):,}" if use_thousands else str(int(value))

    elif format_type == 'percent':
        # Value is assumed to be in decimal form (0.15 = 15%)
        pct_value = value * 100
        if precision is not None:
            formatted = f"{pct_value:.{precision}f}%"
        else:
            formatted = f"{pct_value:.1f}%"
        if use_thousands:
            # Add commas to the number before %
            parts = formatted.split('%')
            parts[0] = f"{float(parts[0]):,.{precision if precision else 1}f}"
            formatted = parts[0] + '%'

    elif format_type == 'currency':
        # Infer currency if not specified
        if not currency_code:
            currency_code = infer_currency_from_context(
                field_name or '', dashboard_metadata
            )

        symbol = get_currency_symbol(currency_code) if currency_code else '$'

        if significant_digits:
            # Format with significant digits
            formatted_val = _format_significant_digits(abs(value), significant_digits)
        elif precision is not None:
            formatted_val = f"{abs(value):.{precision}f}"
        else:
            formatted_val = f"{abs(value):.2f}"

        if use_thousands:
            # Add thousand separators
            parts = formatted_val.split('.')
            parts[0] = f"{int(parts[0]):,}"
            formatted_val = '.'.join(parts)

        # Handle negative values
        if value < 0:
            formatted = f"-{symbol}{formatted_val}"
        else:
            formatted = f"{symbol}{formatted_val}"

    elif format_type == 'number':
        if significant_digits:
            formatted = _format_significant_digits(value, significant_digits)
        elif precision is not None:
            formatted = f"{value:.{precision}f}"
        else:
            # Auto precision: integers get no decimals, floats get up to 3
            if isinstance(value, int) or value == int(value):
                formatted = str(int(value))
            else:
                formatted = f"{value:.3f}".rstrip('0').rstrip('.')

        if use_thousands and '.' in formatted:
            parts = formatted.split('.')
            parts[0] = f"{int(float(parts[0])):,}"
            formatted = '.'.join(parts)
        elif use_thousands:
            formatted = f"{int(float(formatted)):,}"

    else:
        formatted = str(value)

    return formatted


def _format_significant_digits(value: float, sig_digits: int) -> str:
    """Format number with significant digits"""
    if value == 0:
        return '0'

    # Use numpy for significant digit formatting
    return np.format_float_positional(value, precision=sig_digits, unique=False,
                                     fractional=False, trim='k')


def _format_legacy(value: Union[int, float], format_str: str) -> str:
    """Handle legacy format strings"""
    format_str = format_str.lower()

    if format_str == 'integer':
        return f"{int(value):,}"
    elif format_str == 'percent':
        return f"{value*100:.1f}%" if value < 1 else f"{value:.1f}%"
    elif format_str == 'float':
        return f"{value:.3f}".rstrip('0').rstrip('.')
    elif format_str == 'date':
        if isinstance(value, (datetime, date)):
            return value.strftime('%Y-%m-%d')
        return str(value)
    else:
        return str(value)


def format_dataframe_columns(
    df: pd.DataFrame,
    formatting: Optional[Dict[str, Dict]] = None,
    column_labels: Optional[Dict[str, str]] = None,
    dashboard_metadata: Optional[Dict] = None
) -> pd.DataFrame:
    """
    Apply formatting and labels to dataframe for display

    Args:
        df: DataFrame to format
        formatting: Dict of {field_name: format_spec}
        column_labels: Dict of {field_name: human_label}
        dashboard_metadata: Dashboard metadata for context

    Returns:
        DataFrame with formatted values and renamed columns
    """
    df = df.copy()

    # Apply formatting to columns
    if formatting:
        for field, format_spec in formatting.items():
            if field in df.columns:
                df[field] = df[field].apply(
                    lambda x: format_number(x, format_spec, field, dashboard_metadata)
                )

    # Apply column labels
    if column_labels:
        # Only rename columns that exist and have labels
        rename_map = {k: v for k, v in column_labels.items() if k in df.columns}
        df = df.rename(columns=rename_map)

    return df


def get_column_labels(
    columns: list,
    column_labels: Optional[Dict[str, str]] = None,
    auto_generate: bool = True
) -> Dict[str, str]:
    """
    Get column labels, auto-generating human-readable ones if needed

    Args:
        columns: List of column names
        column_labels: Explicit label mapping
        auto_generate: Whether to auto-generate labels from column names

    Returns:
        Dict mapping column names to labels
    """
    labels = {}

    for col in columns:
        if column_labels and col in column_labels:
            labels[col] = column_labels[col]
        elif auto_generate:
            # Auto-generate from snake_case/camelCase
            labels[col] = _auto_label(col)
        else:
            labels[col] = col

    return labels


def _auto_label(field_name: str) -> str:
    """Auto-generate human-readable label from field name"""
    # Handle snake_case
    if '_' in field_name:
        parts = field_name.split('_')
        return ' '.join(word.capitalize() for word in parts)

    # Handle camelCase
    import re
    # Insert space before capitals
    spaced = re.sub(r'([a-z])([A-Z])', r'\1 \2', field_name)
    return spaced.title()


def format_axis_label(
    field_name: str,
    column_labels: Optional[Dict[str, str]] = None,
    format_spec: Optional[Dict] = None
) -> str:
    """
    Format axis label for charts

    Args:
        field_name: Field name
        column_labels: Label mapping
        format_spec: Format specification (for units)

    Returns:
        Formatted label
    """
    # Get base label
    if column_labels and field_name in column_labels:
        label = column_labels[field_name]
    else:
        label = _auto_label(field_name)

    # Add units from format spec
    if format_spec:
        format_type = format_spec.get('type')
        currency_code = format_spec.get('currency_code')

        if format_type == 'percent':
            label += ' (%)'
        elif format_type == 'currency' and currency_code:
            label += f' ({currency_code})'

    return label
