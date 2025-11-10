# DSL Directory Restructuring Plan

## Goal
Separate general schema/DSL activities from Streamlit-specific rendering code to enable support for multiple visualization tools (e.g., Plotly, Matplotlib, D3.js, etc.).

## Current Structure (dsl/)
```
dsl/
├── adapter.py                 # Core DSL execution + validation
├── codegen.py                 # Code generation (Streamlit-specific?)
├── custom_renderers_template.py  # Streamlit template
├── data_loader.py             # General data loading
├── data_quality.py            # General DQ processing
├── formatting.py              # General formatting logic
├── streamlit_renderer.py      # Streamlit-specific renderer
├── viz_renderers.py           # Streamlit-specific viz renderers
├── schema*.json               # DSL schemas
├── examples/                  # Dashboard specs
├── design_card.yaml           # Example spec
├── validation_rules.yaml      # Validation rules
└── README.md
```

## Proposed Structure

```
dsl/
├── core/                      # General DSL logic (visualization-agnostic)
│   ├── __init__.py
│   ├── adapter.py             # Core DSL execution + validation
│   ├── data_loader.py         # Data loading
│   ├── data_quality.py        # DQ processing
│   ├── formatting.py          # Formatting logic
│   ├── schema_validator.py    # NEW: Schema validation logic
│   └── ir.py                  # NEW: Intermediate representation
│
├── renderers/                 # Visualization-specific renderers
│   ├── __init__.py
│   ├── base.py                # Base renderer interface
│   │
│   ├── streamlit/             # Streamlit implementation
│   │   ├── __init__.py
│   │   ├── renderer.py        # Main Streamlit renderer (streamlit_renderer.py)
│   │   ├── viz_renderers.py   # Streamlit viz renderers
│   │   ├── codegen.py         # Streamlit code generation
│   │   └── custom_renderers_template.py
│   │
│   └── plotly/                # Future: Plotly implementation
│       ├── __init__.py
│       ├── renderer.py
│       └── viz_renderers.py
│
├── schemas/                   # All schema files
│   ├── schema.json            # Current schema
│   ├── schema_v1.0.json
│   ├── schema_v1.1.json
│   ├── schema_v1.2.json
│   └── validation_rules.yaml
│
├── examples/                  # Dashboard specifications
│   └── *.yaml
│
├── README.md
└── design_card.yaml
```

## File Classification

### Core (Visualization-Agnostic)
- `adapter.py` - Core execution engine, validation logic
- `data_loader.py` - Data loading from Parquet/CSV
- `data_quality.py` - DQ rules processing
- `formatting.py` - Number/currency/date formatting

### Streamlit-Specific
- `streamlit_renderer.py` - Main Streamlit app renderer
- `viz_renderers.py` - Streamlit chart rendering
- `codegen.py` - Generates Streamlit code
- `custom_renderers_template.py` - Streamlit template

### Schemas
- All `schema*.json` files
- `validation_rules.yaml`

## Migration Steps

### 1. Create Directory Structure
```bash
mkdir -p dsl/core
mkdir -p dsl/renderers/streamlit
mkdir -p dsl/schemas
```

### 2. Move Core Files
```bash
mv dsl/adapter.py dsl/core/
mv dsl/data_loader.py dsl/core/
mv dsl/data_quality.py dsl/core/
mv dsl/formatting.py dsl/core/
```

### 3. Move Streamlit Files
```bash
mv dsl/streamlit_renderer.py dsl/renderers/streamlit/renderer.py
mv dsl/viz_renderers.py dsl/renderers/streamlit/
mv dsl/codegen.py dsl/renderers/streamlit/
mv dsl/custom_renderers_template.py dsl/renderers/streamlit/
```

### 4. Move Schema Files
```bash
mv dsl/schema*.json dsl/schemas/
mv dsl/validation_rules.yaml dsl/schemas/
```

### 5. Create __init__.py Files
- `dsl/core/__init__.py` - Export core classes
- `dsl/renderers/__init__.py` - Export base renderer
- `dsl/renderers/streamlit/__init__.py` - Export StreamlitRenderer

### 6. Update Imports
Files to update:
- `app.py` - Update StreamlitRenderer import
- `tests/test_dashboards_v12.py` - Update imports
- `run_dashboard.py` - Update imports
- All core files - Update cross-references
- All streamlit files - Update core imports

## Import Changes

### Before:
```python
from dsl.adapter import validate, to_intermediate_representation, execute
from dsl.streamlit_renderer import StreamlitRenderer
from dsl.data_loader import DataLoader
```

### After:
```python
from dsl.core.adapter import validate, to_intermediate_representation, execute
from dsl.renderers.streamlit import StreamlitRenderer
from dsl.core.data_loader import DataLoader
```

## Benefits

1. **Clear Separation of Concerns**: Core DSL logic separated from rendering
2. **Extensibility**: Easy to add new renderers (Plotly, Matplotlib, etc.)
3. **Testability**: Core logic can be tested independently
4. **Maintainability**: Related code grouped together
5. **Documentation**: Structure self-documents the architecture

## Future Renderers

With this structure, adding a new renderer is straightforward:

```python
# dsl/renderers/plotly/renderer.py
from dsl.core.adapter import to_intermediate_representation, execute
from dsl.renderers.base import BaseRenderer

class PlotlyRenderer(BaseRenderer):
    def render(self, spec_path: str):
        ir = to_intermediate_representation(spec_path)
        results = execute(ir, inputs={})
        # Render using Plotly...
```

## Backwards Compatibility

All public APIs remain accessible through `dsl/__init__.py` for backwards compatibility:

```python
# dsl/__init__.py
from dsl.core.adapter import validate, to_intermediate_representation, execute
from dsl.renderers.streamlit import StreamlitRenderer

__all__ = ['validate', 'to_intermediate_representation', 'execute', 'StreamlitRenderer']
```

## Testing Strategy

1. Run existing tests with updated imports
2. Verify all dashboards still render correctly
3. Verify app.py works with new structure
4. Add integration tests for base renderer interface

## Rollback Plan

If issues arise:
1. Git revert to previous commit
2. Or manually reverse file moves
3. Restore original import paths
