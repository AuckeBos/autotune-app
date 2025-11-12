<!-- Based on: https://github.com/github/awesome-copilot/blob/main/instructions/python.instructions.md -->
---
applyTo: '**/*.py'
description: 'Python coding conventions and guidelines for autotune-app'
---

# Python Coding Conventions

## Python Instructions

- Package manager: uv
- Write clear and concise comments for each function.
- Ensure functions have descriptive names and include type hints.
- Provide docstrings following PEP 257 conventions.
- For typing, prefer types like `list`  and `dict` over the Typing module where possible (e.g., `list[str]` instead of `List[str]` in Python 3.9+).
- Break down complex functions into smaller, more manageable functions.

## General Instructions

- Always prioritize readability and clarity.
- For algorithm-related code, include explanations of the approach used.
- Write code with good maintainability practices, including comments on why certain design decisions were made.
- Handle edge cases and write clear exception handling.
- For libraries or external dependencies, mention their usage and purpose in comments.
- Use consistent naming conventions and follow language-specific best practices.
- Write concise, efficient, and idiomatic code that is also easily understandable.

## Code Style and Formatting

- Use Ruff as formatter. Strict: all default rules enabled. Including line length.
- Maintain proper indentation (use 4 spaces for each level of indentation).
- Place function and class docstrings immediately after the `def` or `class` keyword.
- Use blank lines to separate functions, classes, and code blocks where appropriate.

## Type Hints

- Use type hints for all function parameters and return values.
- Use `|None` for parameters that can be None.
- Use `|` when a parameter can be multiple types.
- For complex types, consider using TypedDict or Pydantic.
- Import types from `typing` module: `List`, `Dict`, `Set`, `Tuple`, `Optional`, `Union`, etc. Only when needed.
- Use Pydantic BaseModel, never dataclasses.

## Error Handling

- Use specific exception types rather than generic `Exception`.
- Provide meaningful error messages that help with debugging.
- Use try-except blocks for operations that may fail (API calls, file I/O, etc.).
- Log errors with appropriate context using Prefect's logging or Python's logging module.
- Implement retry logic for transient failures (network errors, API rate limits).
- Document expected exceptions in docstrings.

## Asynchronous Code

- Use `async`/`await` for I/O-bound operations (API calls, database queries).
- Use `asyncio.gather()` for concurrent operations.
- Handle exceptions in async code with try-except in async functions.
- Use async context managers (`async with`) when appropriate.
- Avoid blocking calls in async functions.

## Testing

- Write unit tests for all public functions.
- Use pytest fixtures for test setup and teardown.
- Mock external dependencies (APIs, databases) in unit tests.
- Use descriptive test names that explain what is being tested.
- Include edge cases and error scenarios in tests.
- Aim for high test coverage (>80%).

## Documentation

- Write comprehensive docstrings for all public functions and classes.
- Include parameter descriptions, return value descriptions, and examples in docstrings.
- Use Google-style or NumPy-style docstring format.
- Keep README.md updated with project setup and usage instructions.
- Document configuration options and environment variables.

## Edge Cases and Testing

- Always include test cases for critical paths of the application.
- Account for common edge cases like empty inputs, invalid data types, and large datasets.
- Include comments for edge cases and the expected behavior in those cases.
- Write unit tests for functions and document them with docstrings explaining the test cases.

## Example of Proper Documentation

```python
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


def fetch_nightscout_profile(
    url: str,
    api_secret: str,
    profile_name: Optional[str] = None
) -> Dict[str, Any]:
    """
    Fetch a profile from Nightscout API.
    
    Parameters:
        url (str): The Nightscout URL.
        api_secret (str): The API secret for authentication.
        profile_name (Optional[str]): The name of the profile to fetch. 
            If None, fetches the default profile.
    
    Returns:
        Dict[str, Any]: The profile data from Nightscout.
    
    Raises:
        ValueError: If the URL is invalid or empty.
        requests.HTTPError: If the API request fails.
    
    Example:
        >>> profile = fetch_nightscout_profile(
        ...     "https://mysite.herokuapp.com",
        ...     "my-api-secret",
        ...     "Default"
        ... )
        >>> print(profile['basal'])
    """
    if not url or not url.startswith('http'):
        raise ValueError(f"Invalid Nightscout URL: {url}")
    
    logger.info(f"Fetching profile from Nightscout: {url}")
    
    # Implementation here
    ...
```

## Prefered libraries
- Pydantic for data models and validation
- Ruff for formatting
- Prefect for scheduling
- Requests for HTTP calls
- Pytest for testing
- Pydantic settings for configuration management
- uv as package manager, use pyproject.toml

## Project-Specific Guidelines

### Prefect Tasks and Flows
- Keep tasks focused on a single responsibility.
- Use task decorators with appropriate settings (retries, cache_key_fn).
- Use Prefect's logging instead of print statements.
- Return structured data from tasks (dataclasses or TypedDicts).
- Handle task failures gracefully with try-except.

### Nightscout API Interactions
- Always validate API responses before processing.
- Implement rate limiting to respect API constraints.
- Use exponential backoff for retries.
- Cache data when appropriate to minimize API calls.
- Log API calls with relevant context (URL, parameters, response status).

### Configuration Management
- Use environment variables for sensitive configuration (API keys, URLs). Pydantic settings
- Provide default values for optional configuration.
- Validate configuration on application startup.
- Use pydantic for configuration validation when possible.
- Document all configuration options in README.

## Anti-Patterns to Avoid

- ❌ Using `print()` instead of proper logging
- ❌ Catching generic `Exception` without re-raising
- ❌ Hardcoding URLs, API keys, or other configuration
- ❌ Not using type hints
- ❌ Writing functions longer than 50 lines
- ❌ Not handling None values explicitly
- ❌ Using mutable default arguments
- ❌ Not cleaning up resources (files, connections)
