# DashSpec v1.1 Dashboard Gallery

Comprehensive collection of production-ready dashboards showcasing DashSpec v1.1 capabilities.

## Overview

This gallery contains **4 rich, production-quality dashboards** built with DashSpec v1.1, demonstrating:
- Role-based visualization specifications
- 15 advanced chart types (ECDF, violin, hexbin, KDE, etc.)
- Multi-page dashboard layouts
- Advanced filtering and metrics
- Real-world data analysis patterns

All dashboards are fully functional and ready to use with the processed datasets.

---

## Dashboard 1: Credit Card Fraud Detection

**File:** `dsl/examples/fraud_detection_v1.1.yaml`
**Dataset:** Credit Card Fraud (283K transactions)
**Pages:** 4
**Launch:** `make dashboard-fraud`

### Features

**Executive Overview**
- Summary statistics by transaction type
- Amount distribution analysis (histogram + ECDF)
- Violin and box plots for statistical comparison
- Transaction filtering by amount and type

**Pattern Analysis**
- Feature correlation scatter plots with trendlines
- Hexbin density maps for large datasets
- 2D kernel density estimation
- 10-feature correlation heatmap

**Feature Distributions**
- Kernel density estimates by class
- Cumulative distributions (ECDF)
- Violin plots with quartile displays
- Multi-feature comparative analysis

**Transaction Details**
- Pie chart breakdown of transaction types
- Sortable transaction tables
- High-value fraud detection
- Time-series analysis

### Key Visualizations

```yaml
# Example: Advanced scatter with trendline
visualization:
  chart_type: "scatter"
  roles:
    x: "v1"
    y: "v2"
    color: "class"
    size: "amount"
  params:
    trendline: "ols"
    alpha: 0.6
    limit: 5000
```

### Use Cases
- Fraud pattern identification
- Anomaly detection analysis
- Feature engineering insights
- Risk assessment visualization

---

## Dashboard 2: US Air Quality & Pollution Analysis

**File:** `dsl/examples/us_pollution_v1.1.yaml`
**Dataset:** US Pollution Data (1.7M measurements, 2000-2016)
**Pages:** 4
**Launch:** `make dashboard-pollution`

### Features

**Air Quality Overview**
- Multi-state filtering
- NO2, O3, SO2, CO pollutant summaries
- AQI distribution analysis
- State-level comparisons

**Pollutant Analysis**
- Violin plots for pollutant distributions
- Cumulative distribution functions
- Box plots for state comparisons
- Kernel density estimates

**Pollutant Correlations**
- 8-metric correlation heatmap
- Cross-pollutant scatter analysis
- 2D density distributions
- Hexbin maps for dense data

**Geographic Patterns**
- State distribution breakdown
- City-level pollution ranking
- High-pollution area identification
- Temporal trend analysis

### Key Visualizations

```yaml
# Example: Correlation heatmap
visualization:
  chart_type: "corr_heatmap"
  params:
    columns: ["no2_mean", "no2_aqi", "o3_mean", "o3_aqi", "so2_mean", "co_mean"]
    method: "pearson"
    mask_upper: true
```

### Use Cases
- Environmental monitoring
- Regulatory compliance tracking
- Public health impact analysis
- Climate policy insights

---

## Dashboard 3: Spotify Music Analytics

**File:** `dsl/examples/spotify_tracks_v1.1.yaml`
**Dataset:** Spotify Tracks (114K tracks, 114 genres)
**Pages:** 5
**Launch:** `make dashboard-spotify`

### Features

**Music Overview**
- Audio feature statistics by genre
- Popularity distribution analysis
- Danceability and energy violin plots
- Multi-genre filtering

**Audio Feature Analysis**
- Danceability vs Energy correlation
- Hexbin density maps
- Valence (mood) vs Energy analysis
- 2D KDE for acoustic features
- Tempo distribution analysis

**Popularity Insights**
- 10-feature correlation matrix
- What makes tracks popular?
- Audio feature impact on success
- Genre-specific patterns

**Genre Characteristics**
- Cross-genre box plot comparisons
- Cumulative distribution analysis
- Acoustic feature KDE
- Genre distribution breakdown

**Track Explorer**
- Most popular tracks table
- High-energy track listings
- Most danceable tracks
- Sortable by multiple metrics

### Key Visualizations

```yaml
# Example: Multi-role scatter with size encoding
visualization:
  chart_type: "scatter"
  roles:
    x: "danceability"
    y: "energy"
    color: "track_genre"
    size: "popularity"
  params:
    trendline: "ols"
    alpha: 0.5
```

### Use Cases
- Music recommendation systems
- Playlist curation
- Genre analysis
- Artist insights

---

## Dashboard 4: Amazon Food Reviews Analytics

**File:** `dsl/examples/amazon_reviews_v1.1.yaml`
**Dataset:** Amazon Fine Food Reviews (568K reviews)
**Pages:** 5
**Launch:** `make dashboard-reviews`

### Features

**Review Overview**
- Rating distribution analysis
- Helpfulness metrics
- 5-star review percentages
- Multi-rating filtering

**Review Helpfulness**
- Helpfulness vs rating correlation
- Vote density maps
- Distribution analysis
- 2D density visualization

**Temporal Trends**
- Review volume over time
- Rating trends
- Helpfulness evolution
- Seasonal patterns

**Quality Insights**
- Spearman correlation analysis
- Low-rating pattern detection
- Highly helpful review characteristics
- Quality metric distributions

**Review Explorer**
- Most helpful reviews table
- Recent 5-star reviews
- Critical review analysis
- Sortable by helpfulness/time

### Key Visualizations

```yaml
# Example: Violin plot with logarithmic scale
visualization:
  chart_type: "violin"
  roles:
    y: "helpfulnessnumerator"
    by: "score"
  params:
    inner: "box"
    log_y: true
    limit: 50000
```

### Use Cases
- Product quality monitoring
- Customer sentiment analysis
- Review authenticity detection
- Marketing insights

---

## Visualization Type Coverage

All dashboards utilize the full range of DashSpec v1.1 chart types:

### Level 0-1: Tables & Distributions
- ✅ **table**: Sortable data tables with column selection
- ✅ **summary**: Statistical summaries with percentiles
- ✅ **histogram**: Distribution analysis with grouping
- ✅ **ecdf**: Cumulative distribution functions
- ✅ **boxplot**: Statistical box plots
- ✅ **violin**: Distribution violin plots with inner displays
- ✅ **kde**: Kernel density estimates

### Level 2: Relationships
- ✅ **scatter**: Correlation with trendlines and multi-encoding
- ✅ **hexbin**: Density heatmaps for large datasets
- ✅ **kde2d**: 2D kernel density estimation

### Level 3: Categoricals & Comparisons
- ✅ **line**: Time series and trend analysis
- ✅ **bar**: Categorical comparisons
- ✅ **heatmap**: Matrix visualizations
- ✅ **corr_heatmap**: Correlation matrices with masking
- ✅ **pie**: Categorical breakdowns

---

## Dashboard Statistics

| Dashboard | Pages | Visualizations | Metrics | Filters | Dataset Size |
|-----------|-------|----------------|---------|---------|--------------|
| Fraud Detection | 4 | 15+ | 4 | 2 | 283K rows |
| US Pollution | 4 | 18+ | 4 | 2 | 1.7M rows |
| Spotify Tracks | 5 | 20+ | 4 | 3 | 114K rows |
| Amazon Reviews | 5 | 21+ | 4 | 2 | 568K rows |
| **Total** | **18** | **74+** | **16** | **9** | **2.7M rows** |

---

## Common Patterns

### Multi-Page Layout
All dashboards follow a consistent structure:
1. **Overview** - High-level metrics and key distributions
2. **Analysis** - Deep dive into patterns and relationships
3. **Correlations** - Feature/metric relationships
4. **Details** - Individual record exploration

### Filtering Strategy
- Range filters for continuous variables
- Multi-select for categorical variables
- Sensible defaults for immediate insights
- Filter values reflected in all visualizations

### Visualization Progression
1. Start with summary statistics
2. Show distributions (histogram/violin/KDE)
3. Explore relationships (scatter/hexbin)
4. Present correlations (heatmaps)
5. Provide detailed tables

---

## Performance Considerations

### Data Sampling
All dashboards use appropriate `limit` parameters:
- Scatter plots: 5K-20K points
- Hexbin: 50K-100K points
- KDE: 20K-50K points
- Tables: 50-100 rows

### Logarithmic Scales
Applied where appropriate:
- Transaction amounts (`log_x: true`)
- Helpfulness votes (`log_y: true`)
- Pollutant concentrations

### Efficient Aggregations
- Pre-filtered metrics
- By-group summaries
- Percentile calculations

---

## Testing & Validation

All dashboards have been:
- ✅ Schema validated against v1.1 specification
- ✅ Tested with real datasets
- ✅ Verified for role-based syntax
- ✅ Checked for visualization compatibility

### Validation Results

```bash
make test  # Run DSL tests
python -m dsl.adapter validate dsl/examples/fraud_detection_v1.1.yaml
```

All dashboards pass validation with zero errors.

---

## Quick Start

### Launch Any Dashboard

```bash
# Fraud detection
make dashboard-fraud

# US pollution
make dashboard-pollution

# Spotify analytics
make dashboard-spotify

# Amazon reviews
make dashboard-reviews

# Or use custom dashboard
make dashboard-custom SPEC=my_dashboard.yaml
```

### Create Your Own

1. Copy an existing example
2. Update data source path
3. Adjust filters and metrics
4. Modify visualizations
5. Test: `python -m dsl.adapter validate your_spec.yaml`
6. Launch: `streamlit run run_dashboard.py -- your_spec.yaml`

---

## Advanced Features Demonstrated

### Role-Based Specifications
```yaml
# v1.1 syntax (recommended)
roles:
  x: "feature1"
  y: "feature2"
  color: "category"
  size: "metric"
```

### Trendline Analysis
```yaml
params:
  trendline: "ols"  # Ordinary least squares
  alpha: 0.6        # Transparency for overplotting
```

### Violin Plot Customization
```yaml
params:
  inner: "box"        # box, quartiles, points
  log_y: true         # Logarithmic scale
```

### Correlation Analysis
```yaml
params:
  method: "pearson"   # pearson, spearman, kendall
  mask_upper: true    # Cleaner heatmap
```

---

## Next Steps

### Extend Existing Dashboards
- Add new pages for deeper analysis
- Create custom metrics
- Implement additional filters
- Add temporal analysis

### Create New Dashboards
See the other datasets:
- IBM HR Attrition (`ibm_hr_attrition.parquet`)
- Network Intrusion Detection (`network_intrusion_*.parquet`)
- TMDB Movies (`tmdb_movies_*.parquet`)
- US Accidents (`us_accidents.parquet`)

### Custom Visualizations
1. Copy `dsl/custom_renderers_template.py`
2. Implement custom chart types
3. Register in `CUSTOM_RENDERERS`
4. Use in dashboard specs

---

## Resources

- **User Guide**: `docs/dsl_v1.1_guide.md`
- **Implementation Docs**: `dev_docs/dsl_v1.1_implementation.md`
- **Schema**: `dsl/schema_v1.1.json`
- **Template**: `dsl/custom_renderers_template.py`

---

## Support & Feedback

Found an issue or have suggestions? Check:
- Makefile: `make help`
- Test validation: `make test`
- Code formatting: `make format`
- Linting: `make lint`

Happy exploring! 🚀
