# Use Python 3.11 slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY pyproject.toml ./
COPY src/ ./src/
COPY api_server.py ./

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    SETUPTOOLS_SCM_PRETEND_VERSION=1.0.0 pip install --no-cache-dir -e .

# Create directory for cookie persistence
RUN mkdir -p /app/gemini_cookies

# Expose port
EXPOSE 50014

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:50014/health')" || exit 1

# Run the application
CMD ["python", "api_server.py"]
