# --- Build Stage ---
FROM python:3.12-slim-bookworm AS builder

# 1. Grab the uv binary from the official image
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/

# 2. Configure uv to use the container's Python interpreter
ENV UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1 \
    UV_PYTHON_DOWNLOADS=never \
    UV_NO_MANAGED_PYTHON=1

WORKDIR /app

# 3. Create the virtual environment using uv
RUN uv venv /app/.venv

# 4. Copy only requirements first to optimize Docker layer caching
COPY requirements.txt .

# 5. Install dependencies into the venv using uv pip
RUN uv pip install --project /app/.venv -r requirements.txt


# --- Runtime Stage ---
FROM python:3.12-slim-bookworm AS runtime

WORKDIR /app

# 6. Copy the pre-built virtual environment from the builder
COPY --from=builder /app/.venv /app/.venv

# 7. Copy your actual application source code
COPY . .

# 8. Add the virtual environment to the system PATH
# This means you don't need 'uv run' or to activate it; 'python' defaults to the venv
ENV PATH="/app/.venv/bin:$PATH"

# 9. Security: Run as a non-root user
RUN adduser --disabled-password --gecos "" appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

# Call fastapi dev for development (adjust for production if needed)
CMD ["fastapi", "dev", "app/main.py", "--host", "0.0.0.0"]
