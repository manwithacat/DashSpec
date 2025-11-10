#!/usr/bin/env python3
"""
Main ETL Pipeline Runner

This script orchestrates the ETL pipeline for downloading and processing
Kaggle datasets defined in config/datasets.yaml
"""

import argparse
import logging
import sys
from pathlib import Path

from etl.config import load_config
from etl.pipeline import ETLPipeline


def setup_logging(log_level: str = "INFO") -> None:
    """Configure logging"""
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    # Create formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)

    # File handler
    file_handler = logging.FileHandler(log_dir / "etl_pipeline.log")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="ETL Pipeline for Kaggle Datasets",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process all datasets
  python run_etl.py

  # Process specific datasets
  python run_etl.py --datasets credit_card_fraud us_accidents

  # Force reprocess existing datasets
  python run_etl.py --no-skip-existing

  # Verbose output
  python run_etl.py --verbose
        """,
    )

    parser.add_argument(
        "--datasets", nargs="+", help="Specific dataset names to process (default: all)"
    )

    parser.add_argument(
        "--no-skip-existing",
        action="store_true",
        help="Reprocess datasets even if they already exist",
    )

    parser.add_argument(
        "--config",
        default="config/datasets.yaml",
        help="Path to configuration file (default: config/datasets.yaml)",
    )

    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")

    args = parser.parse_args()

    # Setup logging
    log_level = "DEBUG" if args.verbose else "INFO"
    setup_logging(log_level)

    logger = logging.getLogger(__name__)

    try:
        # Load configuration
        logger.info("Loading configuration...")
        config = load_config(args.config)

        logger.info(f"Found {len(config.datasets)} datasets in configuration")

        # Create and run pipeline
        pipeline = ETLPipeline(config)

        results = pipeline.run(dataset_names=args.datasets, skip_existing=not args.no_skip_existing)

        # Print summary
        summary = pipeline.get_summary()

        if summary["failed"] > 0:
            logger.error("Pipeline completed with errors")
            sys.exit(1)
        else:
            logger.info("Pipeline completed successfully")
            sys.exit(0)

    except KeyboardInterrupt:
        logger.warning("\nPipeline interrupted by user")
        sys.exit(130)

    except Exception as e:
        logger.error(f"Pipeline failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
