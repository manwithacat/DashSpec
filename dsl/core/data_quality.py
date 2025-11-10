"""
DashSpec Data Quality Processor

Handles missing values, outliers, duplicates, validation, and transformations
according to declarative rules in dashboard specifications.
"""

from typing import Dict, List, Tuple, Any, Optional
import pandas as pd
import numpy as np
from dataclasses import dataclass, field
import logging

logger = logging.getLogger(__name__)


@dataclass
class DataQualityReport:
    """Track data quality processing results"""
    total_rows_initial: int = 0
    total_rows_final: int = 0
    rows_dropped: int = 0
    rows_modified: int = 0
    missing_values_filled: int = 0
    outliers_detected: int = 0
    outliers_capped: int = 0
    duplicates_found: int = 0
    duplicates_removed: int = 0
    validation_failures: int = 0
    transformations_applied: int = 0
    details: List[Dict[str, Any]] = field(default_factory=list)

    def add_detail(self, operation: str, field: str, count: int, description: str):
        """Add a detail entry"""
        self.details.append({
            'operation': operation,
            'field': field,
            'count': count,
            'description': description
        })

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for reporting"""
        return {
            'total_rows_initial': self.total_rows_initial,
            'total_rows_final': self.total_rows_final,
            'rows_dropped': self.rows_dropped,
            'rows_modified': self.rows_modified,
            'missing_values_filled': self.missing_values_filled,
            'outliers_detected': self.outliers_detected,
            'outliers_capped': self.outliers_capped,
            'duplicates_found': self.duplicates_found,
            'duplicates_removed': self.duplicates_removed,
            'validation_failures': self.validation_failures,
            'transformations_applied': self.transformations_applied,
            'issues_detected': (
                self.missing_values_filled +
                self.outliers_detected +
                self.duplicates_found +
                self.validation_failures
            ),
            'details': self.details
        }


class DataQualityProcessor:
    """Process data quality rules declaratively"""

    def __init__(self, rules: Dict[str, Any]):
        """
        Initialize with DQ rules from dashboard spec

        Args:
            rules: data_quality section from YAML
        """
        self.rules = rules
        self.report = DataQualityReport()

    def process(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Apply all data quality rules

        Args:
            df: Input dataframe

        Returns:
            Tuple of (cleaned_df, report_dict)
        """
        df = df.copy()
        self.report.total_rows_initial = len(df)

        logger.info(f"Starting DQ processing on {len(df):,} rows")

        # Phase 1: Type coercion
        if 'coercion' in self.rules:
            df = self._apply_coercion(df)

        # Phase 2: Missing value handling
        if 'missing_values' in self.rules:
            df = self._handle_missing_values(df)

        # Phase 3: Duplicate detection/removal
        if 'duplicates' in self.rules:
            df = self._handle_duplicates(df)

        # Phase 4: Outlier detection/handling
        if 'outliers' in self.rules and self.rules['outliers'].get('enabled', True):
            df = self._handle_outliers(df)

        # Phase 5: Validation
        if 'validation' in self.rules:
            df = self._apply_validations(df)

        # Phase 6: Custom transformations
        if 'transformations' in self.rules:
            df = self._apply_transformations(df)

        self.report.total_rows_final = len(df)
        self.report.rows_dropped = self.report.total_rows_initial - self.report.total_rows_final

        logger.info(f"DQ processing complete: {len(df):,} rows remaining "
                   f"({self.report.rows_dropped:,} dropped)")

        return df, self.report.to_dict()

    def _apply_coercion(self, df: pd.DataFrame) -> pd.DataFrame:
        """Apply type coercion rules"""
        rules = self.rules['coercion'].get('rules', [])

        for rule in rules:
            fields = rule.get('fields', [])
            target_type = rule.get('target_type')
            on_error = rule.get('on_error', 'coerce')

            for field in fields:
                if field not in df.columns:
                    continue

                try:
                    if target_type == 'integer':
                        df[field] = pd.to_numeric(df[field], errors=on_error)
                        if on_error == 'coerce':
                            df[field] = df[field].fillna(0).astype('int64')
                    elif target_type == 'float':
                        df[field] = pd.to_numeric(df[field], errors=on_error)
                    elif target_type == 'datetime':
                        date_format = rule.get('format')
                        df[field] = pd.to_datetime(df[field], format=date_format, errors=on_error)
                    elif target_type == 'string':
                        df[field] = df[field].astype(str)

                    self.report.add_detail('coercion', field, len(df),
                                          f"Converted to {target_type}")
                except Exception as e:
                    logger.warning(f"Coercion failed for {field}: {e}")

        return df

    def _handle_missing_values(self, df: pd.DataFrame) -> pd.DataFrame:
        """Handle missing values according to rules"""
        rules = self.rules['missing_values'].get('rules', [])

        for rule in rules:
            fields = rule.get('fields', [])
            action = rule.get('action')

            for field in fields:
                if field not in df.columns:
                    continue

                missing_before = df[field].isna().sum()

                if action == 'drop_rows':
                    df = df.dropna(subset=[field])
                    self.report.add_detail('missing_values', field, missing_before,
                                          f"Dropped {missing_before} rows")

                elif action == 'fill_forward':
                    limit = rule.get('limit')
                    original_dtype = df[field].dtype
                    filled_series = df[field].fillna(method='ffill', limit=limit)
                    df[field] = filled_series.astype(original_dtype)
                    missing_after = df[field].isna().sum()
                    filled = missing_before - missing_after
                    self.report.missing_values_filled += filled
                    self.report.add_detail('missing_values', field, filled,
                                          f"Forward filled {filled} values")

                elif action == 'fill_backward':
                    limit = rule.get('limit')
                    original_dtype = df[field].dtype
                    filled_series = df[field].fillna(method='bfill', limit=limit)
                    df[field] = filled_series.astype(original_dtype)
                    missing_after = df[field].isna().sum()
                    filled = missing_before - missing_after
                    self.report.missing_values_filled += filled
                    self.report.add_detail('missing_values', field, filled,
                                          f"Backward filled {filled} values")

                elif action == 'fill_value':
                    value = rule.get('value', 0)
                    original_dtype = df[field].dtype
                    # Cast value to match column dtype if numeric
                    if not pd.api.types.is_object_dtype(original_dtype):
                        value = original_dtype.type(value)
                    filled_series = df[field].fillna(value)
                    df[field] = filled_series.astype(original_dtype)
                    self.report.missing_values_filled += missing_before
                    self.report.add_detail('missing_values', field, missing_before,
                                          f"Filled with {value}")

                elif action == 'interpolate':
                    original_dtype = df[field].dtype
                    interpolated = df[field].interpolate(method='linear')
                    df[field] = interpolated.astype(original_dtype)
                    missing_after = df[field].isna().sum()
                    filled = missing_before - missing_after
                    self.report.missing_values_filled += filled
                    self.report.add_detail('missing_values', field, filled,
                                          f"Interpolated {filled} values")

                elif action == 'flag':
                    # Create a flag column
                    flag_col = f"{field}_missing_flag"
                    df[flag_col] = df[field].isna().astype(int)
                    self.report.add_detail('missing_values', field, missing_before,
                                          f"Flagged {missing_before} missing values")

        return df

    def _handle_duplicates(self, df: pd.DataFrame) -> pd.DataFrame:
        """Handle duplicate rows"""
        if not self.rules['duplicates'].get('enabled', True):
            return df

        subset = self.rules['duplicates'].get('subset')
        keep = self.rules['duplicates'].get('keep', 'first')
        action = self.rules['duplicates'].get('action', 'drop')

        duplicates_mask = df.duplicated(subset=subset, keep=False)
        n_duplicates = duplicates_mask.sum()
        self.report.duplicates_found = n_duplicates

        if action == 'drop' and n_duplicates > 0:
            df = df.drop_duplicates(subset=subset, keep=keep)
            self.report.duplicates_removed = n_duplicates
            self.report.add_detail('duplicates', ','.join(subset), n_duplicates,
                                  f"Removed {n_duplicates} duplicate rows")

        elif action == 'flag' and n_duplicates > 0:
            df['_duplicate_flag'] = duplicates_mask.astype(int)
            self.report.add_detail('duplicates', ','.join(subset), n_duplicates,
                                  f"Flagged {n_duplicates} duplicate rows")

        return df

    def _handle_outliers(self, df: pd.DataFrame) -> pd.DataFrame:
        """Detect and handle outliers"""
        rules = self.rules['outliers'].get('rules', [])

        for rule in rules:
            fields = rule.get('fields', [])
            method = rule.get('method', 'iqr')
            action = rule.get('action', 'flag')

            for field in fields:
                if field not in df.columns or not pd.api.types.is_numeric_dtype(df[field]):
                    continue

                outliers_mask = self._detect_outliers(df[field], method, rule)
                n_outliers = outliers_mask.sum()
                self.report.outliers_detected += n_outliers

                if action == 'cap' and n_outliers > 0:
                    lower_bound, upper_bound = self._get_outlier_bounds(df[field], method, rule)
                    # Clip values and preserve original dtype
                    # Clip entire series first, then assign back using boolean indexing
                    clipped_series = df[field].clip(lower=lower_bound, upper=upper_bound).astype(df[field].dtype)
                    df[field] = clipped_series
                    self.report.outliers_capped += n_outliers
                    self.report.add_detail('outliers', field, n_outliers,
                                          f"Capped {n_outliers} outliers")

                elif action == 'drop' and n_outliers > 0:
                    df = df[~outliers_mask]
                    self.report.add_detail('outliers', field, n_outliers,
                                          f"Dropped {n_outliers} outlier rows")

                elif action == 'flag' and n_outliers > 0:
                    flag_col = f"{field}_outlier_flag"
                    df[flag_col] = outliers_mask.astype(int)
                    self.report.add_detail('outliers', field, n_outliers,
                                          f"Flagged {n_outliers} outliers")

        return df

    def _detect_outliers(self, series: pd.Series, method: str, rule: Dict) -> pd.Series:
        """Detect outliers using specified method"""
        series = series.dropna()

        if method == 'iqr':
            Q1 = series.quantile(0.25)
            Q3 = series.quantile(0.75)
            IQR = Q3 - Q1
            threshold = rule.get('threshold', 1.5)
            lower_bound = Q1 - threshold * IQR
            upper_bound = Q3 + threshold * IQR
            return (series < lower_bound) | (series > upper_bound)

        elif method == 'zscore':
            threshold = rule.get('threshold', 3.0)
            z_scores = np.abs((series - series.mean()) / series.std())
            return z_scores > threshold

        elif method == 'percentile':
            lower = rule.get('lower', 1.0)
            upper = rule.get('upper', 99.0)
            lower_bound = series.quantile(lower / 100)
            upper_bound = series.quantile(upper / 100)
            return (series < lower_bound) | (series > upper_bound)

        return pd.Series([False] * len(series), index=series.index)

    def _get_outlier_bounds(self, series: pd.Series, method: str, rule: Dict) -> Tuple[float, float]:
        """Get bounds for capping outliers"""
        series = series.dropna()

        if method == 'iqr':
            Q1 = series.quantile(0.25)
            Q3 = series.quantile(0.75)
            IQR = Q3 - Q1
            threshold = rule.get('threshold', 1.5)
            return Q1 - threshold * IQR, Q3 + threshold * IQR

        elif method == 'percentile':
            lower = rule.get('lower', 1.0)
            upper = rule.get('upper', 99.0)
            return series.quantile(lower / 100), series.quantile(upper / 100)

        elif method == 'zscore':
            threshold = rule.get('threshold', 3.0)
            mean = series.mean()
            std = series.std()
            return mean - threshold * std, mean + threshold * std

        return series.min(), series.max()

    def _apply_validations(self, df: pd.DataFrame) -> pd.DataFrame:
        """Apply validation rules"""
        rules = self.rules['validation'].get('rules', [])

        for rule in rules:
            field = rule.get('field')
            constraint = rule.get('constraint')
            action = rule.get('action', 'flag')

            if field not in df.columns:
                continue

            invalid_mask = self._check_validation(df, field, constraint, rule)
            n_invalid = invalid_mask.sum()
            self.report.validation_failures += n_invalid

            if action == 'drop' and n_invalid > 0:
                df = df[~invalid_mask]
                self.report.add_detail('validation', field, n_invalid,
                                      f"Dropped {n_invalid} invalid rows")

            elif action == 'flag' and n_invalid > 0:
                flag_col = f"{field}_invalid_flag"
                df[flag_col] = invalid_mask.astype(int)
                self.report.add_detail('validation', field, n_invalid,
                                      f"Flagged {n_invalid} invalid values")

            elif action == 'coerce' and n_invalid > 0:
                # Set invalid values to NaN or provided default
                default_value = rule.get('default', np.nan)
                # Ensure default value matches column dtype
                if pd.notna(default_value) and not pd.api.types.is_object_dtype(df[field].dtype):
                    default_value = df[field].dtype.type(default_value)
                df.loc[invalid_mask, field] = default_value
                self.report.add_detail('validation', field, n_invalid,
                                      f"Coerced {n_invalid} invalid values")

        return df

    def _check_validation(self, df: pd.DataFrame, field: str,
                         constraint: str, rule: Dict) -> pd.Series:
        """Check validation constraint"""
        if constraint == 'range':
            min_val = rule.get('min', -np.inf)
            max_val = rule.get('max', np.inf)
            return (df[field] < min_val) | (df[field] > max_val)

        elif constraint == 'in_set':
            values = rule.get('values', [])
            return ~df[field].isin(values)

        elif constraint == 'not_null':
            return df[field].isna()

        elif constraint == 'unique':
            return df[field].duplicated(keep=False)

        return pd.Series([False] * len(df), index=df.index)

    def _apply_transformations(self, df: pd.DataFrame) -> pd.DataFrame:
        """Apply custom transformations"""
        transformations = self.rules['transformations']

        for transform in transformations:
            name = transform.get('name', 'unnamed')
            transform_type = transform.get('type')

            logger.info(f"Applying transformation: {name}")

            if transform_type == 'custom_filter':
                df = self._apply_custom_filter(df, transform)
            elif transform_type == 'custom_compute':
                df = self._apply_custom_compute(df, transform)

            self.report.transformations_applied += 1

        return df

    def _apply_custom_filter(self, df: pd.DataFrame, transform: Dict) -> pd.DataFrame:
        """Apply custom filter transformation"""
        operation = transform.get('operation')

        if operation == 'group_rank':
            group_by = transform.get('group_by', [])
            order_by = transform.get('order_by')
            keep_ranks = transform.get('keep_ranks', [1, -1])

            # Add rank column
            df['_rank'] = df.groupby(group_by)[order_by].rank(method='first')

            # Filter based on ranks
            if len(keep_ranks) == 2:
                start_rank, end_rank = keep_ranks
                if end_rank == -1:
                    df = df[df['_rank'] >= start_rank]
                else:
                    df = df[(df['_rank'] >= start_rank) & (df['_rank'] <= end_rank)]

            df = df.drop(columns=['_rank'])

        return df

    def _apply_custom_compute(self, df: pd.DataFrame, transform: Dict) -> pd.DataFrame:
        """Apply custom computation"""
        field = transform.get('field')
        condition = transform.get('condition')

        # Evaluate condition if provided
        if condition:
            mask = eval(f"df['{field}'].isnull()")  # Simplified - need safer eval
        else:
            mask = pd.Series([True] * len(df), index=df.index)

        # Apply formula (simplified - would need expression parser)
        # For now, just document the approach
        logger.info(f"Custom compute would apply formula to {field}")

        return df
