# GitHub Copilot Instructions for autotune-app

## Project Overview

**autotune-app** is a Python application that automates AAPS (AndroidAPS) profile generation using the autotune tool. The application loads historical data from Nightscout, runs autotune analysis to generate profile suggestions, and syncs updated profiles back to Nightscout.

## Technology Stack

- **Language**: Python 3.11+
- **Workflow Orchestration**: Prefect (for task orchestration and job scheduling)
- **Web Interface**: Streamlit (planned)
- **Data Source**: Nightscout API
- **Autotune Tool**: Based on OpenAPS oref0 autotune
- **Development Environment**: Dev Containers
- **Containerization**: Docker
- **Testing**: pytest (unit tests and integration tests)

## Project Architecture

The application follows a task-based architecture with Prefect flows:

1. **Load Data Task**: Retrieve historical data from Nightscout
2. **Run Autotune Task**: Execute autotune analysis on historical data
3. **Sync Profile Task**: Update Nightscout with suggested profile changes
4. **Streamlit UI**: User interface for triggering and monitoring autotune runs

## Core Development Principles

### Code Quality
- Write clean, maintainable, and well-documented Python code
- Follow PEP 8 style guidelines consistently
- Use type hints for all function signatures
- Write comprehensive docstrings following PEP 257 conventions
- Prioritize readability and clarity over cleverness

### Testing Strategy
- Write unit tests for all business logic
- Implement integration tests for API interactions (Nightscout, autotune)
- Use pytest fixtures for test setup and teardown
- Mock external dependencies in unit tests
- Aim for high test coverage (>80%)

### Security
- Never commit secrets or API keys to the repository
- Use environment variables for configuration
- Validate all external inputs (Nightscout data, user inputs)
- Follow OWASP security best practices
- Implement proper error handling without exposing sensitive information

### Development Workflow
- Use Dev Containers for consistent development environments
- Follow Git Flow branching strategy
- Write descriptive commit messages
- Keep pull requests focused and reviewable
- Run tests before committing

## File Organization

```
autotune-app/
├── .devcontainer/          # Dev container configuration
├── src/
│   ├── autotune_app/       # Main application package
│   │   ├── flows/          # Prefect flows
│   │   ├── tasks/          # Prefect tasks
│   │   ├── services/       # Business logic (Nightscout client, autotune runner)
│   │   ├── models/         # Data models (profiles, settings)
│   │   └── utils/          # Utility functions
│   └── streamlit_app/      # Streamlit web interface
├── tests/
│   ├── unit/               # Unit tests
│   └── integration/        # Integration tests
├── docker/                 # Docker configurations
├── docs/                   # Documentation
└── scripts/                # Utility scripts

```

## Coding Standards

### Python Style
- Use 4 spaces for indentation
- Maximum line length: 88 characters (Black formatter)
- Use descriptive variable and function names
- Prefer explicit over implicit
- Use f-strings for string formatting

### Error Handling
- Use specific exception types
- Provide meaningful error messages
- Log errors with appropriate context
- Implement retry logic for external API calls
- Fail fast and fail loudly in development

### Dependencies
- Pin dependency versions in requirements.txt
- Keep dependencies minimal and up-to-date
- Document why each major dependency is needed
- Regularly check for security vulnerabilities

## Prefect Best Practices
- Keep tasks focused and single-purpose
- Use task caching for expensive operations
- Implement proper retry strategies for external calls
- Use Prefect's logging instead of print statements
- Handle task failures gracefully

## Nightscout Integration
- Implement rate limiting to respect API constraints
- Cache data when appropriate to minimize API calls
- Validate API responses before processing
- Handle API errors and network failures gracefully
- Document expected data formats

## Streamlit Guidelines
- Keep the UI simple and intuitive
- Provide clear feedback for user actions
- Display progress for long-running operations
- Implement proper error handling and user notifications
- Use session state appropriately

## Documentation Requirements
- Maintain up-to-date README.md with setup instructions
- Document all configuration options
- Provide examples for common use cases
- Keep API documentation in sync with code
- Document any quirks or limitations

## References
- [Android AAPS Documentation](https://androidaps.readthedocs.io/en/latest/index.html)
- [OpenAPS Autotune](https://github.com/openaps/oref0/blob/master/bin/oref0-autotune.py)
- [Nightscout API Documentation](https://nightscout.github.io/)
- [Prefect Documentation](https://docs.prefect.io/)
- [Streamlit Documentation](https://docs.streamlit.io/)

## Related Instructions
- See [python.instructions.md](./instructions/python.instructions.md) for Python-specific guidelines
- See [testing.instructions.md](./instructions/testing.instructions.md) for testing standards
- See [prefect.instructions.md](./instructions/prefect.instructions.md) for Prefect workflow patterns
- See [security.instructions.md](./instructions/security.instructions.md) for security best practices
- See [containerization.instructions.md](./instructions/containerization.instructions.md) for Docker best practices
