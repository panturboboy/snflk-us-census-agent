# Test Suite

Tests are organized by type and scope:

## Directory Structure

```
tests/
├── unit/           # Unit tests (fast, no external dependencies)
├── integration/    # Integration tests (require Snowflake/Cortex)
├── e2e/           # End-to-end tests (full application flow)
├── conftest.py    # Shared pytest fixtures and configuration
└── README.md      # This file
```

## Running Tests

### All tests:
```bash
pytest
```

### By type:
```bash
pytest tests/unit/              # Unit tests only
pytest tests/integration/       # Integration tests only
pytest tests/e2e/              # E2E tests only
```

### By marker:
```bash
pytest -m unit                 # Fast tests
pytest -m integration          # Medium speed (requires Snowflake)
pytest -m e2e                  # Full application tests
pytest -m slow                 # Tests with API calls
```

### With output:
```bash
pytest -v                      # Verbose
pytest -v --tb=short          # Verbose with short traceback
pytest -s                      # Show print statements
```

## Test Categories

### Unit Tests (`unit/`)
- Fast, no external dependencies
- Test individual functions/classes in isolation
- Run locally without Snowflake
- Examples: config validation, sanitization functions

### Integration Tests (`integration/`)
- Require Snowflake and Cortex Analyst connection
- Test API integration and queries
- Run in CI/CD with real Snowflake account
- Examples:
  - `test_cortex_api.py` - Cortex Analyst REST API
  - `test_cortex.py` - Query execution
  - `test_context_preservation.py` - Multi-turn conversations

### E2E Tests (`e2e/`)
- Full application flow testing
- Require all services running
- Test user scenarios end-to-end
- Examples:
  - `test_context_with_data.py` - Multi-turn with data summaries
  - `test_smoke.py` - Deployment smoke tests

## Environment Setup

Tests require these environment variables:
```bash
SNOWFLAKE_ACCOUNT
SNOWFLAKE_USER
SNOWFLAKE_PASSWORD
SNOWFLAKE_DATABASE
SNOWFLAKE_SCHEMA
SNOWFLAKE_WAREHOUSE
CORTEX_ANALYST_TOKEN
```

Set them in `.env` file or export them.

## CI/CD Integration

GitHub Actions runs:
1. **Unit tests** (fast, always run)
2. **Integration tests** (if unit tests pass)
3. **Smoke tests** (after deployment)

See `.github/workflows/deploy.yml` for details.

## Adding New Tests

1. Choose category (unit/integration/e2e)
2. Create `test_*.py` file in appropriate directory
3. Use `@pytest.mark.unit`, `@pytest.mark.integration`, or `@pytest.mark.e2e`
4. Import fixtures from `conftest.py`

Example:
```python
import pytest

@pytest.mark.unit
def test_sanitize_content():
    from src.cortex_analyst import sanitize_content
    result = sanitize_content("Test **bold** text")
    assert "**" not in result
```

## Fixtures

Available pytest fixtures from `conftest.py`:

- `snowflake_config` - Snowflake connection config dict
- `cortex_token` - Cortex Analyst API token
- `cortex_analyst` - CortexAnalyst class

Example usage:
```python
def test_cortex_connection(cortex_analyst, cortex_token):
    assert cortex_token is not None
    analyst = cortex_analyst
    assert analyst.API_TOKEN == cortex_token
```

## Test Coverage

To generate coverage report:
```bash
pytest --cov=src --cov-report=html
open htmlcov/index.html
```

Current coverage target: 80%+ for `src/` modules
