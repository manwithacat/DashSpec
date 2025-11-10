# DashSpec v1.2 Examples

This directory contains production-ready dashboard examples demonstrating the full capabilities of DashSpec v1.2.

## Available Dashboards

### 📊 Credit Card Fraud Detection
**File:** [`fraud_detection.yaml`](fraud_detection.yaml)
**Dataset:** 283K credit card transactions

Comprehensive fraud detection analytics with:
- 4 pages of analysis (Overview, Patterns, Distributions, Details)
- 15+ visualizations including ECDF, violin plots, hexbin density maps
- Advanced correlation analysis with 10-feature heatmap
- Transaction filtering and high-value fraud detection
- Data quality rules with outlier detection and capping

### 🌍 US Air Quality & Pollution
**File:** [`us_pollution.yaml`](us_pollution.yaml)
**Dataset:** 1.7M pollution measurements (2000-2016)

Environmental monitoring dashboard with:
- Multi-pollutant analysis (NO2, O3, SO2, CO)
- State-level comparative visualizations
- 8-metric correlation matrices
- Geographic pattern exploration across 47 states
- Time-series analysis with OLS trendlines

### 🎵 Spotify Music Analytics
**File:** [`spotify_tracks.yaml`](spotify_tracks.yaml)
**Dataset:** 114K tracks across 114 genres

Music analytics platform featuring:
- Audio feature analysis (danceability, energy, valence, tempo)
- Popularity insights and success factor correlation
- Genre characteristic comparison
- Track explorer with popularity rankings
- Multi-page navigation with 5 analysis views

### ⭐ Amazon Food Reviews
**File:** [`amazon_reviews.yaml`](amazon_reviews.yaml)
**Dataset:** 568K customer reviews

Customer sentiment analysis with:
- Rating distribution and helpfulness metrics
- Temporal trend analysis
- Quality insights with correlation matrices
- Review explorer (most helpful, recent, critical)
- Text analysis and review scoring

### 🚗 US Traffic Accidents
**File:** [`us_accidents.yaml`](us_accidents.yaml)
**Dataset:** 7.7M accident records (2016-2023)

Traffic safety analytics with:
- Severity analysis and temporal patterns
- Weather and environmental impact assessment
- Geographic hotspot identification
- Infrastructure feature correlation
- Multi-dimensional filtering

### 🎬 TMDB Movie Database
**File:** [`tmdb_movies.yaml`](tmdb_movies.yaml)
**Dataset:** 4,803 movies with metadata

Film industry analytics featuring:
- Revenue and budget analysis
- Genre performance trends
- Rating correlation studies
- Production insight explorer

### 👔 IBM HR Attrition Analysis
**File:** [`ibm_hr_attrition.yaml`](ibm_hr_attrition.yaml)
**Dataset:** 1,470 employee records

Human resources analytics with:
- Attrition pattern identification
- Compensation and satisfaction analysis
- Department and role comparisons
- Career progression insights

### 🔐 Network Intrusion Detection
**File:** [`network_intrusion.yaml`](network_intrusion.yaml)
**Dataset:** 47,679 network connection records

Cybersecurity monitoring with:
- Attack type classification
- Protocol and service analysis
- Connection pattern exploration
- Security metric correlation

### 🌍 Global Food Price Inflation
**File:** [`food_price_inflation.yaml`](food_price_inflation.yaml)
**Dataset:** Global food commodity prices

Economic analysis featuring:
- Commodity price trends
- Regional inflation patterns
- Market volatility assessment
- Cross-commodity correlation

### ⚡ Power Consumption Analysis
**File:** [`power_consumption.yaml`](power_consumption.yaml)
**Dataset:** Household electric power consumption

Energy usage analytics with:
- Consumption pattern analysis
- Peak usage identification
- Cost optimization insights
- Load distribution visualization

### 🔧 Enhanced Fraud Analysis (Advanced)
**File:** [`enhanced_fraud_analysis.yaml`](enhanced_fraud_analysis.yaml)
**Dataset:** 283K transactions with advanced features

Extended fraud detection showcase demonstrating:
- Full v1.2 feature set
- Advanced data quality processing
- Custom formatting and labeling
- Validation policy configuration
- Comprehensive metadata and narrative

## Test Cases

### ✅ Happy Path (Testing)
**File:** [`happy_path.yaml`](happy_path.yaml)
Simple validation test case for basic functionality

### ⚠️ Minimal Example (Testing)
**File:** [`minimal.yaml`](minimal.yaml)
Minimal viable dashboard specification

### ❌ Failing Example (Testing)
**File:** [`failing.yaml`](failing.yaml)
Intentionally invalid spec for validation testing

## Quick Start

```bash
# Launch the unified gallery (all dashboards)
streamlit run app.py

# Or launch a specific dashboard
streamlit run run_dashboard.py -- dsl/examples/fraud_detection.yaml
streamlit run run_dashboard.py -- dsl/examples/us_pollution.yaml
streamlit run run_dashboard.py -- dsl/examples/spotify_tracks.yaml
```

## v1.2 Features Demonstrated

### Metadata & Narrative
```yaml
metadata:
  dataset_name: "Credit Card Fraud Detection"
  source: "Kaggle MLG-ULB"
  rows: 283726
  currency: USD
  narrative: |
    Comprehensive analysis of credit card transactions...
```

### Data Quality Rules
```yaml
data_quality:
  outliers:
    enabled: true
    rules:
      - fields: [amount]
        method: percentile
        lower: 0.1
        upper: 99.9
        action: cap
  missing_values:
    strategy: auto
```

### Formatting Specifications
```yaml
formatting:
  amount:
    type: currency
    precision: 2
    use_thousands_separator: true
  transaction_rate:
    type: percent
    precision: 1
```

### Column Labels
```yaml
column_labels:
  v1: "PCA Component 1"
  amount: "Transaction Amount"
  class: "Fraud Status"
```

### Validation Policy
```yaml
validation_policy:
  strictness: moderate  # strict | moderate | relaxed
  suppress_codes:
    - DQ_QUESTIONABLE_METHOD
```

### Role-Based Visualizations
```yaml
visualization:
  chart_type: scatter
  roles:
    x: amount
    y: time
    color: class
    size: popularity
  params:
    trendline: ols      # OLS regression line
    alpha: 0.6          # Transparency
    log_x: true         # Log scale
    limit: 5000         # Sample size
```

### Advanced Chart Types
- **ECDF** - Cumulative distributions
- **Violin** - Distribution violin plots with inner quartiles
- **Hexbin** - 2D density heatmaps
- **KDE/KDE2D** - Kernel density estimation
- **Correlation Heatmaps** - With upper triangle masking
- **Box/Boxplot** - Statistical summaries with outliers

## Dashboard Statistics

| Dashboard | Pages | Charts | Metrics | Filters | Rows | Features |
|-----------|-------|--------|---------|---------|------|----------|
| Fraud Detection | 4 | 15+ | 4 | 2 | 283K | ✅ DQ, Formatting |
| US Pollution | 4 | 18+ | 4 | 2 | 1.7M | ✅ Trendlines, Labels |
| Spotify Tracks | 5 | 20+ | 4 | 3 | 114K | ✅ Multi-page, Metadata |
| Amazon Reviews | 5 | 21+ | 4 | 2 | 568K | ✅ Narrative, Currency |
| US Accidents | 4 | 16+ | 5 | 3 | 7.7M | ✅ Large dataset handling |
| TMDB Movies | 3 | 12+ | 3 | 2 | 4.8K | ✅ Revenue analysis |
| IBM HR | 3 | 14+ | 4 | 2 | 1.5K | ✅ Attrition analytics |
| Network Intrusion | 3 | 13+ | 4 | 2 | 47K | ✅ Security metrics |
| Food Price | 3 | 11+ | 3 | 2 | Varies | ✅ Economic indicators |
| Power Consumption | 3 | 10+ | 3 | 1 | Varies | ✅ Energy monitoring |
| **Total** | **37** | **150+** | **38** | **21** | **10M+** | **Full v1.2** |

## Creating Your Own Dashboard

### 1. Copy an example
```bash
cp dsl/examples/fraud_detection.yaml dsl/examples/my_dashboard.yaml
```

### 2. Update metadata
```yaml
dsl_version: 1.2.0
dashboard:
  metadata:
    dataset_name: "My Dataset"
    source: "Data Source"
    currency: USD
    narrative: "Your dataset description..."
```

### 3. Configure data source
```yaml
data_source:
  type: parquet
  path: data/processed/your_dataset.parquet
  schema:
    field1: float
    field2: integer
    field3: string
```

### 4. Add formatting rules
```yaml
formatting:
  revenue:
    type: currency
    precision: 2
  conversion_rate:
    type: percent
    precision: 1
```

### 5. Define data quality
```yaml
data_quality:
  outliers:
    enabled: true
    rules:
      - fields: [revenue]
        method: percentile
        lower: 0.5
        upper: 99.5
        action: cap
```

### 6. Design pages
```yaml
pages:
  - id: overview
    title: "Overview"
    filters: [...]
    metrics: [...]
    layout:
      type: grid
      components: [...]
```

### 7. Validate
```bash
python -c "
from dsl.core.adapter import validate
import yaml

spec = yaml.safe_load(open('dsl/examples/my_dashboard.yaml'))
errors = validate(spec)
if errors:
    for e in errors:
        print(f'{e[\"severity\"]}: {e[\"message\"]}')
else:
    print('✓ Valid')"
```

### 8. Launch
```bash
streamlit run run_dashboard.py -- dsl/examples/my_dashboard.yaml
```

## Validation

All dashboards pass v1.2 schema validation:

```bash
# Run full test suite
python -m pytest tests/test_dashboards_v12.py -v

# Validate all examples
python scripts/audit_yaml_features.py
```

## Documentation

- **Error Handling Guide:** [`dev_docs/error_handling_guide.md`](../../dev_docs/error_handling_guide.md) - Edge case handling
- **Schema Enhancements:** [`dev_docs/schema_enhancements.md`](../../dev_docs/schema_enhancements.md) - Future improvements
- **Validation Policy:** [`dev_docs/validation_policy_design.md`](../../dev_docs/validation_policy_design.md) - Policy system design
- **DSL Restructuring:** [`dev_docs/dsl_restructuring_plan.md`](../../dev_docs/dsl_restructuring_plan.md) - Architecture
- **Schema Specification:** [`dsl/schemas/schema.json`](../schemas/schema.json) - v1.2 JSON schema

## Architecture

The DSL has been restructured for extensibility:

```
dsl/
├── core/                   # Visualization-agnostic logic
│   ├── adapter.py         # DSL execution + validation
│   ├── data_loader.py     # Data loading
│   ├── data_quality.py    # DQ processing
│   └── formatting.py      # Formatting
├── renderers/             # Visualization backends
│   └── streamlit/         # Streamlit implementation
└── schemas/               # Schema specifications
```

This enables future support for other rendering backends (Plotly Dash, Matplotlib, etc.).

## Best Practices

### ✅ DO
- Use validation policies to control error strictness
- Add narratives for context and documentation
- Apply data quality rules for large/messy datasets
- Format currency and percentages appropriately
- Label technical column names with human-readable text
- Test with filtered/sparse data edge cases

### ⚠️ CONSIDER
- Sampling large datasets (`limit: 10000`) for performance
- Using percentile outlier detection over z-score for robustness
- Suppressing specific validation codes for known patterns
- Adding trendlines to time-series scatter plots

### ❌ AVOID
- Hardcoding version suffixes in filenames (use `dsl_version` in YAML)
- Applying statistical methods to categorical fields
- Creating dashboards without data quality rules
- Using raw technical field names without labels

## Support

```bash
# Get help
python run_dashboard.py --help

# Run tests
python -m pytest tests/ -v

# Validate spec
python -c "from dsl import validate; import yaml; validate(yaml.safe_load(open('spec.yaml')))"
```

## Next Steps

1. **Explore the gallery** - Launch `streamlit run app.py` to see all dashboards
2. **Study examples** - Review YAML files to understand patterns
3. **Read documentation** - Check `dev_docs/` for detailed guides
4. **Create your dashboard** - Use examples as templates
5. **Extend functionality** - See [`dsl/renderers/streamlit/custom_renderers_template.py`](../renderers/streamlit/custom_renderers_template.py)

Happy dashboarding! 🚀
