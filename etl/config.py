"""
Configuration management for the ETL pipeline
"""

from pathlib import Path
from typing import List, Optional

import yaml
from pydantic import BaseModel, Field


class SamplingConfig(BaseModel):
    """Configuration for deployment sampling"""

    enabled: bool = False
    max_rows: Optional[int] = None
    strategy: str = "random"  # random, stratified, time_series
    stratify_column: Optional[str] = None
    time_column: Optional[str] = None


class DatasetConfig(BaseModel):
    """Configuration for a single dataset"""

    name: str
    kaggle_id: str
    description: str
    project_category: str
    url: str
    enabled: bool = True
    sampling: Optional[SamplingConfig] = None


class ETLConfig(BaseModel):
    """Main ETL pipeline configuration"""

    datasets: List[DatasetConfig]

    # Directory paths
    raw_data_dir: Path = Field(default_factory=lambda: Path("data/raw"))
    processed_data_dir: Path = Field(default_factory=lambda: Path("data/processed"))
    metadata_dir: Path = Field(default_factory=lambda: Path("data/metadata"))
    logs_dir: Path = Field(default_factory=lambda: Path("logs"))

    # Processing options
    max_workers: int = 2
    chunk_size: int = 10000
    compression: str = "snappy"


def load_config(config_path: str = "config/datasets.yaml") -> ETLConfig:
    """Load configuration from YAML file"""
    with open(config_path, "r") as f:
        config_data = yaml.safe_load(f)

    return ETLConfig(**config_data)


def ensure_directories(config: ETLConfig) -> None:
    """Ensure all required directories exist"""
    for dir_path in [
        config.raw_data_dir,
        config.processed_data_dir,
        config.metadata_dir,
        config.logs_dir,
    ]:
        dir_path.mkdir(parents=True, exist_ok=True)
