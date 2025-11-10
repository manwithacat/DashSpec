# DashSpec DSL

**DashSpec** is a declarative, verifiable Domain-Specific Language (DSL) for specifying data-driven dashboards. It enables data analysts to create interactive dashboards using a simple YAML specification that gets rendered as a Streamlit application.

## Overview

DashSpec allows you to:
- **Declare** dashboard layouts, visualizations, filters, and metrics in YAML
- **Validate** specifications against a strict JSON Schema
- **Execute** dashboards with computed metrics and filtered data
- **Render** interactive Streamlit applications

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Create a Dashboard Specification

Create a YAML file (e.g., `my_dashboard.yaml`):

```yaml
dsl_version: "1.0.0"

dashboard:
  title: "My Dashboard"
  id: "my_dashboard"
  data_source:
    type: "parquet"
    path: "data/processed/my_data.parquet"
  pages:
    - id: "overview"
      title: "Overview"
      layout:
        type: "single"
        components:
          - id: "table1"
            type: "visualization"
            visualization:
              chart_type: "table"
```

### 3. Launch the Dashboard

```bash
streamlit run run_dashboard.py -- my_dashboard.yaml
```

Or use the fraud detection example:

```bash
streamlit run run_dashboard.py -- dsl/examples/happy_path.yaml
```

## Architecture

### Core Components

1. **Parser** (`adapter.parse`) - Converts YAML to Python dict
2. **Validator** (`adapter.validate`) - Validates against schema with error codes
3. **IR Builder** (`adapter.build_ir`) - Builds intermediate representation
4. **Executor** (`adapter.execute`) - Computes metrics and filters data
5. **Renderer** (`streamlit_renderer.StreamlitRenderer`) - Renders Streamlit UI

### Data Flow

```
YAML Spec → Parse → Validate → Build IR → Execute → Render
```

## DSL Structure

### Top Level

```yaml
dsl_version: "1.0.0"  # Required: DSL version (1.x.x)
dashboard:            # Required: Dashboard definition
  # ... dashboard properties
```

### Dashboard

```yaml
dashboard:
  id: "dashboard_id"                    # Required: Unique identifier
  title: "Dashboard Title"              # Required: Display title
  description: "Dashboard description"  # Optional
  data_source:                          # Required
    type: "parquet"                     # Required: Data format
    path: "data/file.parquet"           # Required: Data path
    schema:                             # Optional: Schema hints
      field1: "float"
      field2: "integer"
  pages:                                # Required: List of pages
    - # ... page definitions
```

### Pages

```yaml
pages:
  - id: "page_id"                       # Required
    title: "Page Title"                 # Required
    description: "Page description"     # Optional
    filters:                            # Optional: Filter widgets
      - # ... filter definitions
    metrics:                            # Optional: Computed metrics
      - # ... metric definitions
    layout:                             # Required
      type: "grid"                      # Required: single|grid|tabs
      components:                       # Required: List of components
        - # ... component definitions
```

### Filters

Supported filter types: `range`, `slider`, `select`, `multiselect`, `date_range`

```yaml
filters:
  - id: "amount_filter"
    field: "amount"
    type: "range"
    label: "Transaction Amount"
    default: [0, 1000]

  - id: "category_filter"
    field: "category"
    type: "select"
    label: "Category"
    default: "A"
```

### Metrics

Supported aggregations: `count`, `sum`, `mean`, `median`, `min`, `max`, `std`

```yaml
metrics:
  - id: "total_count"
    field: "transaction_id"
    aggregation: "count"
    label: "Total Transactions"
    format: ",.0f"

  - id: "fraud_count"
    field: "class"
    aggregation: "count"
    filter:
      field: "class"
      operator: "eq"
      value: 1
    label: "Fraudulent Transactions"
    format: ",.0f"
```

### Visualizations

Supported chart types: `line`, `bar`, `scatter`, `histogram`, `box`, `pie`, `heatmap`, `table`

```yaml
components:
  - id: "scatter_plot"
    type: "visualization"
    title: "Amount vs Time"
    width: "half"
    visualization:
      chart_type: "scatter"
      x_field: "time"
      y_field: "amount"
      color_field: "class"
      size_field: "amount"
      limit: 5000
      sort:
        field: "amount"
        order: "desc"
```

### Layouts

**Single Column:**
```yaml
layout:
  type: "single"
  components:
    - # Full width components
```

**Grid:**
```yaml
layout:
  type: "grid"
  components:
    - id: "comp1"
      width: "full"    # full|half|third
      # ...
```

**Tabs:**
```yaml
layout:
  type: "tabs"
  components:
    - title: "Tab 1"
      # ...
    - title: "Tab 2"
      # ...
```

## Validation

DashSpec performs strict validation with helpful error messages:

```python
from dsl.adapter import parse, validate

spec = parse(yaml_content)
violations = validate(spec)

if violations:
    for v in violations:
        print(f"[{v['code']}] {v['message']}")
        print(f"  Path: {v['path']}")
        print(f"  Repair: {v['repair']}")
```

### Error Codes

- `SCHEMA_VIOLATION` - Schema validation failed
- `INVALID_SCHEMA` - Schema file is malformed
- `DUPLICATE_ID` - Duplicate identifier found
- `INVALID_REFERENCE` - Reference to undefined element
- `UNKNOWN_FIELD` - Field not found in data source
- `INVALID_AGGREGATION` - Incompatible aggregation for data type
- `INVALID_VERSION` - Unsupported DSL version
- `INVALID_PATH` - Invalid file path format

## Testing

Run the test suite:

```bash
python test_dsl.py
```

This tests:
1. ✓ Minimal spec parsing and execution
2. ✓ Happy path with full dashboard features
3. ✓ Error detection for invalid specs

## Examples

### Minimal Example

See `dsl/examples/minimal.yaml` - the smallest valid dashboard:
- Single page with a table visualization
- No filters or metrics

### Happy Path Example

See `dsl/examples/happy_path.yaml` - complete fraud detection dashboard:
- 2 pages (Overview and Analysis)
- Multiple filters (range, select)
- Computed metrics with conditional filters
- Various chart types (scatter, histogram, line, box, pie, table)
- Grid layout with custom widths

### Failing Example

See `dsl/examples/failing.yaml` - intentionally invalid spec for testing:
- Invalid version number
- Duplicate IDs
- Unknown fields
- Invalid references

## API Reference

### Adapter Functions

```python
from dsl.adapter import parse, validate, canonicalize, build_ir, execute

# Parse YAML to dict
spec = parse(yaml_string)

# Validate specification
violations = validate(spec)

# Convert to canonical form
canonical_yaml = canonicalize(spec)

# Build intermediate representation
ir = build_ir(spec)

# Execute with inputs
results = execute(ir, inputs={
    "filters": {
        "filter_id": value
    }
})
```

### Streamlit Renderer

```python
from dsl.streamlit_renderer import render_dashboard

# Render a dashboard
render_dashboard("path/to/spec.yaml")
```

## File Structure

```
dsl/
├── README.md                 # This file
├── design_card.yaml          # DSL design specification
├── schema.json               # JSON Schema for validation
├── validation_rules.yaml     # Validation rules and error codes
├── adapter.py                # Core DSL functions
├── streamlit_renderer.py     # Streamlit rendering engine
└── examples/
    ├── minimal.yaml          # Minimal valid spec
    ├── happy_path.yaml       # Complete example
    └── failing.yaml          # Invalid spec for testing
```

## Design Principles

1. **Declarative** - Specify what you want, not how to build it
2. **Verifiable** - Static validation with helpful error messages
3. **Canonical** - Deterministic serialization with sorted keys
4. **Closed-world** - Reject unknown fields (strict schema)
5. **Separation of Concerns** - Parse → Validate → Execute → Render

## Versioning

DashSpec uses semantic versioning:
- `1.x.x` - Current stable version
- Version constraint: `^1\.\\d+\.\\d+$`

## Contributing

When extending DashSpec:

1. Update `schema.json` with new fields
2. Add validation rules to `validation_rules.yaml`
3. Implement execution logic in `adapter.py`
4. Update renderer in `streamlit_renderer.py`
5. Create test examples
6. Update this README

## License

See main project LICENSE file.

## Support

For issues or questions, see the main project documentation at `/docs/`.
