---
applyTo: '**/*.md,**/docs/**/*'
description: 'Documentation standards for autotune-app'
---

# Documentation Standards

## Overview

Clear and comprehensive documentation is essential for this project. Documentation helps users understand how to use the application, helps developers understand the codebase, and serves as a reference for the project's architecture and design decisions.

## Documentation Types

### README.md
- **Purpose**: Primary entry point for understanding the project
- **Location**: Root directory
- **Content**: Project overview, setup instructions, usage examples, configuration
- **Audience**: New users and developers

### API Documentation
- **Purpose**: Document public APIs and interfaces
- **Format**: Docstrings in code, generated with Sphinx or similar
- **Content**: Function signatures, parameters, return values, examples
- **Audience**: Developers using the API

### Architecture Documentation
- **Purpose**: Explain system design and architecture decisions
- **Location**: `docs/architecture/` directory
- **Content**: System diagrams, component descriptions, data flow
- **Audience**: Developers and architects

### User Guides
- **Purpose**: Help users accomplish specific tasks
- **Location**: `docs/user-guide/` directory
- **Content**: Step-by-step instructions, screenshots, examples
- **Audience**: End users

## Docstring Standards

### Function Docstrings
Use Google-style docstrings for all public functions.

Example:
```python
def run_autotune_analysis(
    nightscout_data: Dict[str, Any],
    profile: Dict[str, Any],
    days: int = 7
) -> Dict[str, Any]:
    """
    Run autotune analysis on Nightscout data.
    
    This function processes historical glucose and insulin data from Nightscout
    to generate suggested adjustments to the AAPS profile using the autotune
    algorithm.
    
    Args:
        nightscout_data: Dictionary containing entries and treatments from Nightscout
            Expected keys: 'entries' (list of glucose readings), 
            'treatments' (list of insulin/carb entries)
        profile: Current AAPS profile to analyze
            Expected keys: 'basal', 'carbratio', 'sens'
        days: Number of days of data to include in analysis (default: 7)
            Valid range: 1-30 days
    
    Returns:
        Dictionary containing autotune results with suggested profile adjustments:
            {
                'basalprofile': [...],  # Suggested basal rates
                'carb_ratio': [...],    # Suggested carb ratios
                'sens': [...]           # Suggested sensitivity factors
            }
    
    Raises:
        ValueError: If nightscout_data is empty or invalid
        AutotuneError: If autotune execution fails
    
    Example:
        >>> data = load_nightscout_data("https://mysite.herokuapp.com", "secret")
        >>> profile = load_profile("https://mysite.herokuapp.com", "secret")
        >>> results = run_autotune_analysis(data, profile, days=7)
        >>> print(results['basalprofile'])
        [{'time': '00:00', 'value': 1.05}, ...]
    
    Note:
        Requires at least 3 days of data for reliable results.
        Results should be reviewed before applying to actual therapy.
    """
    # Implementation
    pass
```

### Class Docstrings
Document classes with purpose, attributes, and usage examples.

Example:
```python
class NightscoutClient:
    """
    Client for interacting with Nightscout API.
    
    This class provides methods for fetching profiles, entries, and treatments
    from a Nightscout instance. It handles authentication, rate limiting, and
    error handling.
    
    Attributes:
        url: Nightscout URL (e.g., "https://mysite.herokuapp.com")
        api_secret: API secret for authentication
        timeout: Request timeout in seconds (default: 30)
    
    Example:
        >>> client = NightscoutClient(
        ...     url="https://mysite.herokuapp.com",
        ...     api_secret="my-secret"
        ... )
        >>> profile = client.fetch_profile()
        >>> entries = client.fetch_entries(days=7)
    
    Note:
        API secret should be stored securely in environment variables,
        not hardcoded in source code.
    """
    
    def __init__(self, url: str, api_secret: str, timeout: int = 30):
        """
        Initialize Nightscout client.
        
        Args:
            url: Nightscout URL
            api_secret: API secret for authentication
            timeout: Request timeout in seconds
        
        Raises:
            ValueError: If URL is invalid or empty
        """
        pass
```

### Module Docstrings
Document modules at the top of each file.

Example:
```python
"""
Nightscout API client module.

This module provides functionality for interacting with the Nightscout API,
including authentication, data fetching, and error handling.

Classes:
    NightscoutClient: Main client class for API interactions
    NightscoutError: Base exception for Nightscout-related errors

Functions:
    validate_nightscout_url: Validate Nightscout URL format

Example:
    >>> from autotune_app.services.nightscout_client import NightscoutClient
    >>> client = NightscoutClient(url, api_secret)
    >>> data = client.fetch_entries(days=7)
"""
```

## README.md Structure

The README should follow this structure:

```markdown
# Project Name

Brief description (1-2 sentences)

## Features

- Feature 1
- Feature 2
- Feature 3

## Prerequisites

- Python 3.11+
- Docker (for containerized deployment)
- Nightscout account and API secret

## Installation

### Local Development

Step-by-step installation instructions

### Docker

Docker-specific instructions

### Dev Container

Dev container setup instructions

## Configuration

List of required environment variables and their purposes

## Usage

### Basic Usage

Simple usage examples

### Advanced Usage

More complex scenarios

## Development

Instructions for developers

### Running Tests

How to run tests

### Code Style

Code formatting and style guidelines

## Deployment

Deployment instructions

## Troubleshooting

Common issues and solutions

## Contributing

Contribution guidelines

## License

License information

## References

Links to related documentation
```

## Inline Comments

### When to Comment
- Explain **why**, not **what** (the code shows what)
- Document non-obvious logic or algorithms
- Explain business rules or domain knowledge
- Note workarounds or temporary solutions
- Reference tickets or issues

### When NOT to Comment
- Don't explain obvious code
- Don't repeat function names
- Don't comment out code (use version control)
- Don't add noise comments

Example:
```python
# GOOD: Explains why
# Use SHA-1 hash for Nightscout authentication (required by API)
api_secret_hash = hashlib.sha1(api_secret.encode()).hexdigest()

# Retry with exponential backoff to handle transient API failures
for attempt in range(max_retries):
    try:
        return fetch_data()
    except requests.HTTPError:
        sleep(2 ** attempt)

# BAD: States the obvious
# Increment counter by 1
counter = counter + 1

# BAD: Commented out code
# old_implementation()
new_implementation()
```

## Architecture Documentation

### System Overview
Document the high-level architecture with diagrams.

Example structure:
```markdown
# Architecture Overview

## System Components

### Data Layer
- Nightscout API client
- Data validation
- Caching

### Processing Layer
- Prefect workflows
- Autotune runner
- Profile generator

### Presentation Layer
- Streamlit UI
- API endpoints

## Data Flow

[Diagram showing data flow through system]

## Key Design Decisions

### Decision: Use Prefect for Orchestration
Rationale: ...
Alternatives considered: ...
Trade-offs: ...
```

## Configuration Documentation

Document all configuration options clearly.

Example:
```markdown
## Configuration

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `NIGHTSCOUT_URL` | Yes | - | URL of your Nightscout instance |
| `NIGHTSCOUT_API_SECRET` | Yes | - | API secret for authentication |
| `PREFECT_API_URL` | No | `http://localhost:4200/api` | Prefect server URL |
| `LOG_LEVEL` | No | `INFO` | Logging level (DEBUG, INFO, WARNING, ERROR) |
| `AUTOTUNE_DAYS` | No | `7` | Days of data to analyze (1-30) |

### Example Configuration

Create a `.env` file in the project root:

```env
NIGHTSCOUT_URL=https://mysite.herokuapp.com
NIGHTSCOUT_API_SECRET=your-secret-here
LOG_LEVEL=INFO
```
```

## API Documentation Generation

Use Sphinx or similar tools to generate API documentation from docstrings.

Example `docs/conf.py`:
```python
# Sphinx configuration
project = 'autotune-app'
author = 'Your Name'
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',
    'sphinx.ext.viewcode',
]
napoleon_google_docstring = True
```

## Changelog

Maintain a CHANGELOG.md following Keep a Changelog format.

Example:
```markdown
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added
- Initial Streamlit UI for profile management

### Changed
- Improved error handling in Nightscout client

### Fixed
- Fixed timezone handling in autotune analysis

## [0.2.0] - 2024-01-15

### Added
- Prefect workflow for autotune execution
- Integration tests for Nightscout API

### Changed
- Upgraded to Python 3.11
- Improved Docker image efficiency

## [0.1.0] - 2024-01-01

### Added
- Initial release
- Basic autotune functionality
- Nightscout integration
```

## Documentation Maintenance

### Keeping Documentation Current
- Update documentation with code changes
- Review documentation in pull requests
- Run documentation builds in CI/CD
- Mark outdated documentation clearly

### Documentation Testing
- Test code examples in documentation
- Verify links are not broken
- Ensure screenshots are current
- Run spell check

## Anti-Patterns to Avoid

- ❌ Writing documentation after the fact
- ❌ Copying code into documentation (use includes or references)
- ❌ Not updating documentation when code changes
- ❌ Writing documentation only for yourself
- ❌ Assuming knowledge about domain or technology
- ❌ Using jargon without explanation
- ❌ Not providing examples
- ❌ Documentation without context

## Tools and Resources

### Documentation Generators
- Sphinx - Python documentation generator
- MkDocs - Markdown-based documentation
- pdoc - Simple API documentation

### Diagram Tools
- Mermaid - Text-based diagrams in Markdown
- Draw.io - Visual diagram editor
- PlantUML - Text-based UML diagrams

### Writing Tools
- Grammarly - Grammar and spelling
- Hemingway Editor - Readability
- Vale - Style linting

## References

- [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html)
- [Write the Docs](https://www.writethedocs.org/)
- [Keep a Changelog](https://keepachangelog.com/)
- [Semantic Versioning](https://semver.org/)
