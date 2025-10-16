FROM python:3.12.8-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY asset-service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY asset-service/ .

# Copy ALL shared modules
COPY shared/*.py ./

# Remove logging.py if it exists (it shadows Python's built-in logging module)
RUN rm -f /app/logging.py /app/logging_utils.py

# Expose port (will be overridden by docker-compose)
EXPOSE 3000

# Run the application
CMD ["python", "main.py"]
