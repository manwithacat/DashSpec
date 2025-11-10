# Validation Policy Design

## Problem Statement

Dashboard specifications may contain impractical or questionable requirements due to:
- Human error when writing YAML
- Copy-paste mistakes
- Lack of domain knowledge about what makes sense for certain field types
- Over-aggressive DQ rules that don't fit the data

Currently, validation is binary: specs either pass or fail. We need a more flexible approach that allows the generator/renderer to:
1. Warn about questionable configurations
2. Auto-correct minor issues
3. Gracefully degrade instead of failing completely

## Solution: Validation Policy

Add a `validation_policy` parameter to dashboard specs that controls how strictly requirements are enforced.

### Strictness Levels

```yaml
validation_policy:
  strictness: "relaxed"  # Options: "strict", "moderate", "relaxed"
  auto_correct: true     # Allow automatic corrections
  fail_on_warnings: false  # Treat warnings as errors
```

#### Strictness Levels Defined

1. **`strict`** (Default for production)
   - All violations are errors
   - No auto-correction
   - Spec must be perfect to render
   - Use case: Production dashboards, CI/CD validation

2. **`moderate`** (Recommended for development)
   - Critical violations → errors (missing fields, invalid references)
   - Questionable configurations → warnings (temporal outlier detection)
   - Minor issues → auto-corrected with warning logs
   - Use case: Interactive development, testing

3. **`relaxed`** (For rapid prototyping)
   - Only critical violations → errors
   - Everything else → warnings or auto-corrected
   - Maximum graceful degradation
   - Use case: Prototyping, experimentation, learning

### Violation Severity Levels

Introduce severity classification for violations:

```python
class ViolationSeverity:
    CRITICAL = "critical"    # Missing required field, invalid reference
    ERROR = "error"          # Schema violation, unsupported version
    WARNING = "warning"      # Questionable but functional (temporal outliers)
    INFO = "info"            # Suggestions for improvement
```

### Auto-Correction Rules

When `auto_correct: true`, the validator can fix issues:

| Issue | Auto-Correction |
|-------|----------------|
| Temporal field in outlier detection | Remove from DQ rules, log warning |
| Categorical field with percentile method | Switch to mode-based detection or skip |
| Missing field in DQ rule | Remove rule, log warning |
| Duplicate IDs | Auto-suffix with `_1`, `_2`, etc. |
| Invalid formatting precision | Clamp to valid range (0-10) |

### Implementation Strategy

#### 1. Schema Changes (v1.2)

Add optional `validation_policy` to top level:

```json
{
  "validation_policy": {
    "type": "object",
    "properties": {
      "strictness": {
        "type": "string",
        "enum": ["strict", "moderate", "relaxed"],
        "default": "moderate"
      },
      "auto_correct": {
        "type": "boolean",
        "default": false
      },
      "fail_on_warnings": {
        "type": "boolean",
        "default": false
      },
      "suppress_codes": {
        "type": "array",
        "items": {"type": "string"},
        "description": "Violation codes to suppress (e.g., ['DQ_QUESTIONABLE_METHOD'])"
      }
    }
  }
}
```

#### 2. Adapter Changes

Modify `validate()` function signature:

```python
def validate(
    model: dict,
    policy: dict = None,
    factors: dict = None
) -> tuple[list[Violation], dict]:
    """
    Returns:
        violations: List of violations
        corrections: Dict of auto-corrections applied
    """
```

Add violation severity:

```python
class Violation(TypedDict):
    code: str
    severity: str      # NEW: "critical", "error", "warning", "info"
    message: str
    path: str
    repair: str
    auto_correctable: bool  # NEW: Can this be auto-fixed?
```

#### 3. Validation Logic

```python
def validate(model: dict, policy: dict = None, factors: dict = None):
    # Extract policy
    validation_policy = model.get("validation_policy", {})
    strictness = validation_policy.get("strictness", "moderate")
    auto_correct = validation_policy.get("auto_correct", False)
    suppress_codes = set(validation_policy.get("suppress_codes", []))

    violations = []
    corrections = {}

    # ... collect violations with severity levels ...

    # Filter by strictness
    if strictness == "relaxed":
        # Only return critical/error violations
        violations = [v for v in violations if v["severity"] in ["critical", "error"]]
    elif strictness == "moderate":
        # Return all but filter warnings if not fail_on_warnings
        if not validation_policy.get("fail_on_warnings", False):
            violations = [v for v in violations if v["severity"] != "warning"]

    # Apply suppressions
    violations = [v for v in violations if v["code"] not in suppress_codes]

    # Auto-correct if enabled
    if auto_correct:
        violations, corrections = apply_auto_corrections(model, violations)

    return violations, corrections
```

### Example Usage

#### Strict Mode (Production)
```yaml
validation_policy:
  strictness: strict
  auto_correct: false
  fail_on_warnings: true
```

#### Moderate Mode (Development)
```yaml
validation_policy:
  strictness: moderate
  auto_correct: true
  fail_on_warnings: false
  suppress_codes:
    - DQ_QUESTIONABLE_METHOD  # Allow temporal outlier detection
```

#### Relaxed Mode (Prototyping)
```yaml
validation_policy:
  strictness: relaxed
  auto_correct: true
```

### Benefits

1. **Graceful Degradation**: Dashboards can render with warnings instead of failing completely
2. **Learning Friendly**: Beginners get helpful warnings without blocking
3. **Flexibility**: Expert users can suppress specific warnings they understand
4. **Auto-Repair**: Common mistakes get fixed automatically with clear logging
5. **CI/CD Ready**: Strict mode ensures production quality

### Migration Path

1. **Phase 1** (Current): Add severity levels to violations
2. **Phase 2**: Implement policy parsing and filtering
3. **Phase 3**: Add auto-correction rules
4. **Phase 4**: Update all dashboards to include policy (optional)
5. **Phase 5**: Update documentation and examples

### Testing Strategy

```python
def test_validation_strictness():
    """Test that strictness levels filter appropriately"""

    # Spec with temporal outlier detection
    spec = load_spec_with_temporal_outliers()

    # Strict mode - should fail
    violations, _ = validate(spec, {"strictness": "strict"})
    assert len(violations) > 0

    # Moderate mode - should warn but not fail
    violations, _ = validate(spec, {"strictness": "moderate"})
    assert all(v["severity"] != "warning" for v in violations)

    # Relaxed mode - should pass
    violations, _ = validate(spec, {"strictness": "relaxed"})
    assert all(v["severity"] in ["critical", "error"] for v in violations)
```

## Open Questions

1. Should auto-correction modify the original spec object or return a corrected copy?
2. How verbose should correction logging be in the UI?
3. Should we track correction history for debugging?
4. Default strictness level - moderate or strict?
