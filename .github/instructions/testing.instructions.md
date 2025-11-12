---
applyTo: '**/test_*.py,**/*_test.py,**/tests/**/*.py'
description: 'Testing standards and best practices for autotune-app'
---

# Testing Standards and Best Practices

## Overview

This project uses pytest for unit tests and integration tests. All code should be thoroughly tested with a focus on reliability, maintainability, and coverage.

## Test Organization

### Directory Structure
```
tests/
├── unit/                    # Unit tests (isolated, fast)
│   ├── test_services/       # Service layer tests
│   ├── test_tasks/          # Prefect task tests
│   └── test_utils/          # Utility function tests
├── integration/             # Integration tests (external dependencies)
│   ├── test_nightscout/     # Nightscout API integration tests
│   └── test_flows/          # End-to-end flow tests
├── conftest.py              # Shared fixtures
└── fixtures/                # Test data and mock responses
```

### File Naming
- Test files must start with `test_` or end with `_test.py`
- Test functions must start with `test_`
- Test classes must start with `Test`
- Use descriptive names that explain what is being tested

## Test Writing Guidelines

### Unit Tests
- Test one function or method at a time
- Mock all external dependencies (APIs, databases, file system)
- Keep tests fast (under 100ms per test)
- Test both success and failure scenarios
- Test edge cases (empty inputs, None values, large datasets)
- Use fixtures for common test setup

### Integration Tests
- Test interactions between components
- Use real or test instances of external services when possible
- Mark slow tests with `@pytest.mark.slow`
- Clean up test data after tests run
- Use environment variables for test configuration
- Can be slower but should still complete in reasonable time

## Pytest Best Practices

### Fixtures
- Use fixtures for reusable test setup and teardown
- Use appropriate fixture scopes: `function`, `class`, `module`, `session`
- Prefer factory fixtures over parameterized fixtures for complex scenarios
- Clean up resources in fixtures using `yield` and cleanup code

Example:
```python
import pytest
from unittest.mock import Mock
from autotune_app.services.nightscout_client import NightscoutClient


@pytest.fixture
def mock_nightscout_client():
    """Fixture providing a mocked Nightscout client."""
    client = Mock(spec=NightscoutClient)
    client.fetch_profile.return_value = {
        "basal": [{"time": "00:00", "value": 1.0}],
        "carbratio": [{"time": "00:00", "value": 10}],
        "sens": [{"time": "00:00", "value": 50}]
    }
    return client


@pytest.fixture
def sample_nightscout_data():
    """Fixture providing sample Nightscout data for testing."""
    return {
        "entries": [
            {"sgv": 120, "date": 1234567890000, "type": "sgv"},
            {"sgv": 130, "date": 1234567900000, "type": "sgv"}
        ],
        "treatments": [
            {"insulin": 5.0, "timestamp": "2024-01-01T12:00:00Z"}
        ]
    }
```

### Mocking
- Use `unittest.mock` for mocking external dependencies
- Mock at the boundary (API calls, file I/O, network requests)
- Verify mock calls when behavior is important
- Use `patch` decorator for replacing modules or functions
- Use `Mock` or `MagicMock` for creating mock objects

Example:
```python
from unittest.mock import patch, Mock
import pytest
import requests


def test_fetch_profile_with_mocked_requests(mock_nightscout_client):
    """Test fetching profile with mocked HTTP requests."""
    with patch('requests.get') as mock_get:
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"profile": "data"}
        mock_get.return_value = mock_response
        
        result = mock_nightscout_client.fetch_profile()
        
        assert result is not None
        mock_get.assert_called_once()
```

### Assertions
- Use descriptive assertion messages
- Prefer specific assertions over generic `assert`
- Use pytest's rich assertion rewriting
- Test for exceptions using `pytest.raises()`

Example:
```python
def test_invalid_url_raises_error():
    """Test that invalid URL raises ValueError."""
    with pytest.raises(ValueError, match="Invalid Nightscout URL"):
        fetch_nightscout_profile("not-a-url", "secret")


def test_profile_has_required_fields(sample_profile):
    """Test that profile contains all required fields."""
    assert "basal" in sample_profile, "Profile missing basal field"
    assert "carbratio" in sample_profile, "Profile missing carbratio field"
    assert "sens" in sample_profile, "Profile missing sens field"
```

### Parametrization
- Use `@pytest.mark.parametrize` for testing multiple inputs
- Keep parametrized tests readable with descriptive IDs
- Use indirect parametrization for complex fixtures

Example:
```python
@pytest.mark.parametrize(
    "sgv,expected_category",
    [
        (70, "low"),
        (100, "normal"),
        (180, "high"),
        (300, "very_high")
    ],
    ids=["low_bg", "normal_bg", "high_bg", "very_high_bg"]
)
def test_glucose_categorization(sgv, expected_category):
    """Test glucose value categorization."""
    assert categorize_glucose(sgv) == expected_category
```

## Testing Prefect Workflows

### Testing Tasks
- Test tasks as regular Python functions
- Mock external dependencies and Prefect context
- Test retry logic and error handling
- Verify task results and side effects

Example:
```python
from autotune_app.tasks.load_data import load_nightscout_data
from unittest.mock import patch


def test_load_nightscout_data_task(mock_nightscout_client, sample_nightscout_data):
    """Test loading Nightscout data task."""
    with patch('autotune_app.tasks.load_data.NightscoutClient') as mock_client_class:
        mock_client_class.return_value = mock_nightscout_client
        
        result = load_nightscout_data("https://mysite.herokuapp.com", "secret")
        
        assert result is not None
        assert "entries" in result
        mock_nightscout_client.fetch_entries.assert_called_once()
```

### Testing Flows
- Test flows end-to-end with integration tests
- Use Prefect's testing utilities
- Mock expensive operations (autotune execution)
- Verify flow state and task results

## Testing External APIs

### Nightscout API
- Mock HTTP responses using `responses` or `requests-mock` library
- Test both success and error responses
- Test rate limiting and retry logic
- Use recorded responses for realistic testing (VCR.py)

Example:
```python
import responses
import pytest


@responses.activate
def test_nightscout_api_error_handling():
    """Test handling of Nightscout API errors."""
    responses.add(
        responses.GET,
        "https://mysite.herokuapp.com/api/v1/profile",
        json={"error": "Unauthorized"},
        status=401
    )
    
    with pytest.raises(requests.HTTPError):
        client = NightscoutClient("https://mysite.herokuapp.com", "wrong-secret")
        client.fetch_profile()
```

## Test Coverage

### Coverage Goals
- Maintain minimum 80% code coverage
- Focus on critical paths and business logic
- Don't sacrifice quality for coverage metrics
- Use coverage reports to identify untested code

### Running Coverage
```bash
# Run tests with coverage
pytest --cov=autotune_app --cov-report=html --cov-report=term

# View HTML coverage report
open htmlcov/index.html
```

## Test Markers

Use pytest markers to categorize tests:
- `@pytest.mark.slow` - Integration tests or slow tests
- `@pytest.mark.unit` - Unit tests
- `@pytest.mark.integration` - Integration tests
- `@pytest.mark.skip` - Temporarily skip tests
- `@pytest.mark.xfail` - Expected failures

Example:
```python
@pytest.mark.slow
@pytest.mark.integration
def test_full_autotune_workflow():
    """Test complete autotune workflow (slow integration test)."""
    # Full workflow test
    pass
```

## Test Data Management

### Fixtures Directory
- Store test data in `tests/fixtures/` directory
- Use JSON files for API responses
- Use CSV files for sample datasets
- Keep test data minimal and realistic

### Loading Test Data
```python
import json
from pathlib import Path


def load_fixture(filename: str) -> dict:
    """Load test fixture from JSON file."""
    fixture_path = Path(__file__).parent / "fixtures" / filename
    with open(fixture_path) as f:
        return json.load(f)


@pytest.fixture
def sample_autotune_result():
    """Load sample autotune result from fixture."""
    return load_fixture("autotune_result.json")
```

## Continuous Integration

- All tests must pass before merging
- Run tests automatically on push and pull requests
- Run fast unit tests on every commit
- Run full test suite including integration tests on pull requests
- Fail builds on test failures or coverage drops

## Anti-Patterns to Avoid

- ❌ Testing implementation details instead of behavior
- ❌ Writing tests that depend on execution order
- ❌ Not cleaning up test data or resources
- ❌ Using sleep() instead of proper waiting mechanisms
- ❌ Testing multiple things in one test
- ❌ Not testing error conditions
- ❌ Committing failing or skipped tests without explanation
- ❌ Writing tests that are slower than the code being tested
