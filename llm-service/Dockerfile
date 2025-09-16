FROM python:3.12.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# CUDA will be available through the host GPU drivers and nvidia-docker runtime
# No need to install CUDA toolkit in the container

WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies with CUDA support in stages to avoid OOM
RUN pip install --no-cache-dir torch torchvision --index-url https://download.pytorch.org/whl/cu121

# Install core dependencies first
RUN pip install --no-cache-dir fastapi==0.104.1 uvicorn==0.24.0 pydantic>=2.8.0 httpx==0.25.2

# Install remaining dependencies one by one to avoid OOM
RUN pip install --no-cache-dir python-multipart==0.0.6
RUN pip install --no-cache-dir structlog==23.2.0 requests==2.31.0
RUN pip install --no-cache-dir ollama==0.1.7
RUN pip install --no-cache-dir --only-binary=all "numpy>=1.19.0,<2.0"
RUN pip install --no-cache-dir asyncpg==0.29.0 redis==5.0.1 python-dotenv==1.0.0
RUN pip install --no-cache-dir --only-binary=all pandas>=2.1.0
RUN pip install --no-cache-dir --only-binary=all scikit-learn>=1.3.0
RUN pip install --no-cache-dir --only-binary=all scipy>=1.11.0
RUN pip install --no-cache-dir transformers>=4.30.0
RUN pip install --no-cache-dir accelerate>=0.20.0

# Copy shared directory
COPY shared/ ./shared/

# Copy service code
COPY *.py ./

# Expose port
EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:3000/health || exit 1

# Run the service
CMD ["python", "main.py"]