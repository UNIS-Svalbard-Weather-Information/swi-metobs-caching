ARG PYTHON_VERSION=3.14
ARG APP_VERSION=3.X.X

# Stage 1: Dependency resolution
FROM astral/uv:python${PYTHON_VERSION}-bookworm-slim AS uv
WORKDIR /swi
COPY pyproject.toml .
RUN uv pip compile pyproject.toml > requirements.txt

# Stage 2: Build
FROM python:${PYTHON_VERSION}-slim AS builder
WORKDIR /swi
COPY --from=uv /swi/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Stage 3: Runtime
FROM python:${PYTHON_VERSION}-slim
ARG APP_VERSION
ARG PYTHON_VERSION
WORKDIR /swi

# Install Git and other dependencies
RUN apt-get update && \
    apt-get install -y git && \
    rm -rf /var/lib/apt/lists/*

# Copy only necessary files from the builder stage
COPY --from=builder /usr/local/lib/python${PYTHON_VERSION}/site-packages /usr/local/lib/python${PYTHON_VERSION}/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy the current directory to /swi
COPY . .

# Make the entrypoint scripts executable
RUN chmod +x /swi/entrypoint.sh /swi/run-cron.sh

# Use the entrypoint script - supports DOCKER_CRON=1 to stay alive between runs so an
# external scheduler can re-trigger the job via `docker exec <container> run-cron`
ENTRYPOINT ["./entrypoint.sh"]

