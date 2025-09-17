FROM nvidia/cuda:12.1.1-devel-ubuntu22.04

# Set non-interactive installation to avoid timezone prompts
ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=America/Los_Angeles

# Install Python 3.12 and system dependencies
RUN apt-get update && apt-get install -y \
    software-properties-common \
    tzdata \
    && ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone \
    && add-apt-repository ppa:deadsnakes/ppa \
    && apt-get update && apt-get install -y \
    python3.12 \
    python3.12-dev \
    python3.12-venv \
    python3-pip \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set Python 3.12 as default
RUN update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.12 1
RUN update-alternatives --install /usr/bin/python python /usr/bin/python3.12 1

# Install pip for Python 3.12
RUN curl -sS https://bootstrap.pypa.io/get-pip.py | python3.12

# Set CUDA environment variables
ENV CUDA_HOME=/usr/local/cuda
ENV PATH=${CUDA_HOME}/bin:${PATH}
ENV LD_LIBRARY_PATH=${CUDA_HOME}/lib64:${LD_LIBRARY_PATH}

WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies with CUDA support in stages to avoid OOM
RUN pip install --no-cache-dir torch torchvision --index-url https://download.pytorch.org/whl/cu121

# Install core dependencies first
RUN pip install --no-cache-dir fastapi==0.116.2 uvicorn==0.34.0 pydantic>=2.10.0 httpx==0.28.1

# Install remaining dependencies one by one to avoid OOM
RUN pip install --no-cache-dir python-multipart==0.0.20
RUN pip install --no-cache-dir structlog==24.4.0 requests==2.32.3
RUN pip install --no-cache-dir ollama==0.4.4
RUN pip install --no-cache-dir --only-binary=all "numpy>=1.26.0,<3.0"
RUN pip install --no-cache-dir asyncpg==0.30.0 redis==5.2.1 python-dotenv==1.0.1
RUN pip install --no-cache-dir --only-binary=all pandas>=2.2.0
RUN pip install --no-cache-dir --only-binary=all scikit-learn>=1.6.0
RUN pip install --no-cache-dir --only-binary=all scipy>=1.14.0
RUN pip install --no-cache-dir transformers>=4.47.0
RUN pip install --no-cache-dir accelerate>=1.2.0

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