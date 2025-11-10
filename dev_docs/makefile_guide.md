# Makefile Guide

This project includes a comprehensive Makefile to streamline development workflows.

## Quick Start

```bash
# See all available commands
make help

# Get project information
make info

# Complete setup for development
make setup
```

## Command Categories

### Setup & Installation

```bash
make install        # Install production dependencies only
make install-dev    # Install development dependencies (includes production)
make setup          # Complete setup: install-dev + create directories
```

### Code Quality

The project uses multiple tools to maintain code quality:

- **black**: Code formatter (line length: 100)
- **isort**: Import sorter (compatible with black)
- **flake8**: Linter for style issues
- **pylint**: Advanced linter for code quality
- **mypy**: Static type checker

```bash
make format         # Auto-format code with black and isort
make lint           # Run flake8 and pylint
make typecheck      # Run mypy type checking
make check          # Run all: format + lint + typecheck
```

**Configuration Files:**
- `.flake8` - Flake8 configuration
- `.pylintrc` - Pylint configuration
- `pyproject.toml` - Black, isort, mypy, pytest configuration

### Testing

```bash
make test           # Run DSL system tests
make test-pytest    # Run pytest tests (if available)
make test-cov       # Run tests with coverage report
```

### ETL Pipeline

```bash
# Process all datasets
make etl

# Process specific dataset
make etl-dataset DATASET=credit_card_fraud

# List processed datasets
make inspect

# Inspect specific dataset
make inspect-dataset DATASET=credit_card_fraud
```

### Dashboard

```bash
# Launch pre-configured dashboards
make dashboard           # Fraud detection dashboard (happy_path.yaml)
make dashboard-minimal   # Minimal example dashboard

# Launch custom dashboard
make dashboard-custom SPEC=my_dashboard.yaml
```

### Cleaning

```bash
make clean          # Remove Python cache files (__pycache__, *.pyc, etc.)
make clean-data     # Remove all data (with 5-second confirmation)
make clean-all      # Clean everything (cache + data)
```

### Development

```bash
make dev            # Setup development environment and show commands
make watch          # Watch for file changes and auto-run tests
```

### Git

```bash
make git-status     # Show git status and potential .gitignore items
```

### Information

```bash
make info           # Show:
                    # - Python/pip versions
                    # - Installed packages
                    # - Data status (raw/processed/metadata counts)
```

## Examples

### Setting up a new development environment

```bash
# Clone repository
git clone <repo-url>
cd Essentials

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Complete setup
make setup

# Verify installation
make info
```

### Daily development workflow

```bash
# Activate virtual environment
source .venv/bin/activate

# Format and check code before committing
make check

# Run tests
make test

# Check git status
make git-status
```

### Running ETL and Dashboard

```bash
# Process all datasets
make etl

# View processed data
make inspect

# Launch dashboard
make dashboard
```

### Code quality workflow

```bash
# 1. Format code
make format

# 2. Check for issues
make lint

# 3. Type check
make typecheck

# Or all at once:
make check
```

## Customizing the Makefile

### Adding new commands

Edit the `Makefile` and follow this pattern:

```makefile
##@ Category Name

my-command: ## Description of command
	@echo "$(BLUE)Doing something...$(NC)"
	# Your commands here
	@echo "$(GREEN)✓ Done$(NC)"
```

### Using variables

The Makefile defines several useful variables:

- `$(PYTHON_VENV)` - Python in virtual environment
- `$(PIP)` - Pip in virtual environment
- `$(SRC_DIRS)` - Source directories for linting

### Color codes

- `$(BLUE)` - Blue text
- `$(GREEN)` - Green text (success)
- `$(YELLOW)` - Yellow text (warning)
- `$(RED)` - Red text (error)
- `$(NC)` - No color (reset)

## Troubleshooting

### Command not found

Ensure the virtual environment is activated:
```bash
source .venv/bin/activate
```

Or use absolute paths defined in the Makefile (already handled).

### Permission denied

Make sure the Makefile is in the project root and you have execute permissions on scripts.

### Tool not installed

Run `make install-dev` to ensure all development tools are installed:
```bash
make install-dev
```

### Data not found

If ETL hasn't been run yet:
```bash
make etl
```

Or for a specific dataset:
```bash
make etl-dataset DATASET=credit_card_fraud
```

## CI/CD Integration

The Makefile is designed to work in CI/CD pipelines:

```yaml
# Example GitHub Actions workflow
- name: Install dependencies
  run: make install-dev

- name: Run quality checks
  run: make check

- name: Run tests
  run: make test
```

## Best Practices

1. **Always format before committing**: `make format`
2. **Run checks before pushing**: `make check`
3. **Keep dependencies updated**: Review `requirements*.txt` regularly
4. **Use `make clean` periodically**: Remove cache files to avoid issues
5. **Document new commands**: Add `##` comments for help text

## Related Files

- `requirements.txt` - Production dependencies
- `requirements-dev.txt` - Development dependencies
- `pyproject.toml` - Tool configurations
- `.flake8` - Flake8 configuration
- `.pylintrc` - Pylint configuration
- `.gitignore` - Ignored files (includes `.venv`, `__pycache__`, etc.)
