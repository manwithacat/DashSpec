"""
Data transformation module - handles data cleaning and preprocessing
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd

logger = logging.getLogger(__name__)


class DataTransformer:
    """Handles transformation and cleaning of datasets"""

    def __init__(self, chunk_size: int = 10000):
        self.chunk_size = chunk_size

    def transform_dataframe(
        self, df: pd.DataFrame, dataset_name: str, metadata: Optional[Dict] = None
    ) -> pd.DataFrame:
        """
        Apply transformations to a dataframe

        Args:
            df: Input dataframe
            dataset_name: Name of the dataset
            metadata: Optional metadata dictionary

        Returns:
            Transformed dataframe
        """
        logger.info(f"Transforming dataset: {dataset_name}")
        logger.info(f"Original shape: {df.shape}")

        # Create a copy to avoid modifying original
        df_transformed = df.copy()

        # 1. Standardize column names
        df_transformed = self._standardize_columns(df_transformed)

        # 2. Handle missing values
        df_transformed = self._handle_missing_values(df_transformed, dataset_name)

        # 3. Infer and optimize data types
        df_transformed = self._optimize_dtypes(df_transformed)

        # 4. Remove duplicate rows
        df_transformed = self._remove_duplicates(df_transformed)

        # 5. Add metadata columns
        df_transformed = self._add_metadata_columns(df_transformed, dataset_name, metadata)

        logger.info(f"Transformed shape: {df_transformed.shape}")
        logger.info(
            f"Memory usage: {df_transformed.memory_usage(deep=True).sum() / 1024**2:.2f} MB"
        )

        return df_transformed

    def _standardize_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Standardize column names to lowercase with underscores"""
        df.columns = (
            df.columns.str.strip()
            .str.lower()
            .str.replace(" ", "_")
            .str.replace("[^a-z0-9_]", "", regex=True)
        )
        logger.debug(f"Standardized column names: {list(df.columns)}")
        return df

    def _handle_missing_values(self, df: pd.DataFrame, dataset_name: str) -> pd.DataFrame:
        """Handle missing values with dataset-aware strategies"""
        missing_counts = df.isnull().sum()
        missing_pct = (missing_counts / len(df)) * 100

        if missing_counts.sum() > 0:
            logger.info(f"Missing values found:")
            for col, pct in missing_pct[missing_pct > 0].items():
                logger.info(f"  {col}: {pct:.2f}%")

            # Drop columns with >50% missing values
            cols_to_drop = missing_pct[missing_pct > 50].index.tolist()
            if cols_to_drop:
                logger.warning(f"Dropping columns with >50% missing: {cols_to_drop}")
                df = df.drop(columns=cols_to_drop)

        return df

    def _optimize_dtypes(self, df: pd.DataFrame) -> pd.DataFrame:
        """Optimize data types to reduce memory usage"""
        for col in df.columns:
            col_type = df[col].dtype

            if col_type == "object":
                # Try to convert to numeric
                try:
                    numeric_col = pd.to_numeric(df[col], errors='raise')
                    df[col] = numeric_col
                    continue
                except (ValueError, TypeError):
                    pass

                # Try to convert to datetime
                try:
                    datetime_col = pd.to_datetime(df[col], errors='raise', format='mixed')
                    df[col] = datetime_col
                    continue
                except (ValueError, TypeError):
                    pass

                # Check if it should be categorical
                num_unique = df[col].nunique()
                num_total = len(df[col])
                if num_unique / num_total < 0.5:  # Less than 50% unique values
                    df[col] = df[col].astype("category")

            elif col_type in ["int64", "int32"]:
                # Downcast integers
                downcast_col = pd.to_numeric(df[col], downcast="integer")
                df[col] = downcast_col

            elif col_type in ["float64", "float32"]:
                # Downcast floats
                downcast_col = pd.to_numeric(df[col], downcast="float")
                df[col] = downcast_col

        return df

    def _remove_duplicates(self, df: pd.DataFrame) -> pd.DataFrame:
        """Remove duplicate rows"""
        original_len = len(df)
        df = df.drop_duplicates()
        duplicates_removed = original_len - len(df)

        if duplicates_removed > 0:
            logger.info(f"Removed {duplicates_removed} duplicate rows")

        return df

    def _add_metadata_columns(
        self, df: pd.DataFrame, dataset_name: str, metadata: Optional[Dict]
    ) -> pd.DataFrame:
        """Add metadata columns for tracking"""
        df["_dataset_name"] = dataset_name

        if metadata:
            df["_dataset_category"] = metadata.get("category", "unknown")

        return df

    def get_data_profile(self, df: pd.DataFrame) -> Dict:
        """
        Generate a data profile summary

        Args:
            df: Input dataframe

        Returns:
            Dictionary containing profile information
        """
        profile = {
            "shape": {"rows": len(df), "columns": len(df.columns)},
            "memory_usage_mb": df.memory_usage(deep=True).sum() / 1024**2,
            "columns": {},
            "missing_values": df.isnull().sum().to_dict(),
            "dtypes": df.dtypes.astype(str).to_dict(),
        }

        # Column-level statistics
        for col in df.columns:
            col_profile = {
                "dtype": str(df[col].dtype),
                "missing_count": int(df[col].isnull().sum()),
                "missing_pct": float((df[col].isnull().sum() / len(df)) * 100),
                "unique_count": int(df[col].nunique()),
            }

            # Add numeric statistics if applicable
            if pd.api.types.is_numeric_dtype(df[col]):
                col_profile.update(
                    {
                        "mean": float(df[col].mean()) if not df[col].isnull().all() else None,
                        "std": float(df[col].std()) if not df[col].isnull().all() else None,
                        "min": float(df[col].min()) if not df[col].isnull().all() else None,
                        "max": float(df[col].max()) if not df[col].isnull().all() else None,
                    }
                )

            profile["columns"][col] = col_profile

        return profile
