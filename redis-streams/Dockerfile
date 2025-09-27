FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY redis-streams/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY redis-streams/processor.py .
COPY shared /app/shared

# Create non-root user
RUN useradd -m -u 1000 processor && chown -R processor:processor /app
USER processor

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import redis; r=redis.from_url('redis://redis-streams:6379/0'); r.ping()" || exit 1

CMD ["python", "processor.py"]