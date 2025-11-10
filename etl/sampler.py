"""
Data sampling for deployment and testing
"""

import logging
from typing import Optional

import pandas as pd

from .config import SamplingConfig

logger = logging.getLogger(__name__)


class DataSampler:
    """Handles intelligent data sampling for deployment"""

    @staticmethod
    def sample(
        df: pd.DataFrame, config: Optional[SamplingConfig] = None
    ) -> pd.DataFrame:
        """
        Sample a dataset according to configuration

        Args:
            df: DataFrame to sample
            config: Sampling configuration

        Returns:
            Sampled DataFrame (or original if no sampling configured)
        """
        if not config or not config.enabled:
            return df

        original_rows = len(df)

        # If already small enough, return as is
        if config.max_rows and original_rows <= config.max_rows:
            logger.info(
                f"Dataset has {original_rows:,} rows, already <= {config.max_rows:,}, keeping all"
            )
            return df

        # Apply sampling strategy
        if config.strategy == "stratified" and config.stratify_column:
            sampled_df = DataSampler._stratified_sample(
                df, config.max_rows, config.stratify_column
            )
        elif config.strategy == "time_series" and config.time_column:
            sampled_df = DataSampler._time_series_sample(
                df, config.max_rows, config.time_column
            )
        else:  # random
            sampled_df = DataSampler._random_sample(df, config.max_rows)

        reduction_pct = (1 - len(sampled_df) / original_rows) * 100
        logger.info(
            f"Sampled {len(sampled_df):,} rows from {original_rows:,} "
            f"({reduction_pct:.1f}% reduction) using {config.strategy} strategy"
        )

        return sampled_df

    @staticmethod
    def _random_sample(df: pd.DataFrame, n_samples: int) -> pd.DataFrame:
        """Simple random sampling"""
        return df.sample(n=min(n_samples, len(df)), random_state=42)

    @staticmethod
    def _stratified_sample(
        df: pd.DataFrame, n_samples: int, stratify_column: str
    ) -> pd.DataFrame:
        """Stratified sampling preserving class distributions"""
        if stratify_column not in df.columns:
            logger.warning(
                f"Stratify column '{stratify_column}' not found, falling back to random sampling"
            )
            return DataSampler._random_sample(df, n_samples)

        # Calculate samples per stratum
        sampled = df.groupby(stratify_column, group_keys=False).apply(
            lambda x: x.sample(
                n=min(len(x), max(1, int(n_samples * len(x) / len(df)))),
                random_state=42,
            )
        )

        # Ensure we don't exceed max_samples
        if len(sampled) > n_samples:
            sampled = sampled.sample(n=n_samples, random_state=42)

        return sampled

    @staticmethod
    def _time_series_sample(
        df: pd.DataFrame, n_samples: int, time_column: str
    ) -> pd.DataFrame:
        """Time series sampling preserving temporal patterns"""
        if time_column not in df.columns:
            logger.warning(
                f"Time column '{time_column}' not found, falling back to random sampling"
            )
            return DataSampler._random_sample(df, n_samples)

        # Sort by time
        df_sorted = df.sort_values(time_column)

        # Take every Nth row to maintain temporal coverage
        step = max(1, len(df_sorted) // n_samples)
        sampled = df_sorted.iloc[::step].head(n_samples)

        return sampled
