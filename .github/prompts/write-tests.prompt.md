---
mode: 'agent'
model: 'Claude Sonnet 4.5'
tools: ['codebase', 'edit/editFiles', 'runCommands']
description: 'Generate unit tests for Python code using pytest'
---

# Generate Unit Tests

You are tasked with generating comprehensive unit tests for Python code using pytest.

## Requirements

When generating tests:

1. **Test Structure**
   - Create tests in the appropriate `tests/unit/` directory
   - Name test files with `test_` prefix
   - Use descriptive test function names starting with `test_`
   - Group related tests in test classes if appropriate

2. **Test Coverage**
   - Test happy path (normal execution)
   - Test edge cases (boundary conditions, empty inputs, None values)
   - Test error conditions (exceptions, invalid inputs)
   - Test different parameter combinations using `@pytest.mark.parametrize`

3. **Mocking**
   - Mock external dependencies (APIs, databases, file system)
   - Use `unittest.mock` for creating mocks
   - Verify mock calls when behavior is important
   - Use fixtures for reusable mocks

4. **Fixtures**
   - Create pytest fixtures for common test setup
   - Use appropriate fixture scopes (`function`, `class`, `module`)
   - Put shared fixtures in `conftest.py`
   - Clean up resources in fixtures using `yield`

5. **Assertions**
   - Use descriptive assertion messages
   - Test specific exceptions with `pytest.raises()`
   - Verify expected values and types
   - Check side effects when relevant

6. **Documentation**
   - Add docstrings explaining what each test verifies
   - Include examples of test data
   - Document any special setup or assumptions

## Example Test Structure

```python
import pytest
from unittest.mock import Mock, patch
from autotune_app.services.example import ExampleService


@pytest.fixture
def mock_api_client():
    """Fixture providing a mocked API client."""
    client = Mock()
    client.fetch_data.return_value = {"key": "value"}
    return client


@pytest.fixture
def sample_data():
    """Fixture providing sample test data."""
    return {
        "entries": [
            {"sgv": 120, "date": 1234567890000},
            {"sgv": 130, "date": 1234567900000}
        ]
    }


class TestExampleService:
    """Tests for ExampleService class."""
    
    def test_process_data_success(self, mock_api_client, sample_data):
        """Test successful data processing."""
        service = ExampleService(mock_api_client)
        result = service.process_data(sample_data)
        
        assert result is not None
        assert "processed" in result
        mock_api_client.fetch_data.assert_called_once()
    
    def test_process_data_empty_input(self, mock_api_client):
        """Test processing with empty input."""
        service = ExampleService(mock_api_client)
        result = service.process_data({"entries": []})
        
        assert result == {}
    
    def test_process_data_invalid_input_raises_error(self, mock_api_client):
        """Test that invalid input raises ValueError."""
        service = ExampleService(mock_api_client)
        
        with pytest.raises(ValueError, match="Invalid input"):
            service.process_data(None)
    
    @pytest.mark.parametrize(
        "sgv,expected",
        [
            (70, "low"),
            (100, "normal"),
            (180, "high"),
        ],
        ids=["low_bg", "normal_bg", "high_bg"]
    )
    def test_categorize_glucose(self, sgv, expected):
        """Test glucose categorization with various values."""
        result = ExampleService.categorize_glucose(sgv)
        assert result == expected
```

## Process

1. **Analyze the code** to be tested
2. **Identify test cases** (happy path, edge cases, errors)
3. **Create fixtures** for reusable test data and mocks
4. **Write tests** with clear names and documentation
5. **Run tests** to verify they pass
6. **Check coverage** to ensure comprehensive testing

## Deliverables

- Test file(s) in appropriate `tests/unit/` directory
- Fixtures in `conftest.py` if needed
- All tests passing when run with `pytest`
- Docstrings explaining what each test verifies
