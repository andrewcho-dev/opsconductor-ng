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
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install Ollama
RUN curl -fsSL https://ollama.ai/install.sh | sh

# Copy requirements and install Python dependencies (EXACT WORKING ORDER)
COPY requirements.txt .

# Install PyTorch with CUDA support FIRST
RUN pip install --no-cache-dir torch torchvision --index-url https://download.pytorch.org/whl/cu121

# 1. Core web framework
RUN pip install --no-cache-dir fastapi==0.104.1 uvicorn==0.24.0 pydantic>=2.8.0 httpx==0.25.2 aiohttp==3.9.1

# 2. Basic utilities
RUN pip install --no-cache-dir python-multipart==0.0.6
RUN pip install --no-cache-dir structlog==23.2.0 requests==2.31.0
RUN pip install --no-cache-dir ollama==0.1.7
RUN pip install --no-cache-dir psutil>=5.9.0

# 3. NumPy with binary wheels (CRITICAL: --only-binary=all)
RUN pip install --no-cache-dir --only-binary=all "numpy>=1.19.0,<2.0"

# 4. Database/cache
RUN pip install --no-cache-dir asyncpg==0.29.0 redis==5.0.1 python-dotenv==1.0.0

# 5. ML packages with binary wheels (CRITICAL: --only-binary=all AND newer versions)
RUN pip install --no-cache-dir --only-binary=all pandas>=2.1.0
RUN pip install --no-cache-dir --only-binary=all scikit-learn>=1.3.0
RUN pip install --no-cache-dir --only-binary=all scipy>=1.11.0

# 6. NLP dependencies (compatible versions)
RUN pip install --no-cache-dir "numpy>=1.26.0,<2.0.0"
RUN pip install --no-cache-dir "spacy>=3.7.0,<3.8.0"
RUN python -m spacy download en_core_web_sm

# 7. Other dependencies
RUN pip install --no-cache-dir regex==2023.10.3
RUN pip install --no-cache-dir "chromadb>=1.1.0"
RUN pip install --no-cache-dir "ollama>=0.2.0"
RUN pip install --no-cache-dir setuptools wheel
RUN pip install --no-cache-dir sentence-transformers>=3.0.0
RUN pip install --no-cache-dir transformers>=4.30.0

# 8. Prefect workflow orchestration
RUN pip install --no-cache-dir "prefect>=3.0.0"
RUN pip install --no-cache-dir "prefect-docker>=0.4.0"

# Copy shared utilities
COPY shared/ ./shared/

# Copy application code
COPY . .

# Create startup script
RUN echo '#!/bin/bash\n\
echo "Starting OpsConductor AI Service..."\n\
echo "Using external Ollama service at $OLLAMA_HOST"\n\
\n\
# Wait for external Ollama service to be ready\n\
echo "Waiting for external Ollama service to be ready..."\n\
until curl -f $OLLAMA_HOST/api/tags > /dev/null 2>&1; do\n\
    echo "Waiting for Ollama service..."\n\
    sleep 5\n\
done\n\
\n\
echo "Ollama service is ready!"\n\
echo "Starting FastAPI application..."\n\
\n\
# Start the application\n\
uvicorn main:app --host 0.0.0.0 --port 3005' > /app/start.sh

RUN chmod +x /app/start.sh

# Expose ports
EXPOSE 3005

# Run the startup script
CMD ["/app/start.sh"]