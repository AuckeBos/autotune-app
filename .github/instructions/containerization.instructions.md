<!-- Based on: https://github.com/github/awesome-copilot/blob/main/instructions/containerization-docker-best-practices.instructions.md -->
---
applyTo: '**/Dockerfile,**/Dockerfile.*,**/*.dockerfile,**/docker-compose*.yml,**/docker-compose*.yaml'
description: 'Docker and containerization best practices for autotune-app'
---

# Containerization & Docker Best Practices

## Core Principles

### 1. Immutability
- Build new images for every code change
- Never modify running containers
- Use semantic versioning for image tags
- Treat images as immutable artifacts

### 2. Small and Efficient Images
- Use minimal base images (alpine, slim)
- Implement multi-stage builds
- Remove unnecessary files and dependencies
- Combine RUN commands to reduce layers

### 3. Security
- Run containers as non-root user
- Scan images for vulnerabilities
- Don't include secrets in images
- Keep base images updated

### 4. Portability
- Use environment variables for configuration
- Avoid hardcoded values
- Document all required environment variables
- Test on multiple platforms if needed

## Dockerfile Best Practices

### Multi-Stage Builds
Always use multi-stage builds to separate build dependencies from runtime dependencies.

Example:
```dockerfile
# Stage 1: Build stage
FROM python:3.11-slim AS builder

WORKDIR /app

# Install build dependencies
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# Stage 2: Runtime stage
FROM python:3.11-slim

WORKDIR /app

# Create non-root user
RUN useradd -m -u 1000 appuser

# Copy only necessary artifacts from builder
COPY --from=builder /root/.local /home/appuser/.local
COPY --chown=appuser:appuser . .

# Make sure scripts are in PATH
ENV PATH=/home/appuser/.local/bin:$PATH

# Switch to non-root user
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD python -c "import sys; sys.exit(0)"

# Run application
CMD ["python", "-m", "autotune_app"]
```

### Choose Minimal Base Images
- Prefer `python:3.11-slim` over `python:3.11`
- Use `alpine` variants for even smaller images
- Always specify exact version tags (never use `latest`)
- Update base images regularly for security patches

### Optimize Layer Caching
- Copy dependency files before source code
- Combine related RUN commands
- Order instructions from least to most frequently changing
- Clean up in the same RUN command that creates artifacts

Example:
```dockerfile
# GOOD: Optimized layer caching
FROM python:3.11-slim

WORKDIR /app

# Copy dependency files first (changes less frequently)
COPY requirements.txt .

# Install dependencies (will be cached if requirements.txt doesn't change)
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code (changes more frequently)
COPY . .

# BAD: Copying everything first
# COPY . .
# RUN pip install -r requirements.txt
```

### Use .dockerignore
Create a comprehensive `.dockerignore` file to exclude unnecessary files.

Example `.dockerignore`:
```dockerignore
# Version control
.git
.gitignore
.gitattributes

# Python
__pycache__
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
ENV/
.venv

# Testing
.pytest_cache
.coverage
htmlcov/
.tox/

# IDE
.vscode
.idea
*.swp
*.swo

# Documentation
*.md
docs/
!README.md

# CI/CD
.github/
.gitlab-ci.yml

# Development files
.env
.env.local
*.log

# OS files
.DS_Store
Thumbs.db
```

### Security Best Practices

#### Non-Root User
Always run containers as a non-root user.

```dockerfile
# Create dedicated user
RUN useradd -m -u 1000 appuser

# Set ownership of application files
RUN chown -R appuser:appuser /app

# Switch to non-root user
USER appuser
```

#### No Secrets in Images
Never include secrets in Docker images.

```dockerfile
# BAD: Secret in image
# ENV API_SECRET="my-secret-123"

# GOOD: Use runtime secrets
# Secrets should be provided via environment variables at runtime
# or mounted as files
```

#### Health Checks
Define health checks for container monitoring.

```dockerfile
# Simple health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD python -c "import sys; sys.exit(0)" || exit 1

# HTTP health check (if running web service)
HEALTHCHECK --interval=30s --timeout=3s --retries=3 \
  CMD curl --fail http://localhost:8080/health || exit 1
```

## Docker Compose Best Practices

### Development Configuration
Use docker-compose for local development.

Example `docker-compose.yml`:
```yaml
version: '3.8'

services:
  autotune-app:
    build:
      context: .
      dockerfile: Dockerfile
      target: development
    volumes:
      # Mount source code for live reloading
      - ./src:/app/src:ro
      # Mount tests for development
      - ./tests:/app/tests:ro
    environment:
      - NIGHTSCOUT_URL=${NIGHTSCOUT_URL}
      - NIGHTSCOUT_API_SECRET=${NIGHTSCOUT_API_SECRET}
      - PREFECT_API_URL=${PREFECT_API_URL}
      - LOG_LEVEL=DEBUG
    env_file:
      - .env
    ports:
      - "8501:8501"  # Streamlit
    depends_on:
      - prefect-server
    networks:
      - autotune-network

  prefect-server:
    image: prefecthq/prefect:2-latest
    ports:
      - "4200:4200"
    environment:
      - PREFECT_API_DATABASE_CONNECTION_URL=sqlite+aiosqlite:////data/prefect.db
    volumes:
      - prefect-data:/data
    networks:
      - autotune-network

volumes:
  prefect-data:

networks:
  autotune-network:
    driver: bridge
```

### Production Configuration
Separate production configuration from development.

Example `docker-compose.prod.yml`:
```yaml
version: '3.8'

services:
  autotune-app:
    image: autotune-app:${VERSION:-latest}
    restart: unless-stopped
    environment:
      - NIGHTSCOUT_URL=${NIGHTSCOUT_URL}
      - NIGHTSCOUT_API_SECRET=${NIGHTSCOUT_API_SECRET}
      - PREFECT_API_URL=${PREFECT_API_URL}
      - LOG_LEVEL=INFO
    # No volume mounts in production
    # No exposed ports (use reverse proxy)
    networks:
      - autotune-network
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 512M
        reservations:
          cpus: '0.5'
          memory: 256M

networks:
  autotune-network:
    driver: bridge
```

## Container Runtime Best Practices

### Resource Limits
Always set resource limits for containers.

```yaml
deploy:
  resources:
    limits:
      cpus: '1.0'
      memory: 512M
    reservations:
      cpus: '0.25'
      memory: 256M
```

### Environment Variables
Use environment variables for configuration.

```dockerfile
# Set default values
ENV LOG_LEVEL=INFO
ENV PREFECT_API_URL=http://prefect-server:4200/api

# Override at runtime:
# docker run -e LOG_LEVEL=DEBUG myapp
```

### Logging
Configure logging to stdout/stderr for container log collection.

```python
import logging
import sys

# Configure logging to stdout
logging.basicConfig(
    stream=sys.stdout,
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

## Dev Container for Development

Use Dev Containers for consistent development environment.

Example `.devcontainer/devcontainer.json`:
```json
{
  "name": "Autotune App Dev",
  "dockerComposeFile": "../docker-compose.yml",
  "service": "autotune-app",
  "workspaceFolder": "/app",
  "customizations": {
    "vscode": {
      "extensions": [
        "ms-python.python",
        "ms-python.vscode-pylance",
        "ms-python.black-formatter",
        "ms-azuretools.vscode-docker"
      ],
      "settings": {
        "python.defaultInterpreterPath": "/usr/local/bin/python",
        "python.linting.enabled": true,
        "python.linting.pylintEnabled": true,
        "python.formatting.provider": "black",
        "editor.formatOnSave": true
      }
    }
  },
  "postCreateCommand": "pip install -e .[dev]",
  "remoteUser": "appuser"
}
```

## Image Scanning and Security

### Scan Images for Vulnerabilities
Use tools like Trivy or Snyk to scan images.

```bash
# Scan image with Trivy
docker build -t autotune-app:latest .
trivy image autotune-app:latest

# Scan with Snyk
snyk container test autotune-app:latest
```

### CI/CD Integration
Integrate security scanning in your CI/CD pipeline.

```yaml
# GitHub Actions example
- name: Build Docker image
  run: docker build -t autotune-app:${{ github.sha }} .

- name: Scan image for vulnerabilities
  run: |
    docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
      aquasec/trivy image autotune-app:${{ github.sha }}
```

## Dockerfile Review Checklist

- [ ] Uses multi-stage build
- [ ] Uses minimal, specific base image (e.g., `python:3.11-slim`)
- [ ] Layers are optimized (combined RUN commands, cleanup in same layer)
- [ ] `.dockerignore` file is present and comprehensive
- [ ] Non-root USER is defined
- [ ] EXPOSE instruction documents ports
- [ ] CMD or ENTRYPOINT is defined correctly
- [ ] Environment variables used for configuration
- [ ] HEALTHCHECK instruction is defined
- [ ] No secrets in image layers
- [ ] Image has been scanned for vulnerabilities
- [ ] Build is reproducible (pinned versions)

## Common Pitfalls to Avoid

- ❌ Using `latest` tag in production
- ❌ Running containers as root
- ❌ Including secrets in images
- ❌ Not using `.dockerignore`
- ❌ Installing unnecessary packages
- ❌ Not combining RUN commands
- ❌ Not defining resource limits
- ❌ Not implementing health checks
- ❌ Copying entire project with `COPY . .` without `.dockerignore`
- ❌ Not scanning images for vulnerabilities

## References

- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)
- [Dockerfile Best Practices](https://docs.docker.com/develop/develop-images/dockerfile_best-practices/)
- [Docker Security](https://docs.docker.com/engine/security/)
- [Trivy - Vulnerability Scanner](https://github.com/aquasecurity/trivy)
