"""
Main ETL Pipeline orchestration
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd
from tqdm import tqdm

from .config import DatasetConfig, ETLConfig, ensure_directories
from .extractor import KaggleExtractor
from .loader import ParquetLoader
from .sampler import DataSampler
from .transformer import DataTransformer

logger = logging.getLogger(__name__)


class ETLPipeline:
    """Main ETL Pipeline orchestrator"""

    def __init__(self, config: ETLConfig):
        self.config = config
        ensure_directories(config)

        # Initialize components
        self.extractor = KaggleExtractor(config.raw_data_dir)
        self.transformer = DataTransformer(chunk_size=config.chunk_size)
        self.loader = ParquetLoader(
            config.processed_data_dir, config.metadata_dir, config.compression
        )

        self.results = []

    def process_dataset(self, dataset_config: DatasetConfig) -> Dict:
        """
        Process a single dataset through the ETL pipeline

        Args:
            dataset_config: Configuration for the dataset

        Returns:
            Dictionary with processing results
        """
        start_time = datetime.now()
        result = {
            "dataset_name": dataset_config.name,
            "kaggle_id": dataset_config.kaggle_id,
            "status": "pending",
            "start_time": start_time.isoformat(),
        }

        try:
            # EXTRACT
            logger.info(f"\n{'='*60}")
            logger.info(f"PROCESSING DATASET: {dataset_config.name}")
            logger.info(f"{'='*60}\n")

            logger.info("Step 1/4: Extracting data from Kaggle...")
            dataset_dir = self.extractor.download_dataset(dataset_config)
            metadata = self.extractor.extract_metadata(dataset_config)

            # Get CSV files
            csv_files = self.extractor.get_dataset_files(dataset_dir)

            if not csv_files:
                raise ValueError(f"No CSV files found in {dataset_dir}")

            result["csv_files"] = [f.name for f in csv_files]

            # Process each CSV file
            for csv_file in csv_files:
                logger.info(f"\nProcessing file: {csv_file.name}")

                # TRANSFORM
                logger.info("Step 2/4: Transforming data...")
                df = pd.read_csv(csv_file)
                df_transformed = self.transformer.transform_dataframe(
                    df, dataset_config.name, metadata
                )

                # Generate data profile
                logger.info("Step 3/4: Generating data profile...")
                profile = self.transformer.get_data_profile(df_transformed)

                # SAMPLE (if configured)
                if dataset_config.sampling:
                    logger.info("Step 3.5/4: Applying deployment sampling...")
                    df_transformed = DataSampler.sample(df_transformed, dataset_config.sampling)

                # LOAD
                logger.info("Step 4/4: Loading to Parquet format...")

                # Determine output name
                if len(csv_files) == 1:
                    output_name = dataset_config.name
                else:
                    # Multiple files - use filename in output
                    output_name = f"{dataset_config.name}_{csv_file.stem}"

                parquet_path = self.loader.save_to_parquet(df_transformed, output_name)

                # Save metadata
                metadata_path = self.loader.save_metadata(metadata, output_name, profile)

                result["status"] = "success"
                result["parquet_path"] = str(parquet_path)
                result["metadata_path"] = str(metadata_path)
                result["rows"] = len(df_transformed)
                result["columns"] = len(df_transformed.columns)

            end_time = datetime.now()
            result["end_time"] = end_time.isoformat()
            result["duration_seconds"] = (end_time - start_time).total_seconds()

            logger.info(f"\n✓ Successfully processed {dataset_config.name}")
            logger.info(f"Duration: {result['duration_seconds']:.2f} seconds\n")

        except Exception as e:
            result["status"] = "failed"
            result["error"] = str(e)
            logger.error(f"\n✗ Failed to process {dataset_config.name}: {e}\n")

        return result

    def run(
        self, dataset_names: Optional[List[str]] = None, skip_existing: bool = True
    ) -> List[Dict]:
        """
        Run the ETL pipeline for all or selected datasets

        Args:
            dataset_names: Optional list of dataset names to process
            skip_existing: Skip datasets that already have Parquet files

        Returns:
            List of results for each dataset
        """
        datasets_to_process = self.config.datasets

        # Filter by dataset names if provided
        if dataset_names:
            datasets_to_process = [ds for ds in datasets_to_process if ds.name in dataset_names]

        # Filter enabled datasets
        datasets_to_process = [ds for ds in datasets_to_process if ds.enabled]

        if not datasets_to_process:
            logger.warning("No datasets to process")
            return []

        logger.info(f"Starting ETL pipeline for {len(datasets_to_process)} datasets")

        # Process each dataset
        for dataset_config in tqdm(datasets_to_process, desc="Processing datasets"):
            # Check if already processed
            if skip_existing:
                parquet_path = self.config.processed_data_dir / f"{dataset_config.name}.parquet"
                if parquet_path.exists():
                    logger.info(f"Skipping {dataset_config.name} - already exists")
                    self.results.append(
                        {
                            "dataset_name": dataset_config.name,
                            "status": "skipped",
                            "reason": "already_exists",
                        }
                    )
                    continue

            result = self.process_dataset(dataset_config)
            self.results.append(result)

        # Summary
        self._print_summary()

        return self.results

    def _print_summary(self) -> None:
        """Print processing summary"""
        logger.info(f"\n{'='*60}")
        logger.info("PIPELINE SUMMARY")
        logger.info(f"{'='*60}\n")

        success_count = sum(1 for r in self.results if r["status"] == "success")
        failed_count = sum(1 for r in self.results if r["status"] == "failed")
        skipped_count = sum(1 for r in self.results if r["status"] == "skipped")

        logger.info(f"Total datasets: {len(self.results)}")
        logger.info(f"Successful: {success_count}")
        logger.info(f"Failed: {failed_count}")
        logger.info(f"Skipped: {skipped_count}")

        if failed_count > 0:
            logger.info("\nFailed datasets:")
            for result in self.results:
                if result["status"] == "failed":
                    logger.info(
                        f"  - {result['dataset_name']}: {result.get('error', 'Unknown error')}"
                    )

        logger.info("")

    def get_summary(self) -> Dict:
        """Get processing summary as dictionary"""
        return {
            "total": len(self.results),
            "successful": sum(1 for r in self.results if r["status"] == "success"),
            "failed": sum(1 for r in self.results if r["status"] == "failed"),
            "skipped": sum(1 for r in self.results if r["status"] == "skipped"),
            "results": self.results,
        }
