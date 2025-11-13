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
├── .github/
│   ├── copilot-instructions.md # GitHub Copilot guidelines
│   └── instructions/           # Detailed development guidelines
├── src/
│   └── app/                    # Main application package
│       ├── clients/            # Low-level API clients
│       │   ├── nightscout_client.py  # Nightscout API wrapper
│       │   └── autotune_client.py    # Autotune CLI wrapper
│       ├── models/             # Pydantic data models
│       │   ├── nightscout.py   # Nightscout data structures
│       │   └── autotune.py     # Autotune data structures
│       └── services/           # High-level service layer
│           ├── nightscout_service.py # Nightscout service
│           └── autotune_service.py   # Autotune service
├── tests/
│   └── unit/                   # Unit tests
│       ├── test_nightscout_client.py
│       ├── test_autotune_client.py
│       ├── test_nightscout_service.py
│       └── test_autotune_service.py
├── docs/
│   └── IMPLEMENTATION.md       # Implementation documentation
├── docker/                     # Docker configurations
│   ├── Dockerfile              # Development image
│   └── docker-compose.yml      # Multi-container setup
├── pyproject.toml              # Python project config
└── README.md                   # This file
```

## Implementation Status

✅ **Completed**:
- Nightscout API client with profile, entries, and treatments endpoints
- Autotune CLI wrapper for running autotune analysis
- Pydantic models for type-safe data validation
- Service layer with user-friendly interfaces
- Comprehensive unit tests for all components

🚧 **In Progress**:
- Prefect flows and tasks (coming next)
- Streamlit web interface (planned)
- Integration tests (planned)

See [docs/IMPLEMENTATION.md](docs/IMPLEMENTATION.md) for detailed implementation documentation.

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

### Using the Clients and Services

The application provides two layers of interaction:

1. **Clients** (low-level): Direct API/CLI interaction
2. **Services** (high-level): Validated, user-friendly wrappers

Example using services:
```python
from app.services.nightscout_service import NightscoutService
from app.services.autotune_service import AutotuneService

# Load data from Nightscout
ns_service = NightscoutService("https://mysite.herokuapp.com", "api-secret")
profile_store = ns_service.get_profile_store("Default")
historical_data = ns_service.get_historical_data(days=7)

# Run autotune analysis
at_service = AutotuneService()
recommendations = at_service.run_analysis(
    profile_store, 
    historical_data, 
    "Default", 
    days=7
)

# Apply recommendations and sync back
updated_profile = at_service.apply_recommendations(profile_store, recommendations)
ns_service.sync_profile(updated_profile, "Default")
```

See [docs/IMPLEMENTATION.md](docs/IMPLEMENTATION.md) for more examples and detailed API documentation.

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
