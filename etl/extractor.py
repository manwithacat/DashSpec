"""
Data extraction module - handles downloading from Kaggle API
"""

import json
import logging
import subprocess
import zipfile
from pathlib import Path
from typing import Dict, List, Optional

from kaggle.api.kaggle_api_extended import KaggleApi

from .config import DatasetConfig

logger = logging.getLogger(__name__)


class KaggleExtractor:
    """Handles extraction of datasets from Kaggle"""

    def __init__(self, raw_data_dir: Path):
        self.raw_data_dir = raw_data_dir
        self.api = None
        self._authenticate()

    def _authenticate(self) -> None:
        """Authenticate with Kaggle API"""
        try:
            self.api = KaggleApi()
            self.api.authenticate()
            logger.info("Successfully authenticated with Kaggle API")
        except Exception as e:
            logger.error(f"Failed to authenticate with Kaggle API: {e}")
            raise

    def download_dataset(self, dataset_config: DatasetConfig) -> Path:
        """
        Download a dataset from Kaggle

        Args:
            dataset_config: Configuration for the dataset to download

        Returns:
            Path to the directory containing the downloaded files
        """
        dataset_dir = self.raw_data_dir / dataset_config.name
        dataset_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"Downloading dataset: {dataset_config.kaggle_id}")

        try:
            # Download dataset
            self.api.dataset_download_files(
                dataset_config.kaggle_id, path=dataset_dir, unzip=True, quiet=False
            )

            logger.info(f"Successfully downloaded {dataset_config.name} to {dataset_dir}")
            return dataset_dir

        except Exception as e:
            logger.error(f"Failed to download dataset {dataset_config.name}: {e}")
            raise

    def extract_metadata(self, dataset_config: DatasetConfig) -> Dict:
        """
        Extract metadata from Kaggle dataset

        Args:
            dataset_config: Configuration for the dataset

        Returns:
            Dictionary containing dataset metadata
        """
        try:
            # Get dataset metadata
            metadata = self.api.dataset_metadata(
                dataset_config.kaggle_id, self.raw_data_dir / dataset_config.name
            )

            # Get additional dataset information
            dataset_info = self.api.dataset_list_files(dataset_config.kaggle_id).files

            metadata_dict = {
                "name": dataset_config.name,
                "kaggle_id": dataset_config.kaggle_id,
                "description": dataset_config.description,
                "category": dataset_config.project_category,
                "url": dataset_config.url,
                "files": [
                    {
                        "name": f.name,
                        "size": f.size,
                        "creation_date": (
                            str(f.creationDate) if hasattr(f, "creationDate") else None
                        ),
                    }
                    for f in dataset_info
                ],
            }

            logger.info(f"Extracted metadata for {dataset_config.name}")
            return metadata_dict

        except Exception as e:
            logger.warning(f"Could not extract full metadata for {dataset_config.name}: {e}")
            # Return minimal metadata
            return {
                "name": dataset_config.name,
                "kaggle_id": dataset_config.kaggle_id,
                "description": dataset_config.description,
                "category": dataset_config.project_category,
                "url": dataset_config.url,
                "error": str(e),
            }

    def get_dataset_files(self, dataset_dir: Path) -> List[Path]:
        """
        Get all CSV files in the dataset directory

        Args:
            dataset_dir: Directory containing the dataset

        Returns:
            List of paths to CSV files
        """
        csv_files = list(dataset_dir.glob("*.csv"))
        if not csv_files:
            logger.warning(f"No CSV files found in {dataset_dir}")
        return csv_files
