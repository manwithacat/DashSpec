"""
Data loading module - handles saving to Parquet format
"""

import json
import logging
from pathlib import Path
from typing import Dict, Optional

import pandas as pd

logger = logging.getLogger(__name__)


class ParquetLoader:
    """Handles loading transformed data to Parquet files"""

    def __init__(self, processed_data_dir: Path, metadata_dir: Path, compression: str = "snappy"):
        self.processed_data_dir = processed_data_dir
        self.metadata_dir = metadata_dir
        self.compression = compression

    def save_to_parquet(
        self, df: pd.DataFrame, dataset_name: str, partition_cols: Optional[list] = None
    ) -> Path:
        """
        Save dataframe to Parquet format

        Args:
            df: Dataframe to save
            dataset_name: Name of the dataset
            partition_cols: Optional columns to partition by

        Returns:
            Path to the saved Parquet file
        """
        output_path = self.processed_data_dir / f"{dataset_name}.parquet"

        logger.info(f"Saving {dataset_name} to Parquet format")
        logger.info(f"Output path: {output_path}")
        logger.info(f"Compression: {self.compression}")

        try:
            if partition_cols and all(col in df.columns for col in partition_cols):
                # Save with partitioning
                output_dir = self.processed_data_dir / dataset_name
                df.to_parquet(
                    output_dir,
                    engine="pyarrow",
                    compression=self.compression,
                    partition_cols=partition_cols,
                    index=False,
                )
                logger.info(f"Saved partitioned Parquet to {output_dir}")
                return output_dir
            else:
                # Save as single file
                df.to_parquet(
                    output_path, engine="pyarrow", compression=self.compression, index=False
                )
                logger.info(f"Saved Parquet file: {output_path}")
                return output_path

        except Exception as e:
            logger.error(f"Failed to save Parquet file for {dataset_name}: {e}")
            raise

    def save_metadata(
        self, metadata: Dict, dataset_name: str, profile: Optional[Dict] = None
    ) -> Path:
        """
        Save dataset metadata to JSON

        Args:
            metadata: Metadata dictionary
            dataset_name: Name of the dataset
            profile: Optional data profile

        Returns:
            Path to the saved metadata file
        """
        metadata_path = self.metadata_dir / f"{dataset_name}_metadata.json"

        # Combine metadata with profile if available
        full_metadata = metadata.copy()
        if profile:
            full_metadata["data_profile"] = profile

        try:
            with open(metadata_path, "w") as f:
                json.dump(full_metadata, f, indent=2, default=str)

            logger.info(f"Saved metadata to {metadata_path}")
            return metadata_path

        except Exception as e:
            logger.error(f"Failed to save metadata for {dataset_name}: {e}")
            raise

    def load_parquet(self, dataset_name: str) -> pd.DataFrame:
        """
        Load a Parquet file

        Args:
            dataset_name: Name of the dataset to load

        Returns:
            Loaded dataframe
        """
        parquet_path = self.processed_data_dir / f"{dataset_name}.parquet"

        if not parquet_path.exists():
            # Try partitioned format
            parquet_dir = self.processed_data_dir / dataset_name
            if parquet_dir.exists():
                parquet_path = parquet_dir

        logger.info(f"Loading Parquet file: {parquet_path}")

        try:
            df = pd.read_parquet(parquet_path, engine="pyarrow")
            logger.info(f"Loaded {len(df)} rows from {dataset_name}")
            return df

        except Exception as e:
            logger.error(f"Failed to load Parquet file for {dataset_name}: {e}")
            raise

    def load_metadata(self, dataset_name: str) -> Dict:
        """
        Load dataset metadata

        Args:
            dataset_name: Name of the dataset

        Returns:
            Metadata dictionary
        """
        metadata_path = self.metadata_dir / f"{dataset_name}_metadata.json"

        try:
            with open(metadata_path, "r") as f:
                metadata = json.load(f)

            logger.info(f"Loaded metadata for {dataset_name}")
            return metadata

        except Exception as e:
            logger.error(f"Failed to load metadata for {dataset_name}: {e}")
            raise

    def get_parquet_info(self, dataset_name: str) -> Dict:
        """
        Get information about a Parquet file

        Args:
            dataset_name: Name of the dataset

        Returns:
            Dictionary with Parquet file information
        """
        parquet_path = self.processed_data_dir / f"{dataset_name}.parquet"

        if not parquet_path.exists():
            parquet_dir = self.processed_data_dir / dataset_name
            if parquet_dir.exists():
                parquet_path = parquet_dir

        try:
            df = pd.read_parquet(parquet_path, engine="pyarrow")

            info = {
                "path": str(parquet_path),
                "exists": parquet_path.exists(),
                "rows": len(df),
                "columns": len(df.columns),
                "size_mb": (
                    parquet_path.stat().st_size / 1024**2 if parquet_path.is_file() else None
                ),
                "column_names": list(df.columns),
                "dtypes": df.dtypes.astype(str).to_dict(),
            }

            return info

        except Exception as e:
            logger.error(f"Failed to get Parquet info for {dataset_name}: {e}")
            return {"path": str(parquet_path), "exists": False, "error": str(e)}
