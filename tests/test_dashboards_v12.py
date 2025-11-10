"""
Test suite for DashSpec v1.2 dashboards

Tests:
- Dashboard specification validation
- Data quality rules and processing
- Formatting specifications
- Multi-page navigation
- Data file availability
- Renderer functionality
- v1.2-specific features
"""

import json
import warnings
from pathlib import Path
from typing import Dict, List

import numpy as np
import pandas as pd
import pytest
import yaml

from dsl.core.adapter import parse, validate, build_ir, execute
from dsl.core.data_quality import DataQualityProcessor
from dsl.core.formatting import format_number, get_currency_symbol


class TestDashboardV12Validation:
    """Test v1.2 dashboard specification validation"""

    @pytest.fixture
    def dashboard_specs(self) -> List[str]:
        """Get all v1.2 dashboard specifications"""
        spec_dir = Path("dsl/examples")
        # Get all production dashboards (exclude test files)
        all_specs = list(spec_dir.glob("*.yaml"))
        exclude = {"failing.yaml", "happy_path.yaml", "minimal.yaml", "enhanced_fraud_analysis.yaml"}
        return [str(f) for f in all_specs if f.name not in exclude]

    def test_all_v12_dashboards_exist(self, dashboard_specs):
        """Verify all expected v1.2 dashboards exist"""
        assert len(dashboard_specs) >= 10, f"Expected at least 10 v1.2 dashboards, found {len(dashboard_specs)}"

    def test_dashboard_specs_valid_yaml(self, dashboard_specs):
        """Test that all dashboards are valid YAML"""
        for spec_path in dashboard_specs:
            with open(spec_path) as f:
                spec = yaml.safe_load(f)
            assert isinstance(spec, dict), f"{spec_path} is not a valid YAML dict"
            assert "dashboard" in spec, f"{spec_path} missing 'dashboard' key"

    def test_dashboard_validation_passes(self, dashboard_specs):
        """Test that all dashboards pass DSL validation"""
        failed = []
        for spec_path in dashboard_specs:
            with open(spec_path) as f:
                spec = yaml.safe_load(f)

            violations = validate(spec)
            if violations:
                failed.append((spec_path, violations))

        if failed:
            msg = "\n".join([
                f"{path}: {[v['message'] for v in viols]}" for path, viols in failed
            ])
            pytest.fail(f"Dashboards failed validation:\n{msg}")

    def test_dashboard_version(self, dashboard_specs):
        """Test that all dashboards use v1.2"""
        for spec_path in dashboard_specs:
            with open(spec_path) as f:
                spec = yaml.safe_load(f)

            version = spec.get("dsl_version")
            assert version == "1.2.0", f"{spec_path} using version {version}, expected 1.2.0"

    def test_dashboard_has_pages(self, dashboard_specs):
        """Test that all dashboards have at least one page"""
        for spec_path in dashboard_specs:
            with open(spec_path) as f:
                spec = yaml.safe_load(f)

            pages = spec.get("dashboard", {}).get("pages", [])
            assert len(pages) >= 1, f"{spec_path} has no pages"


class TestV12Metadata:
    """Test v1.2 metadata enhancements"""

    @pytest.fixture
    def dashboard_specs(self) -> List[str]:
        """Get all v1.2 dashboard specifications"""
        spec_dir = Path("dsl/examples")
        # Get all production dashboards (exclude test files)
        all_specs = list(spec_dir.glob("*.yaml"))
        exclude = {"failing.yaml", "happy_path.yaml", "minimal.yaml", "enhanced_fraud_analysis.yaml"}
        return [str(f) for f in all_specs if f.name not in exclude]

    def test_metadata_has_currency(self, dashboard_specs):
        """Test that all dashboards specify currency"""
        for spec_path in dashboard_specs:
            with open(spec_path) as f:
                spec = yaml.safe_load(f)

            metadata = spec.get("dashboard", {}).get("metadata", {})
            assert "currency" in metadata, f"{spec_path} missing currency in metadata"
            assert isinstance(metadata["currency"], str), f"{spec_path} currency should be string"
            assert len(metadata["currency"]) == 3, f"{spec_path} currency should be 3-letter ISO code"

    def test_metadata_has_narrative(self, dashboard_specs):
        """Test that all dashboards have narrative"""
        for spec_path in dashboard_specs:
            with open(spec_path) as f:
                spec = yaml.safe_load(f)

            metadata = spec.get("dashboard", {}).get("metadata", {})
            assert "narrative" in metadata, f"{spec_path} missing narrative in metadata"
            narrative = metadata["narrative"]
            assert isinstance(narrative, str), f"{spec_path} narrative should be string"
            assert len(narrative) > 50, f"{spec_path} narrative should be descriptive (>50 chars)"

    def test_metadata_structure_complete(self, dashboard_specs):
        """Test that metadata has all recommended fields"""
        required_fields = ["dataset_name", "description", "currency", "narrative"]
        for spec_path in dashboard_specs:
            with open(spec_path) as f:
                spec = yaml.safe_load(f)

            metadata = spec.get("dashboard", {}).get("metadata", {})
            for field in required_fields:
                assert field in metadata, f"{spec_path} missing {field} in metadata"


class TestFormattingSpecifications:
    """Test v1.2 formatting specifications"""

    @pytest.fixture
    def dashboard_specs(self) -> List[str]:
        """Get all v1.2 dashboard specifications"""
        spec_dir = Path("dsl/examples")
        # Get all production dashboards (exclude test files)
        all_specs = list(spec_dir.glob("*.yaml"))
        exclude = {"failing.yaml", "happy_path.yaml", "minimal.yaml", "enhanced_fraud_analysis.yaml"}
        return [str(f) for f in all_specs if f.name not in exclude]

    def test_formatting_rules_exist(self, dashboard_specs):
        """Test that dashboards have formatting rules"""
        for spec_path in dashboard_specs:
            with open(spec_path) as f:
                spec = yaml.safe_load(f)

            data_source = spec.get("dashboard", {}).get("data_source", {})
            formatting = data_source.get("formatting")
            assert formatting is not None, f"{spec_path} missing formatting rules"
            assert isinstance(formatting, dict), f"{spec_path} formatting should be dict"

    def test_formatting_rules_valid(self, dashboard_specs):
        """Test that formatting rules are valid"""
        valid_types = ["integer", "number", "currency", "percent"]
        for spec_path in dashboard_specs:
            with open(spec_path) as f:
                spec = yaml.safe_load(f)

            formatting = spec.get("dashboard", {}).get("data_source", {}).get("formatting", {})
            for field, fmt in formatting.items():
                assert "type" in fmt, f"{spec_path} field {field} missing type"
                assert fmt["type"] in valid_types, f"{spec_path} invalid format type: {fmt['type']}"

    def test_column_labels_exist(self, dashboard_specs):
        """Test that dashboards have column labels"""
        for spec_path in dashboard_specs:
            with open(spec_path) as f:
                spec = yaml.safe_load(f)

            data_source = spec.get("dashboard", {}).get("data_source", {})
            column_labels = data_source.get("column_labels")
            assert column_labels is not None, f"{spec_path} missing column_labels"
            assert isinstance(column_labels, dict), f"{spec_path} column_labels should be dict"

    def test_format_number_function(self):
        """Test format_number utility function"""
        # Test currency formatting
        result = format_number(1234.56, {"type": "currency", "precision": 2})
        assert "$" in result or "1,234.56" in result

        # Test percent formatting
        result = format_number(0.456, {"type": "percent", "precision": 1})
        assert "%" in result

        # Test integer formatting
        result = format_number(12345, {"type": "integer"})
        assert "," in result or "12345" in result

    def test_currency_symbols(self):
        """Test currency symbol mapping"""
        assert get_currency_symbol("USD") == "$"
        assert get_currency_symbol("EUR") == "€"
        assert get_currency_symbol("GBP") == "£"
        assert get_currency_symbol("JPY") == "¥"


class TestDataQualityRules:
    """Test v1.2 data quality specifications and processing"""

    @pytest.fixture
    def dashboard_specs(self) -> List[str]:
        """Get all v1.2 dashboard specifications"""
        spec_dir = Path("dsl/examples")
        # Get all production dashboards (exclude test files)
        all_specs = list(spec_dir.glob("*.yaml"))
        exclude = {"failing.yaml", "happy_path.yaml", "minimal.yaml", "enhanced_fraud_analysis.yaml"}
        return [str(f) for f in all_specs if f.name not in exclude]

    def test_dq_rules_exist(self, dashboard_specs):
        """Test that dashboards have data quality rules"""
        for spec_path in dashboard_specs:
            with open(spec_path) as f:
                spec = yaml.safe_load(f)

            data_source = spec.get("dashboard", {}).get("data_source", {})
            dq_rules = data_source.get("data_quality")
            assert dq_rules is not None, f"{spec_path} missing data_quality rules"

    def test_dq_structure_valid(self, dashboard_specs):
        """Test that DQ rules have valid structure"""
        required_sections = ["missing_values", "duplicates", "outliers", "validation", "reporting"]
        for spec_path in dashboard_specs:
            with open(spec_path) as f:
                spec = yaml.safe_load(f)

            dq_rules = spec.get("dashboard", {}).get("data_source", {}).get("data_quality", {})
            for section in required_sections:
                assert section in dq_rules, f"{spec_path} missing DQ section: {section}"

    def test_dq_processor_initialization(self):
        """Test that DataQualityProcessor can be initialized"""
        dq_rules = {
            "missing_values": {"strategy": "auto", "rules": []},
            "duplicates": {"enabled": False},
            "outliers": {"enabled": True, "rules": []},
            "validation": {"rules": []},
            "reporting": {"log_level": "info"}
        }
        processor = DataQualityProcessor(dq_rules)
        assert processor is not None
        assert processor.rules == dq_rules

    def test_dq_processor_handles_outliers(self):
        """Test outlier detection and capping"""
        # Create test data with outliers
        df = pd.DataFrame({
            "value": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 100, 200]  # 100, 200 are clear outliers
        })

        dq_rules = {
            "missing_values": {"strategy": "auto", "rules": []},
            "duplicates": {"enabled": False},
            "outliers": {
                "enabled": True,
                "rules": [{
                    "fields": ["value"],
                    "method": "percentile",
                    "lower": 1.0,
                    "upper": 90.0,
                    "action": "cap"
                }]
            },
            "validation": {"rules": []},
            "reporting": {"log_level": "info", "show_summary": False}
        }

        processor = DataQualityProcessor(dq_rules)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            result_df, report = processor.process(df)

        # Check that extreme outliers (200) were capped - 90th percentile is around 10-91
        assert result_df["value"].max() <= 100, f"Extreme outliers should be capped, got max={result_df['value'].max()}"
        assert result_df["value"].max() < 200, "200 should be capped below its original value"
        assert report["outliers_detected"] > 0, "Should detect outliers"

    def test_dq_processor_handles_missing_values(self):
        """Test missing value handling"""
        df = pd.DataFrame({
            "value": [1, 2, np.nan, 4, np.nan, 6]
        })

        dq_rules = {
            "missing_values": {
                "strategy": "auto",
                "rules": [{
                    "fields": ["value"],
                    "action": "drop_rows"
                }]
            },
            "duplicates": {"enabled": False},
            "outliers": {"enabled": False},
            "validation": {"rules": []},
            "reporting": {"log_level": "info", "show_summary": False}
        }

        processor = DataQualityProcessor(dq_rules)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            result_df, report = processor.process(df)

        # Check that NaN rows were dropped
        assert len(result_df) == 4, "Should drop rows with NaN"
        assert result_df["value"].isna().sum() == 0, "No NaN values should remain"


class TestMultiPageNavigation:
    """Test multi-page dashboard features"""

    @pytest.fixture
    def dashboard_specs(self) -> List[str]:
        """Get all v1.2 dashboard specifications"""
        spec_dir = Path("dsl/examples")
        # Get all production dashboards (exclude test files)
        all_specs = list(spec_dir.glob("*.yaml"))
        exclude = {"failing.yaml", "happy_path.yaml", "minimal.yaml", "enhanced_fraud_analysis.yaml"}
        return [str(f) for f in all_specs if f.name not in exclude]

    def test_all_dashboards_have_multiple_pages(self, dashboard_specs):
        """Test that v1.2 dashboards have multiple pages"""
        for spec_path in dashboard_specs:
            with open(spec_path) as f:
                spec = yaml.safe_load(f)

            pages = spec.get("dashboard", {}).get("pages", [])
            # All v1.2 dashboards should have 4-5 pages
            assert len(pages) >= 4, f"{spec_path} should have at least 4 pages, has {len(pages)}"

    def test_page_ids_unique(self, dashboard_specs):
        """Test that page IDs are unique within each dashboard"""
        for spec_path in dashboard_specs:
            with open(spec_path) as f:
                spec = yaml.safe_load(f)

            pages = spec.get("dashboard", {}).get("pages", [])
            page_ids = [p.get("id") for p in pages]
            assert len(page_ids) == len(set(page_ids)), f"{spec_path} has duplicate page IDs"

    def test_pages_have_titles(self, dashboard_specs):
        """Test that all pages have titles"""
        for spec_path in dashboard_specs:
            with open(spec_path) as f:
                spec = yaml.safe_load(f)

            pages = spec.get("dashboard", {}).get("pages", [])
            for idx, page in enumerate(pages):
                assert "title" in page, f"{spec_path} page {idx} missing title"
                assert len(page["title"]) > 0, f"{spec_path} page {idx} has empty title"


class TestDataAvailability:
    """Test that data files are available"""

    @pytest.fixture
    def dashboard_specs(self) -> List[str]:
        """Get all v1.2 dashboard specifications"""
        spec_dir = Path("dsl/examples")
        # Get all production dashboards (exclude test files)
        all_specs = list(spec_dir.glob("*.yaml"))
        exclude = {"failing.yaml", "happy_path.yaml", "minimal.yaml", "enhanced_fraud_analysis.yaml"}
        return [str(f) for f in all_specs if f.name not in exclude]

    def test_data_files_exist(self, dashboard_specs):
        """Test that all referenced data files exist"""
        missing = []
        for spec_path in dashboard_specs:
            with open(spec_path) as f:
                spec = yaml.safe_load(f)

            data_path = spec.get("dashboard", {}).get("data_source", {}).get("path")
            if data_path and not Path(data_path).exists():
                missing.append((spec_path, data_path))

        if missing:
            msg = "\n".join([f"{spec}: {data}" for spec, data in missing])
            pytest.fail(f"Missing data files:\n{msg}")

    def test_data_files_readable(self, dashboard_specs):
        """Test that all data files can be read"""
        for spec_path in dashboard_specs:
            with open(spec_path) as f:
                spec = yaml.safe_load(f)

            data_path = spec.get("dashboard", {}).get("data_source", {}).get("path")
            if data_path and Path(data_path).exists():
                try:
                    df = pd.read_parquet(data_path)
                    assert len(df) > 0, f"Empty dataframe: {data_path}"
                except Exception as e:
                    pytest.fail(f"Cannot read {data_path}: {e}")


class TestIntegrationV12:
    """Integration tests for v1.2 features"""

    def test_full_pipeline_execution(self):
        """Test complete pipeline: parse → validate → build IR → execute"""
        spec_path = "dsl/examples/fraud_detection.yaml"

        if not Path(spec_path).exists():
            pytest.skip(f"Test spec not found: {spec_path}")

        # Parse
        with open(spec_path) as f:
            spec = yaml.safe_load(f)

        # Validate
        violations = validate(spec)
        assert len(violations) == 0, f"Validation errors: {violations}"

        # Build IR
        ir = build_ir(spec)
        assert ir is not None
        assert ir["version"] == "1.2.0"

        # Execute (if data available)
        data_path = spec.get("dashboard", {}).get("data_source", {}).get("path")
        if Path(data_path).exists():
            inputs = {"filters": {}}
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                results = execute(ir, inputs)

            assert "pages" in results
            assert len(results["pages"]) > 0

    def test_renderer_initialization_with_tabs(self):
        """Test that StreamlitRenderer can be initialized with tabs"""
        from dsl import StreamlitRenderer

        spec_path = "dsl/examples/fraud_detection.yaml"
        if not Path(spec_path).exists():
            pytest.skip(f"Test spec not found: {spec_path}")

        # Test with tabs=False (standalone)
        renderer_standalone = StreamlitRenderer(spec_path, use_tabs=False)
        assert renderer_standalone.use_tabs is False

        # Test with tabs=True (gallery)
        renderer_gallery = StreamlitRenderer(spec_path, use_tabs=True)
        assert renderer_gallery.use_tabs is True


def test_app_imports_successfully():
    """Test that the gallery app can be imported"""
    try:
        import app
    except ImportError as e:
        pytest.fail(f"Cannot import app.py: {e}")


def test_all_modules_importable():
    """Test that all DSL modules can be imported"""
    modules = [
        "dsl.core.adapter",
        "dsl.renderers.streamlit.viz_renderers",
        "dsl.renderers.streamlit",
        "dsl.core.data_quality",
        "dsl.core.formatting",
        "dsl.core.data_loader"
    ]

    for module in modules:
        try:
            __import__(module)
        except ImportError as e:
            pytest.fail(f"Cannot import {module}: {e}")


# Run with: pytest tests/test_dashboards_v12.py -v
# Run with coverage: pytest tests/test_dashboards_v12.py --cov=dsl --cov-report=html
