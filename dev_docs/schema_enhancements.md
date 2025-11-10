# Schema Enhancements for Safety and Usability

## Goals
1. Prevent common configuration mistakes
2. Add helpful constraints and defaults
3. Improve error messages with better context
4. Enable graceful degradation

## Proposed Enhancements

### 1. Metric Aggregation Validation
**Current**: Any string accepted for aggregation
**Enhanced**: Enum with supported operations

```json
"aggregation": {
  "type": "string",
  "enum": ["count", "count_unique", "sum", "mean", "median", "min", "max", "std"],
  "description": "Aggregation function to apply"
}
```

### 2. Filter Type Validation
**Current**: Any filter type accepted
**Enhanced**: Strict enum with proper defaults

```json
"type": {
  "type": "string",
  "enum": ["range", "slider", "select", "multiselect", "date_range"],
  "description": "Type of filter widget"
}
```

### 3. Layout Component Width Validation
**Current**: Loose string validation
**Enhanced**: Enum with standard grid sizes

```json
"width": {
  "type": "string",
  "enum": ["full", "half", "third", "quarter", "two-thirds"],
  "default": "full"
}
```

### 4. Chart Type Completeness
**Current**: All chart types implicitly supported
**Enhanced**: Explicitly list all supported types

```json
"chart_type": {
  "type": "string",
  "enum": [
    "histogram", "ecdf", "boxplot", "violin", "kde",
    "scatter", "hexbin", "kde2d",
    "line", "bar", "heatmap", "pie",
    "table", "corr_heatmap", "summary"
  ]
}
```

### 5. DQ Method Validation
**Current**: Any method string
**Enhanced**: Enum with supported methods

```json
"method": {
  "type": "string",
  "enum": ["percentile", "zscore", "iqr", "isolation_forest"],
  "default": "percentile"
}
```

### 6. DQ Action Validation
**Current**: Any action string
**Enhanced**: Enum with supported actions

```json
"action": {
  "type": "string",
  "enum": ["cap", "remove", "flag"],
  "default": "cap"
}
```

### 7. Missing Value Strategy
**Current**: Any strategy string
**Enhanced**: Enum with clear options

```json
"strategy": {
  "type": "string",
  "enum": ["auto", "drop_rows", "fill_mean", "fill_median", "fill_mode", "fill_forward", "fill_value"],
  "default": "auto"
}
```

### 8. Formatting Type Constraints
**Current**: Basic string
**Enhanced**: Enum with precision validation

```json
"type": {
  "type": "string",
  "enum": ["integer", "number", "currency", "percent"]
},
"precision": {
  "type": "integer",
  "minimum": 0,
  "maximum": 10,
  "default": 2
}
```

### 9. Page Layout Type
**Current**: Loose validation
**Enhanced**: Strict enum

```json
"type": {
  "type": "string",
  "enum": ["single", "grid", "tabs"],
  "default": "single"
}
```

### 10. Metadata Currency Code
**Current**: Just a string
**Enhanced**: ISO 4217 pattern

```json
"currency": {
  "type": "string",
  "pattern": "^[A-Z]{3}$",
  "description": "ISO 4217 currency code (e.g., USD, EUR, GBP)"
}
```

## Implementation Priority

### High Priority (Prevent Errors)
1. ✅ Chart type enum - prevents unknown charts
2. ✅ Aggregation enum - prevents typos
3. ✅ Filter type enum - prevents invalid filters
4. ✅ DQ method/action enums - prevents DQ errors

### Medium Priority (Improve UX)
5. Layout width enum
6. Formatting type + precision constraints
7. Missing value strategy enum

### Low Priority (Nice to Have)
8. Currency code pattern
9. Component type enum
10. Additional field validations

## Benefits

1. **Early Error Detection**: Catch typos at spec validation time
2. **Better Error Messages**: JSON schema gives clear "expected X, got Y" messages
3. **IDE Support**: Enums enable autocomplete in YAML editors
4. **Documentation**: Schema serves as API documentation
5. **Type Safety**: Prevents runtime errors from invalid values

## Backwards Compatibility

All enhancements are additive and backwards compatible with existing v1.2 specs.
