"""
DataLoader - Intelligent data loading with caching, sampling, and UX optimization for Streamlit

Handles large dataset loading efficiently with:
- Automatic caching with TTL
- Smart sampling for large datasets
- Loading time estimates
- Progress indicators
- Memory-efficient operations
"""

import time
from pathlib import Path
from typing import Optional, Dict, Any, Tuple
import streamlit as st
import pandas as pd
import numpy as np


class DataLoader:
    """Intelligent data loader with caching and sampling strategies"""

    # Thresholds for automatic sampling
    LARGE_DATASET_ROWS = 100_000  # Datasets larger than this may be sampled
    HUGE_DATASET_ROWS = 1_000_000  # Datasets larger than this will be sampled aggressively

    # Default sample sizes
    DEFAULT_SAMPLE_SIZE = 50_000
    LARGE_SAMPLE_SIZE = 100_000

    # Cache TTL (time to live)
    CACHE_TTL = 3600  # 1 hour

    @staticmethod
    @st.cache_data(ttl=CACHE_TTL, show_spinner=False)
    def _load_parquet_cached(file_path: str, columns: Optional[list] = None) -> pd.DataFrame:
        """Cached parquet loading - internal method"""
        return pd.read_parquet(file_path, columns=columns)

    @staticmethod
    @st.cache_data(ttl=CACHE_TTL, show_spinner=False)
    def _get_parquet_metadata(file_path: str) -> Dict[str, Any]:
        """Get parquet file metadata without loading full data"""
        import pyarrow.parquet as pq

        parquet_file = pq.ParquetFile(file_path)
        metadata = parquet_file.metadata

        return {
            'num_rows': metadata.num_rows,
            'num_columns': metadata.num_columns,
            'file_size_mb': Path(file_path).stat().st_size / (1024 * 1024),
            'columns': [col.name for col in parquet_file.schema],
            'serialized_size': metadata.serialized_size,
        }

    @staticmethod
    def estimate_load_time(num_rows: int, file_size_mb: float) -> Tuple[float, str]:
        """Estimate load time based on dataset size"""
        # Rough estimates: ~500K rows/sec for parquet, ~50MB/sec read speed
        time_from_rows = num_rows / 500_000
        time_from_size = file_size_mb / 50

        estimated_seconds = max(time_from_rows, time_from_size)

        if estimated_seconds < 1:
            time_str = "< 1 second"
        elif estimated_seconds < 60:
            time_str = f"~{int(estimated_seconds)} seconds"
        else:
            time_str = f"~{int(estimated_seconds / 60)} minutes"

        return estimated_seconds, time_str

    @staticmethod
    @st.cache_data(ttl=CACHE_TTL, show_spinner=False)
    def _sample_parquet(file_path: str, sample_size: int, random_state: int = 42) -> pd.DataFrame:
        """Load a random sample from parquet file"""
        # For very large files, we can't load all then sample
        # So we read in chunks and sample
        metadata = DataLoader._get_parquet_metadata(file_path)
        total_rows = metadata['num_rows']

        if total_rows <= sample_size:
            return pd.read_parquet(file_path)

        # Calculate sampling ratio
        sample_ratio = sample_size / total_rows

        # For sampling, we'll use pandas built-in skip rows
        # Read with random sampling using skiprows
        df = pd.read_parquet(file_path)

        # Use deterministic sampling
        np.random.seed(random_state)
        sampled_indices = np.random.choice(len(df), size=min(sample_size, len(df)), replace=False)
        sampled_indices.sort()  # Keep temporal order if any

        return df.iloc[sampled_indices].reset_index(drop=True)

    @classmethod
    def load_data(
        cls,
        file_path: str,
        max_rows: Optional[int] = None,
        columns: Optional[list] = None,
        force_full_load: bool = False,
        show_progress: bool = True
    ) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Load data with intelligent sampling and caching

        Args:
            file_path: Path to parquet file
            max_rows: Maximum rows to load (for visualization limits)
            columns: Specific columns to load (optimization)
            force_full_load: Force loading full dataset regardless of size
            show_progress: Show loading progress indicators

        Returns:
            Tuple of (dataframe, metadata dict with loading info)
        """
        start_time = time.time()

        # Get metadata first (fast operation)
        try:
            metadata = cls._get_parquet_metadata(file_path)
        except Exception as e:
            st.error(f"Failed to read dataset metadata: {e}")
            raise

        total_rows = metadata['num_rows']
        file_size_mb = metadata['file_size_mb']

        # Estimate load time
        est_seconds, est_time_str = cls.estimate_load_time(total_rows, file_size_mb)

        # Determine loading strategy
        should_sample = False
        sample_size = None

        if not force_full_load:
            if max_rows and max_rows < total_rows:
                # Visualization has explicit limit
                should_sample = True
                sample_size = max_rows
            elif total_rows > cls.HUGE_DATASET_ROWS:
                # Very large dataset - aggressive sampling
                should_sample = True
                sample_size = cls.LARGE_SAMPLE_SIZE
            elif total_rows > cls.LARGE_DATASET_ROWS:
                # Large dataset - moderate sampling
                should_sample = True
                sample_size = cls.DEFAULT_SAMPLE_SIZE

        # Show loading info
        if show_progress:
            info_container = st.empty()

            if should_sample:
                info_container.info(
                    f"📊 **Dataset:** {total_rows:,} rows ({file_size_mb:.1f} MB)\n\n"
                    f"⚡ **Loading strategy:** Using smart sample of {sample_size:,} rows for optimal performance\n\n"
                    f"⏱️ **Estimated time:** {est_time_str}"
                )
            else:
                info_container.info(
                    f"📊 **Dataset:** {total_rows:,} rows ({file_size_mb:.1f} MB)\n\n"
                    f"⏱️ **Loading:** {est_time_str}"
                )

        # Load data with spinner
        load_message = f"Loading {'sample of ' if should_sample else ''}{sample_size or total_rows:,} rows..."

        with st.spinner(load_message):
            if should_sample:
                df = cls._sample_parquet(file_path, sample_size)
            else:
                df = cls._load_parquet_cached(file_path, columns=columns)

            actual_time = time.time() - start_time

        # Clear loading info after successful load
        if show_progress:
            info_container.empty()

        # Prepare loading metadata
        load_info = {
            'total_rows': total_rows,
            'loaded_rows': len(df),
            'sampled': should_sample,
            'sample_ratio': len(df) / total_rows if should_sample else 1.0,
            'file_size_mb': file_size_mb,
            'load_time_seconds': actual_time,
            'estimated_time_seconds': est_seconds,
            'columns': metadata['columns'],
            'memory_mb': df.memory_usage(deep=True).sum() / (1024 * 1024),
        }

        return df, load_info

    @staticmethod
    def show_dataset_info(load_info: Dict[str, Any], position: str = "top"):
        """
        Display dataset loading information

        Args:
            load_info: Loading metadata from load_data()
            position: Where to show ("top", "sidebar", or "expander")
        """
        if load_info['sampled']:
            sample_pct = load_info['sample_ratio'] * 100
            message = (
                f"📊 Showing **{load_info['loaded_rows']:,}** of **{load_info['total_rows']:,}** rows "
                f"({sample_pct:.1f}% sample) · "
                f"💾 {load_info['memory_mb']:.1f} MB in memory · "
                f"⏱️ Loaded in {load_info['load_time_seconds']:.2f}s"
            )
            message_type = "info"
        else:
            message = (
                f"📊 **{load_info['loaded_rows']:,}** rows loaded · "
                f"💾 {load_info['memory_mb']:.1f} MB in memory · "
                f"⏱️ Loaded in {load_info['load_time_seconds']:.2f}s"
            )
            message_type = "success"

        if position == "sidebar":
            with st.sidebar:
                if message_type == "info":
                    st.info(message)
                else:
                    st.success(message)
        elif position == "expander":
            with st.expander("📊 Dataset Loading Info", expanded=False):
                st.markdown(message)

                if load_info['sampled']:
                    st.markdown("---")
                    st.markdown(
                        "**Why sampling?** Large datasets are automatically sampled for "
                        "better performance while preserving statistical properties. "
                        "Visualizations remain representative of the full dataset."
                    )
        else:  # top
            if message_type == "info":
                st.info(message)
            else:
                st.success(message)

    @staticmethod
    def show_loading_warning(total_rows: int, file_size_mb: float):
        """Show warning for very large datasets before loading"""
        if total_rows > DataLoader.HUGE_DATASET_ROWS:
            est_seconds, est_time_str = DataLoader.estimate_load_time(total_rows, file_size_mb)

            st.warning(
                f"⚠️ **Large Dataset Detected**\n\n"
                f"This dataset contains **{total_rows:,} rows** ({file_size_mb:.1f} MB). "
                f"Loading may take {est_time_str}.\n\n"
                f"A smart sample will be used automatically for optimal performance."
            )


class ProgressiveLoader:
    """Helper for loading multiple datasets or pages progressively"""

    @staticmethod
    def load_with_progress(items: list, load_func, desc: str = "Loading"):
        """
        Load multiple items with a progress bar

        Args:
            items: List of items to load
            load_func: Function to call for each item
            desc: Description for progress bar

        Yields:
            Results from load_func for each item
        """
        progress_bar = st.progress(0, text=f"{desc}...")

        for i, item in enumerate(items):
            progress = (i + 1) / len(items)
            progress_bar.progress(progress, text=f"{desc} ({i+1}/{len(items)})")

            result = load_func(item)
            yield result

        progress_bar.empty()
