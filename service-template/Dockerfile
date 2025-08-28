FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN addgroup --gid 1001 --system python
RUN adduser --system --uid 1001 --gid 1001 python

# Change ownership of the app directory
RUN chown -R python:python /app
USER python

# Expose port (change if your service uses a different port)
EXPOSE 3010

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:3010/health || exit 1

# Start the application
CMD ["python", "main.py"]