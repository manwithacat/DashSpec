# Error Handling & Edge Cases Guide

## Overview

This document describes error handling strategies for common edge cases when working with large, variable-quality datasets. The DSL is designed to fail gracefully and provide actionable feedback rather than crashing.

## Statistical Visualization Edge Cases

### Trendline Calculations (Scatter Plots)

**Issue**: Division by zero and numerical instability in OLS (Ordinary Least Squares) regression

**Common Causes**:
- Filtered data with zero variance (all values identical)
- Insufficient data points after filtering (< 3 points)
- Extreme outliers causing numerical instability
- Missing/null values after DQ processing
- Categorical data incorrectly used for regression

**DSL Behavior**:
1. **Warning Suppression**: RuntimeWarnings from statsmodels are suppressed as they're handled internally
2. **Graceful Degradation**: If trendline calculation fails, scatter plot renders without trendline
3. **User Feedback**: Warning message explains the issue and shows fallback behavior

**Example Scenarios**:

```yaml
# Scenario 1: Filtered to single state with constant pollution levels
- chart_type: scatter
  roles:
    x: date_local
    y: no2_mean
  params:
    trendline: ols  # May fail if filtered to constant values
```

**Handling Strategy**:
```python
# In viz_renderers.py:
try:
    # Attempt with trendline
    fig = px.scatter(..., trendline=trendline)
except Exception:
    # Fallback to scatter without trendline
    st.warning("Trendline calculation failed. Showing scatter plot.")
    fig = px.scatter(..., trendline=None)
```

**Best Practices**:
- ✅ Use trendlines with time-series or continuous numeric data
- ✅ Ensure sufficient data points (>10 recommended for meaningful trends)
- ⚠️ Avoid trendlines on heavily filtered categorical breakdowns
- ⚠️ Consider data variance before applying trendlines

### Other Statistical Edge Cases

#### 1. **Correlation Heatmaps with Constant Values**

**Issue**: `np.corrcoef()` fails with zero variance

**Handling**:
- Check for variance before computing correlations
- Filter out constant columns automatically
- Display informative message about excluded fields

#### 2. **Percentile Calculations on Small Datasets**

**Issue**: Insufficient data for meaningful percentiles

**Handling**:
- Minimum 10 values required for percentile operations
- Fallback to min/max if insufficient data
- Warning displayed to user

#### 3. **Z-Score Outlier Detection**

**Issue**: Zero standard deviation causes division by zero

**Handling**:
- Check `std > 0` before z-score calculation
- Skip outlier detection for constant fields
- Log warning about skipped fields

## Data Quality Edge Cases

### Missing Value Handling

**Strategies and Edge Cases**:

```yaml
data_quality:
  missing_values:
    strategy: auto  # Handles edge cases automatically
```

**Edge Case Matrix**:

| Data Type | % Missing | Strategy | Edge Case Handling |
|-----------|-----------|----------|-------------------|
| Numeric | <5% | `fill_mean` | Skip if all NaN |
| Numeric | >50% | `drop_column` | Warn about data loss |
| Categorical | Any | `fill_mode` | Use 'Unknown' if no mode |
| Datetime | Any | `drop_rows` | Validate after dropping |

### Outlier Detection Edge Cases

**Percentile Method**:
- Handles skewed distributions well
- Robust to extreme outliers
- Works with sparse data (>100 points recommended)

**Z-Score Method**:
- Assumes normal distribution
- Fails with zero variance → automatic fallback to percentile
- Sensitive to extreme outliers

**IQR Method**:
- Robust to outliers
- Works with small datasets (>20 points)
- May be too aggressive with multimodal distributions

**Isolation Forest**:
- Requires sklearn dependency
- Needs sufficient data (>100 points)
- Falls back to percentile if insufficient data

## Rendering Edge Cases

### Empty Datasets After Filtering

**Issue**: Filters eliminate all data

**Handling**:
```python
if len(df) == 0:
    st.info("No data matches current filters. Try adjusting filter criteria.")
    return
```

### Single Data Point

**Issue**: Cannot render meaningful visualizations

**Handling**:
- Scatter/Line: Show warning, render single point
- Histogram: Show warning, use single bar
- Statistics: Display the single value with context

### Extremely Large Datasets

**Issue**: Memory and performance problems

**Handling**:
```yaml
visualization:
  params:
    limit: 10000  # Sample to 10K points for performance
```

## Validation Policy Integration

### Strictness Levels

**Relaxed** (Production Default):
```yaml
validation_policy:
  strictness: relaxed  # Only critical/error violations
```
- Allows questionable configurations
- Minimal warnings
- Maximum flexibility

**Moderate** (Development Default):
```yaml
validation_policy:
  strictness: moderate  # Critical/error/warning violations
```
- Warns about questionable patterns
- Good balance for iterative development

**Strict** (CI/CD):
```yaml
validation_policy:
  strictness: strict  # All violations including info
```
- Catches all potential issues
- Best for automated validation

### Suppressing Specific Warnings

```yaml
validation_policy:
  strictness: moderate
  suppress_codes:
    - DQ_QUESTIONABLE_METHOD  # Allow outlier detection on temporal fields
    - MISSING_FIELD_LABEL     # Allow auto-generated labels
```

## Logging and Debugging

### Error Log Levels

**INFO**: Normal operations
```
INFO: Loaded 1,746,661 records from us_pollution.parquet
INFO: Applied 3 outlier capping rules
```

**WARNING**: Handled edge cases
```
WARNING: Trendline calculation failed for filtered data (n=2)
WARNING: Dropped column 'wind_chill' (>50% missing)
```

**ERROR**: Operation failed but dashboard continues
```
ERROR: Correlation heatmap failed: zero variance in fields ['state_code']
```

**CRITICAL**: Dashboard cannot render
```
CRITICAL: Data file not found: data/processed/missing.parquet
```

### Debug Mode

Enable verbose logging in development:

```python
# In streamlit_renderer.py
import logging
logging.basicConfig(level=logging.DEBUG)
```

Shows:
- Data transformation steps
- Filter operations
- Statistical calculations
- Rendering decisions

## Testing Edge Cases

### Unit Tests for Edge Cases

```python
# tests/test_edge_cases.py

def test_scatter_with_zero_variance():
    """Scatter plot should handle constant values gracefully"""
    df = pd.DataFrame({'x': [1, 1, 1], 'y': [1, 2, 3]})
    viz = {'chart_type': 'scatter', 'roles': {'x': 'x', 'y': 'y'},
           'params': {'trendline': 'ols'}}
    # Should not crash, should show warning
    render_scatter(df, viz, st)

def test_empty_filtered_data():
    """Empty data after filtering should show helpful message"""
    df = pd.DataFrame({'x': [], 'y': []})
    # Should display "No data matches filters" message
```

### Integration Tests

```python
def test_dashboard_with_extreme_filters():
    """Dashboard should handle extreme filtering gracefully"""
    # Apply filters that eliminate all data
    # Should show informative messages, not crash
```

## Best Practices Summary

### DO ✅

1. **Validate data variance** before statistical operations
2. **Provide fallback options** for failed calculations
3. **Show informative messages** explaining what happened
4. **Log warnings** for debugging without cluttering UI
5. **Test with edge case data** (empty, single point, constant values)
6. **Use validation policies** to control strictness
7. **Suppress handled warnings** to avoid user confusion

### DON'T ❌

1. **Don't crash** on edge cases - always fail gracefully
2. **Don't show raw tracebacks** - translate to user-friendly messages
3. **Don't ignore edge cases** - handle or log them
4. **Don't assume clean data** - always validate
5. **Don't use aggressive statistical methods** without checks
6. **Don't clutter logs** with expected warnings

## Future Enhancements

### Planned Improvements

1. **Auto-detect data issues** before visualization
2. **Suggest alternative visualizations** when current fails
3. **Smart sampling strategies** for large datasets
4. **Progressive rendering** for complex visualizations
5. **Data quality dashboard** showing preprocessing decisions
6. **A/B testing** for fallback strategies

### Open Issues

Track edge cases and improvements at: [GitHub Issues](https://github.com/your-org/dashspec/issues)

- [ ] Better handling of multimodal distributions
- [ ] Smarter trendline selection (polynomial vs linear)
- [ ] Automatic outlier method selection based on data characteristics
- [ ] Real-time data quality metrics in UI

## References

- [Plotly Express Documentation](https://plotly.com/python/plotly-express/)
- [Statsmodels OLS](https://www.statsmodels.org/stable/regression.html)
- [Pandas Missing Data](https://pandas.pydata.org/docs/user_guide/missing_data.html)
- [NumPy Error Handling](https://numpy.org/doc/stable/reference/routines.err.html)
