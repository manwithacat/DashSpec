"""
DashSpec Python Adapter

Provides functions to parse, validate, canonicalize, and execute dashboard specifications.
"""

import json
import logging
from pathlib import Path
from typing import Any, TypedDict

import jsonschema
import yaml

logger = logging.getLogger(__name__)


# Violation severity levels
class ViolationSeverity:
    CRITICAL = "critical"  # Missing required fields, invalid references
    ERROR = "error"        # Schema violations, unsupported versions
    WARNING = "warning"    # Questionable but functional configurations
    INFO = "info"          # Suggestions for improvement


class Violation(TypedDict):
    """Validation violation"""

    code: str
    severity: str  # "critical", "error", "warning", "info"
    message: str
    path: str
    repair: str


def parse(src: str) -> dict:
    """
    Parse a YAML dashboard specification

    Args:
        src: YAML string containing the dashboard spec

    Returns:
        Parsed specification as dictionary

    Raises:
        yaml.YAMLError: If YAML is malformed
    """
    try:
        spec = yaml.safe_load(src)
        if not isinstance(spec, dict):
            raise ValueError("Dashboard spec must be a YAML object/dictionary")
        return spec
    except yaml.YAMLError as e:
        raise ValueError(f"Invalid YAML: {e}")


def canonicalize(model: dict) -> str:
    """
    Convert a dashboard model to canonical YAML form

    Args:
        model: Dashboard specification dictionary

    Returns:
        Canonical YAML string with sorted keys and consistent formatting
    """

    # Sort keys alphabetically, with dsl_version first
    def sort_keys(obj: Any) -> Any:
        if isinstance(obj, dict):
            # dsl_version always comes first
            sorted_dict = {}
            if "dsl_version" in obj:
                sorted_dict["dsl_version"] = obj["dsl_version"]
            for key in sorted(k for k in obj.keys() if k != "dsl_version"):
                sorted_dict[key] = sort_keys(obj[key])
            return sorted_dict
        elif isinstance(obj, list):
            return [sort_keys(item) for item in obj]
        else:
            return obj

    canonical = sort_keys(model)

    # Dump with consistent formatting
    return yaml.dump(
        canonical,
        default_flow_style=False,
        indent=2,
        sort_keys=False,  # We've already sorted
        allow_unicode=True,
    )


def validate(model: dict, policy: dict = None, factors: dict = None) -> list[Violation]:
    """
    Validate a dashboard specification

    Args:
        model: Dashboard specification dictionary
        policy: Optional validation policy (strictness, auto_correct, etc.)
        factors: Optional runtime factors (reserved for future use)

    Returns:
        List of validation violations (empty if valid)
    """
    violations = []

    # Extract validation policy from model if not provided
    if policy is None:
        policy = model.get("validation_policy", {})

    strictness = policy.get("strictness", "moderate")
    suppress_codes = set(policy.get("suppress_codes", []))

    # Detect DSL version and validate against supported versions
    SUPPORTED_VERSIONS = ["1.0", "1.1", "1.2", "1.3"]
    dsl_version = model.get("dsl_version", "1.0.0")

    # Extract major.minor version for validation
    version_prefix = ".".join(str(dsl_version).split(".")[:2])

    if version_prefix not in SUPPORTED_VERSIONS:
        violations.append(
            Violation(
                code="UNSUPPORTED_VERSION",
                severity=ViolationSeverity.ERROR,
                message=f"DSL version '{dsl_version}' is not supported. Supported versions: {', '.join(SUPPORTED_VERSIONS)}",
                path="/dsl_version",
                repair=f"Update dsl_version to one of: {', '.join(SUPPORTED_VERSIONS)}.x",
            )
        )
        return violations

    # Load appropriate schema based on version
    if dsl_version.startswith("1.2"):
        schema_file = "schema_v1.2.json"
    elif dsl_version.startswith("1.1"):
        schema_file = "schema_v1.1.json"
    else:
        schema_file = "schema.json"
    schema_path = Path(__file__).parent.parent / "schemas" / schema_file

    try:
        with open(schema_path) as f:
            schema = json.load(f)
    except FileNotFoundError:
        violations.append(
            Violation(
                code="SCHEMA_NOT_FOUND",
                severity=ViolationSeverity.ERROR,
                message=f"Schema file not found: {schema_file}",
                path="/",
                repair=f"Ensure {schema_file} exists in dsl/ directory",
            )
        )
        return violations

    # Validate against schema
    try:
        jsonschema.validate(instance=model, schema=schema)
    except jsonschema.ValidationError as e:
        violations.append(
            Violation(
                code="SCHEMA_VIOLATION",
                severity=ViolationSeverity.ERROR,
                message=f"Schema validation failed: {e.message}",
                path=f"/{'/'.join(str(p) for p in e.path)}",
                repair=f"Ensure field conforms to schema requirements",
            )
        )
    except jsonschema.SchemaError as e:
        violations.append(
            Violation(
                code="INVALID_SCHEMA",
                severity=ViolationSeverity.ERROR,
                message=f"Invalid schema: {e.message}",
                path="/",
                repair="Contact maintainer - schema file is malformed",
            )
        )

    # Additional semantic validations
    if "dashboard" in model:
        dashboard = model["dashboard"]

        # Check for duplicate IDs
        all_ids = set()

        if "pages" in dashboard:
            for page_idx, page in enumerate(dashboard["pages"]):
                page_id = page.get("id")
                if page_id in all_ids:
                    violations.append(
                        Violation(
                code="DUPLICATE_ID",
                severity=ViolationSeverity.ERROR,
                            message=f"Duplicate ID '{page_id}' found in pages",
                            path=f"/dashboard/pages/{page_idx}/id",
                            repair=f"Rename page to use a unique ID",
                        )
                    )
                else:
                    all_ids.add(page_id)

                # Check filters
                if "filters" in page:
                    for filter_idx, filt in enumerate(page["filters"]):
                        filter_id = filt.get("id")
                        if filter_id in all_ids:
                            violations.append(
                                Violation(
                code="DUPLICATE_ID",
                severity=ViolationSeverity.ERROR,
                                    message=f"Duplicate ID '{filter_id}' found",
                                    path=f"/dashboard/pages/{page_idx}/filters/{filter_idx}/id",
                                    repair=f"Rename filter to use a unique ID",
                                )
                            )
                        else:
                            all_ids.add(filter_id)

                # Check metrics
                metric_ids = set()
                if "metrics" in page:
                    for metric_idx, metric in enumerate(page["metrics"]):
                        metric_id = metric.get("id")
                        if metric_id in metric_ids:
                            violations.append(
                                Violation(
                code="DUPLICATE_ID",
                severity=ViolationSeverity.ERROR,
                                    message=f"Duplicate metric ID '{metric_id}'",
                                    path=f"/dashboard/pages/{page_idx}/metrics/{metric_idx}/id",
                                    repair=f"Rename metric to use a unique ID within the page",
                                )
                            )
                        else:
                            metric_ids.add(metric_id)

                # Check component IDs and references
                if "layout" in page and "components" in page["layout"]:
                    for comp_idx, comp in enumerate(page["layout"]["components"]):
                        comp_id = comp.get("id")
                        if comp_id in all_ids:
                            violations.append(
                                Violation(
                code="DUPLICATE_ID",
                severity=ViolationSeverity.ERROR,
                                    message=f"Duplicate component ID '{comp_id}'",
                                    path=f"/dashboard/pages/{page_idx}/layout/components/{comp_idx}/id",
                                    repair=f"Rename component to use a unique ID",
                                )
                            )
                        else:
                            all_ids.add(comp_id)

                        # Validate metric references
                        if comp.get("type") == "metric_card" and "metric_id" in comp:
                            metric_id = comp["metric_id"]
                            if metric_id not in metric_ids:
                                violations.append(
                                    Violation(
                code="INVALID_REFERENCE",
                severity=ViolationSeverity.CRITICAL,
                                        message=f"Reference to metric '{metric_id}' not found",
                                        path=f"/dashboard/pages/{page_idx}/layout/components/{comp_idx}/metric_id",
                                        repair=f"Define a metric with id '{metric_id}' or update the reference",
                                    )
                                )

                        # Validate visualizations (v1.1)
                        if comp.get("type") == "visualization" and "visualization" in comp:
                            viz = comp["visualization"]
                            chart_type = viz.get("chart_type")

                            # Define required roles for each chart type
                            required_roles = {
                                "histogram": ["x"],
                                "ecdf": ["x"],
                                "boxplot": ["y"],
                                "violin": ["y"],
                                "kde": ["x"],
                                "scatter": ["x", "y"],
                                "hexbin": ["x", "y"],
                                "kde2d": ["x", "y"],
                                "line": ["x", "y"],
                                "bar": ["x", "y"],
                                "heatmap": ["x", "y"],
                                "pie": ["x"],
                            }

                            # Check if chart type requires specific roles
                            if chart_type in required_roles:
                                roles = viz.get("roles", {})
                                for required_role in required_roles[chart_type]:
                                    # Check in roles (v1.1) or legacy field names (v1.0)
                                    legacy_field = f"{required_role}_field"
                                    has_role = required_role in roles
                                    has_legacy = legacy_field in viz

                                    if not has_role and not has_legacy:
                                        violations.append(
                                            Violation(
                code="MISSING_REQUIRED_ROLE",
                severity=ViolationSeverity.ERROR,
                                                message=f"Chart type '{chart_type}' requires '{required_role}' role",
                                                path=f"/dashboard/pages/{page_idx}/layout/components/{comp_idx}/visualization",
                                                repair=f"Add 'roles: {{{required_role}: \"field_name\"}}' or '{legacy_field}: \"field_name\"'",
                                            )
                                        )

        # Validate data quality rules against schema
        data_source = dashboard.get("data_source", {})
        schema = data_source.get("schema", {})
        dq_rules = data_source.get("data_quality", {})

        if dq_rules and schema:
            # Check outlier rules
            outlier_config = dq_rules.get("outliers", {})
            if outlier_config.get("enabled") and outlier_config.get("rules"):
                for rule_idx, rule in enumerate(outlier_config["rules"]):
                    fields = rule.get("fields", [])
                    method = rule.get("method", "percentile")

                    for field in fields:
                        if field not in schema:
                            violations.append(
                                Violation(
                code="DQ_FIELD_NOT_IN_SCHEMA",
                severity=ViolationSeverity.ERROR,
                                    message=f"Data quality outlier rule references field '{field}' not found in schema",
                                    path=f"/dashboard/data_source/data_quality/outliers/rules/{rule_idx}",
                                    repair=f"Remove '{field}' from DQ rule or add it to schema definition",
                                )
                            )
                            continue

                        # Check if field type is suitable for percentile-based outlier detection
                        field_type = schema[field]
                        if method == "percentile":
                            # Percentile method is inappropriate for categorical/discrete fields
                            discrete_types = {"string", "object", "category"}
                            if field_type in discrete_types:
                                violations.append(
                                    Violation(
                code="DQ_INAPPROPRIATE_METHOD",
                severity=ViolationSeverity.WARNING,
                                        message=f"Percentile outlier detection on categorical field '{field}' (type: {field_type})",
                                        path=f"/dashboard/data_source/data_quality/outliers/rules/{rule_idx}",
                                        repair=f"Remove '{field}' from outlier detection or use a different method for categorical data",
                                    )
                                )
                            # Warn about discrete integer fields with few unique values
                            elif field_type in {"integer", "int", "int32", "int64"}:
                                # Fields like year, month, quarter, day_of_week have limited ranges
                                # Use exact matches or start/end patterns to avoid false positives
                                discrete_temporal_fields = {
                                    "year", "month", "quarter", "day", "week", "hour", "minute", "second",
                                    "day_of_week", "day_of_month", "day_of_year", "week_of_year",
                                    "hour_of_day", "minute_of_hour"
                                }
                                field_lower = field.lower()
                                # Check if it's an exact match or starts/ends with temporal pattern
                                is_temporal = (
                                    field_lower in discrete_temporal_fields or
                                    field_lower.endswith("_year") or
                                    field_lower.endswith("_month") or
                                    field_lower.endswith("_quarter") or
                                    field_lower.endswith("_day") or
                                    field_lower.endswith("_week")
                                )
                                if is_temporal:
                                    violations.append(
                                        Violation(
                code="DQ_QUESTIONABLE_METHOD",
                severity=ViolationSeverity.WARNING,
                                            message=f"Percentile outlier detection on discrete temporal field '{field}' may not be appropriate",
                                            path=f"/dashboard/data_source/data_quality/outliers/rules/{rule_idx}",
                                            repair=f"Consider removing '{field}' from outlier detection - temporal fields typically don't have outliers",
                                        )
                                    )

            # Check missing value rules
            missing_config = dq_rules.get("missing_values", {})
            if missing_config.get("rules"):
                for rule_idx, rule in enumerate(missing_config["rules"]):
                    fields = rule.get("fields", [])
                    for field in fields:
                        if field not in schema:
                            violations.append(
                                Violation(
                code="DQ_FIELD_NOT_IN_SCHEMA",
                severity=ViolationSeverity.ERROR,
                                    message=f"Data quality missing value rule references field '{field}' not found in schema",
                                    path=f"/dashboard/data_source/data_quality/missing_values/rules/{rule_idx}",
                                    repair=f"Remove '{field}' from DQ rule or add it to schema definition",
                                )
                            )

            # Check validation rules
            validation_config = dq_rules.get("validation", {})
            if validation_config.get("rules"):
                for rule_idx, rule in enumerate(validation_config["rules"]):
                    fields = rule.get("fields", [])
                    for field in fields:
                        if field not in schema:
                            violations.append(
                                Violation(
                code="DQ_FIELD_NOT_IN_SCHEMA",
                severity=ViolationSeverity.ERROR,
                                    message=f"Data quality validation rule references field '{field}' not found in schema",
                                    path=f"/dashboard/data_source/data_quality/validation/rules/{rule_idx}",
                                    repair=f"Remove '{field}' from DQ rule or add it to schema definition",
                                )
                            )

    # Apply validation policy filtering
    # Filter by suppression list
    violations = [v for v in violations if v["code"] not in suppress_codes]

    # Filter by strictness level
    if strictness == "relaxed":
        # Only return critical and error severity violations
        violations = [v for v in violations
                     if v.get("severity") in [ViolationSeverity.CRITICAL, ViolationSeverity.ERROR]]
    elif strictness == "moderate":
        # Return all except info-level violations
        violations = [v for v in violations
                     if v.get("severity") != ViolationSeverity.INFO]
    # strict mode: return all violations (no filtering)

    return violations


def build_ir(model: dict) -> dict:
    """
    Build intermediate representation for execution

    Args:
        model: Validated dashboard specification

    Returns:
        Intermediate representation with resolved dependencies
    """
    data_source = model.get("dashboard", {}).get("data_source", {})

    ir = {
        "version": model.get("dsl_version", "1.0.0"),
        "dashboard": model.get("dashboard", {}),
        "data_source_path": data_source.get("path"),
        "data_quality_rules": data_source.get("data_quality"),
        "pages": [],
    }

    # Process each page
    for page in model.get("dashboard", {}).get("pages", []):
        page_ir = {
            "id": page.get("id"),
            "title": page.get("title"),
            "filters": page.get("filters", []),
            "metrics": page.get("metrics", []),
            "components": page.get("layout", {}).get("components", []),
            "layout_type": page.get("layout", {}).get("type", "single"),
        }
        ir["pages"].append(page_ir)

    return ir


def execute(ir: dict, inputs: dict) -> dict:
    """
    Execute the dashboard specification

    Args:
        ir: Intermediate representation from build_ir
        inputs: Runtime inputs (e.g., filter values, parameters)

    Returns:
        Execution results with computed metrics and prepared data
    """
    import pandas as pd

    results = {"dashboard_id": ir["dashboard"].get("id"), "pages": []}

    # Load data source with intelligent loading
    data_path = ir.get("data_source_path")
    if not data_path:
        raise ValueError("No data source specified")

    # Use DataLoader for optimized loading with caching and sampling
    from .data_loader import DataLoader

    df, load_info = DataLoader.load_data(
        data_path,
        max_rows=None,  # Will be determined per-visualization
        show_progress=True
    )

    # Show loading info in expander
    DataLoader.show_dataset_info(load_info, position="expander")

    # Apply data quality rules if specified
    dq_rules = ir.get('data_quality_rules')
    dq_report = None

    if dq_rules:
        try:
            from .data_quality import DataQualityProcessor
            import streamlit as st

            with st.spinner("Applying data quality rules..."):
                dq_processor = DataQualityProcessor(dq_rules)
                df, dq_report = dq_processor.process(df)

                st.success(f"✅ Data quality processing complete: {len(df):,} rows")

        except Exception as e:
            import streamlit as st
            import traceback

            # Provide detailed error information
            st.error("❌ Data Quality Processing Failed")

            # Display error details in expandable section
            with st.expander("🔍 Error Details", expanded=True):
                st.markdown(f"**Error Type:** `{type(e).__name__}`")
                st.markdown(f"**Error Message:** {str(e)}")

                # Provide specific repair hints based on error type
                repair_hints = []
                error_str = str(e).lower()

                if "keyerror" in type(e).__name__.lower() or "not found" in error_str:
                    repair_hints.append("**Missing Field:** Check that all fields referenced in DQ rules exist in your dataset schema")
                    repair_hints.append("Verify field names in `data_quality.rules[].fields` match the schema exactly")

                if "typeerror" in type(e).__name__.lower():
                    repair_hints.append("**Type Mismatch:** Ensure DQ rule parameters match expected types")
                    repair_hints.append("Check that numeric thresholds are numbers, not strings")

                if "valueerror" in type(e).__name__.lower():
                    repair_hints.append("**Invalid Value:** Check that percentile values are between 0-100")
                    repair_hints.append("Verify that date formats are valid if using date coercion")

                if "attributeerror" in type(e).__name__.lower():
                    repair_hints.append("**Configuration Error:** Check DQ rule structure matches the schema")
                    repair_hints.append("Ensure all required fields (fields, action, method) are present")

                if not repair_hints:
                    repair_hints.append("**General Guidance:**")
                    repair_hints.append("- Verify DQ rules syntax matches schema_v1.2.json")
                    repair_hints.append("- Check that field datatypes support the DQ operations")
                    repair_hints.append("- Review DQ rule parameters for valid ranges and values")

                st.markdown("### 💡 Repair Hints")
                for hint in repair_hints:
                    st.markdown(f"- {hint}")

                # Show traceback for debugging
                st.markdown("### 🐛 Technical Details")
                with st.code("python"):
                    st.text(traceback.format_exc())

            # Log for debugging
            logger.error(f"DQ processing error: {e}", exc_info=True)

    # Process each page
    for page_ir in ir["pages"]:
        page_result = {
            "id": page_ir["id"],
            "title": page_ir["title"],
            "metrics": {},
            "data": df,  # Store reference to filtered data
        }

        # Apply filters from inputs
        filtered_df = df.copy()
        for filter_spec in page_ir["filters"]:
            filter_id = filter_spec["id"]
            if filter_id in inputs.get("filters", {}):
                filter_value = inputs["filters"][filter_id]
                field = filter_spec["field"]

                # Apply filter based on type
                if filter_spec["type"] == "range":
                    if isinstance(filter_value, (list, tuple)) and len(filter_value) == 2:
                        filtered_df = filtered_df[
                            (filtered_df[field] >= filter_value[0])
                            & (filtered_df[field] <= filter_value[1])
                        ]
                elif filter_spec["type"] in ["select", "multiselect"]:
                    if isinstance(filter_value, list):
                        filtered_df = filtered_df[filtered_df[field].isin(filter_value)]
                    else:
                        filtered_df = filtered_df[filtered_df[field] == filter_value]

        page_result["data"] = filtered_df

        # Compute metrics
        for metric_spec in page_ir["metrics"]:
            metric_id = metric_spec["id"]
            field = metric_spec["field"]
            aggregation = metric_spec["aggregation"]

            # Apply metric-specific filter if present
            metric_df = filtered_df
            if "filter" in metric_spec:
                mf = metric_spec["filter"]
                operator = mf["operator"]
                value = mf["value"]

                if operator == "eq":
                    metric_df = metric_df[metric_df[mf["field"]] == value]
                elif operator == "ne":
                    metric_df = metric_df[metric_df[mf["field"]] != value]
                elif operator == "gt":
                    metric_df = metric_df[metric_df[mf["field"]] > value]
                elif operator == "gte":
                    metric_df = metric_df[metric_df[mf["field"]] >= value]
                elif operator == "lt":
                    metric_df = metric_df[metric_df[mf["field"]] < value]
                elif operator == "lte":
                    metric_df = metric_df[metric_df[mf["field"]] <= value]
                elif operator == "in":
                    metric_df = metric_df[metric_df[mf["field"]].isin(value)]
                elif operator == "not_in":
                    metric_df = metric_df[~metric_df[mf["field"]].isin(value)]

            # Compute aggregation (with NaN handling)
            if aggregation == "count":
                # Count non-null values for the field
                result = metric_df[field].notna().sum()
            elif aggregation == "count_unique":
                # Count unique non-null values (for "count distinct")
                result = metric_df[field].nunique()
            elif aggregation == "sum":
                result = metric_df[field].sum(skipna=True)
            elif aggregation == "mean":
                result = metric_df[field].mean(skipna=True)
            elif aggregation == "median":
                result = metric_df[field].median(skipna=True)
            elif aggregation == "min":
                result = metric_df[field].min(skipna=True)
            elif aggregation == "max":
                result = metric_df[field].max(skipna=True)
            elif aggregation == "std":
                result = metric_df[field].std(skipna=True)
            else:
                result = None

            # Handle NaN results (convert to None for cleaner display)
            if pd.isna(result):
                result = None

            # Round to 3 decimal places for floats
            if isinstance(result, float):
                result = round(result, 3)

            page_result["metrics"][metric_id] = result

        results["pages"].append(page_result)

    return results
