FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    libpq-dev \
    libkrb5-dev \
    libssl-dev \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY executor-service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code first
COPY executor-service .

# Copy shared modules (this will not overwrite the app files)
COPY shared ./shared

# Create non-root user
RUN addgroup --gid 1001 --system python
RUN adduser --system --uid 1001 --gid 1001 python

# Change ownership of the app directory
RUN chown -R python:python /app
USER python

# Set Python path to include /app
ENV PYTHONPATH=/app

# Expose port
EXPOSE 3007

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:3007/health || exit 1

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "3007"]