# Autotune App

Automated AAPS (AndroidAPS) profile generation using the autotune tool.

## Overview

**autotune-app** is a Python application that automates AAPS profile generation by:

1. Loading historical data from Nightscout
2. Running autotune analysis to generate profile suggestions
3. Syncing updated profiles back to Nightscout

The application uses Prefect for workflow orchestration and can be extended with a Streamlit web interface.

## Technology Stack

- **Language**: Python 3.11+
- **Workflow Orchestration**: Prefect 2.x
- **Autotune Tool**: OpenAPS oref0 autotune
- **Data Source**: Nightscout API
- **Development Environment**: Dev Containers + Docker
- **Testing**: pytest
- **Package Manager**: uv

## Quick Start with Dev Containers

### Prerequisites

- Docker and Docker Compose installed
- Visual Studio Code with Dev Containers extension
- Git

### Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd autotune-app
   ```

2. **Configure environment variables**
   ```bash
   cp .env.local.example .env.local
   # Edit .env.local with your Nightscout URL and API secret
   ```

3. **Open in Dev Container**
   - Open the project folder in VS Code
   - Press `Ctrl+Shift+P` (or `Cmd+Shift+P` on macOS)
   - Select "Dev Containers: Reopen in Container"
   - VS Code will build and start the development environment

The dev environment includes:
- Python 3.11 with all dependencies installed via `uv`
- Prefect server running in a separate container
- Autotune tool from OpenAPS oref0
- pytest for testing
- VS Code extensions for Python development, Docker, and Prefect

### Running the Application

Once the dev container is running:

```bash
# Run Prefect flows
prefect flow run <flow-name>

# Run tests
pytest

# Format code
black src/

# Lint code
ruff check src/

# Check types
mypy src/
```

### Accessing Prefect UI

Open your browser and navigate to `http://localhost:4200` to access the Prefect UI dashboard.

## Project Structure

```
autotune-app/
├── .devcontainer/              # Dev container configuration
│   └── devcontainer.json       # VS Code dev container setup
├── src/
│   └── autotune_app/           # Main application package
│       ├── flows/              # Prefect flows
│       ├── tasks/              # Prefect tasks
│       ├── services/           # Business logic (API clients, etc.)
│       ├── models/             # Data models
│       └── utils/              # Utility functions
├── tests/
│   ├── unit/                   # Unit tests
│   └── integration/            # Integration tests
├── docker/                     # Docker configurations
├── Dockerfile                  # Development image
├── docker-compose.yml          # Multi-container setup
├── pyproject.toml              # Python project config
└── README.md                   # This file
```

## Development Workflow

### Writing Code

The dev container includes automatic code formatting with Black and linting with Ruff. Code is formatted on save.

### Running Tests

```bash
# Run all tests
pytest

# Run tests with coverage
pytest --cov=autotune_app --cov-report=html

# Run specific test file
pytest tests/unit/test_services.py

# Run tests matching a pattern
pytest -k "test_nightscout"
```

### Creating Prefect Flows

See [Prefect Guidelines](.github/instructions/prefect.instructions.md) for detailed flow development guidelines.

Example task:
```python
from prefect import task, get_run_logger

@task(
    name="load-data",
    retries=3,
    retry_delay_seconds=60
)
def load_nightscout_data(url: str, api_secret: str) -> dict:
    """Load Nightscout data."""
    logger = get_run_logger()
    logger.info(f"Loading data from {url}")
    # Implementation here
    return data
```

## Configuration

### Environment Variables

Create a `.env.local` file in the project root (use `.env.local.example` as a template):

```bash
# Prefect Configuration
PREFECT_API_URL=http://prefect-server:4200/api

# Nightscout Configuration
NIGHTSCOUT_URL=https://your-site.herokuapp.com
NIGHTSCOUT_API_SECRET=your-api-secret-here

# Application Configuration
LOG_LEVEL=DEBUG
```

**Security Note**: Never commit `.env.local` or any file containing secrets to version control.

## API Documentation

### Nightscout Integration

The application communicates with Nightscout API to:
- Fetch historical glucose entries
- Retrieve treatment data
- Read/update profiles

[Nightscout API Documentation](https://nightscout.github.io/)

### Autotune Tool

The autotune tool analyzes glucose data and suggests profile adjustments.

[OpenAPS Autotune Documentation](https://github.com/openaps/oref0/blob/master/bin/oref0-autotune.py)

## Testing

### Unit Tests

Unit tests are located in `tests/unit/` and test individual functions and components in isolation.

```bash
pytest tests/unit/
```

### Integration Tests

Integration tests are located in `tests/integration/` and test interactions between components.

```bash
pytest tests/integration/
```

### Test Coverage

View coverage report:
```bash
pytest --cov=autotune_app --cov-report=html
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
```

## Troubleshooting

### Dev Container Won't Start

1. Ensure Docker daemon is running
2. Check Docker resources (CPU, memory)
3. View container logs: `docker logs autotune-dev`

### Prefect Server Connection Error

1. Ensure Prefect server container is running: `docker ps`
2. Check Prefect server logs: `docker logs prefect-server`
3. Verify `PREFECT_API_URL` is set to `http://prefect-server:4200/api`

### Python Module Import Errors

1. Ensure dependencies are installed: `uv pip install -e .`
2. Check Python path: `python -c "import sys; print(sys.path)"`
3. Reinstall dev container: `Dev Containers: Rebuild Container`

## Contributing

Please follow the guidelines in:
- [Python Coding Standards](.github/instructions/python.instructions.md)
- [Testing Standards](.github/instructions/testing.instructions.md)
- [Prefect Guidelines](.github/instructions/prefect.instructions.md)
- [Security Best Practices](.github/instructions/security.instructions.md)

## References

- [Android AAPS Documentation](https://androidaps.readthedocs.io/en/latest/index.html)
- [OpenAPS Autotune](https://github.com/openaps/oref0)
- [Nightscout Documentation](https://nightscout.github.io/)
- [Prefect Documentation](https://docs.prefect.io/)
- [Python Best Practices](https://peps.python.org/pep-0008/)

## License

[Add your license information here]

## Support

For issues or questions:
1. Check existing documentation in `.github/instructions/`
2. Review Prefect and Nightscout documentation
3. Create an issue in the repository
