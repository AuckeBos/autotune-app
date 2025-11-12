# Stage 1: Build autotune from oref0
FROM node:20-slim AS autotune-builder

WORKDIR /tmp/build

# Clone oref0 repository and build autotune
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install ca-certificates so HTTPS works, clone oref0 and build with relaxed npm engine checks
RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates && rm -rf /var/lib/apt/lists/*

RUN git clone --depth 1 https://github.com/openaps/oref0.git . \
    && npm config set engine-strict false \
    && npm install --production --legacy-peer-deps --no-audit --no-fund \
    && rm -rf .git

# Stage 2: Python development environment (includes uv)
FROM ghcr.io/astral-sh/uv:python3.14-trixie-slim AS final

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    jq \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY . /app

# Install Python dependencies using uv
RUN uv sync

# Add virtual environment to PATH
ENV PATH="/app/.venv/bin:$PATH"

# Copy autotune from builder stage
COPY --from=autotune-builder /tmp/build /opt/autotune
ENV PATH="/opt/autotune/bin:$PATH"

# Create non-root user with fallback
RUN apt-get update && apt-get install -y --no-install-recommends passwd \
    && useradd -m -u 1000 appuser || echo "appuser:x:1000:1000:appuser:/home/appuser:/bin/bash" >> /etc/passwd \
    && chown -R appuser:appuser /app \
    && cat /etc/passwd | grep appuser

# Set working directory for app user
WORKDIR /app

USER appuser

# Default command: tail dev null
CMD ["tail", "-f", "/dev/null"]
