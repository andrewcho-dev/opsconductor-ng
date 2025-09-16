FROM python:3.12.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive

WORKDIR /app

# Install system dependencies (EXACT WORKING VERSIONS)
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Ollama
RUN curl -fsSL https://ollama.ai/install.sh | sh

# Copy requirements and install Python dependencies (EXACT WORKING ORDER)
COPY requirements.txt .

# 1. Core web framework
RUN pip install --no-cache-dir fastapi==0.104.1 uvicorn==0.24.0 pydantic>=2.8.0 httpx==0.25.2

# 2. Basic utilities
RUN pip install --no-cache-dir python-multipart==0.0.6
RUN pip install --no-cache-dir structlog==23.2.0 requests==2.31.0
RUN pip install --no-cache-dir ollama==0.1.7

# 3. NumPy with binary wheels (CRITICAL: --only-binary=all)
RUN pip install --no-cache-dir --only-binary=all "numpy>=1.19.0,<2.0"

# 4. Database/cache
RUN pip install --no-cache-dir asyncpg==0.29.0 redis==5.0.1 python-dotenv==1.0.0

# 5. ML packages with binary wheels (CRITICAL: --only-binary=all AND newer versions)
RUN pip install --no-cache-dir --only-binary=all pandas>=2.1.0
RUN pip install --no-cache-dir --only-binary=all scikit-learn>=1.3.0
RUN pip install --no-cache-dir --only-binary=all scipy>=1.11.0

# 6. Other dependencies
RUN pip install --no-cache-dir regex==2023.10.3
RUN pip install --no-cache-dir chromadb==0.5.0
RUN pip install --no-cache-dir sentence-transformers==2.2.2

# Copy shared utilities
COPY shared/ ./shared/

# Copy application code
COPY . .

# Create startup script that handles GPU detection
RUN echo '#!/bin/bash\n\
echo "Starting OpsConductor AI Service..."\n\
\n\
# Check for GPU availability\n\
if nvidia-smi > /dev/null 2>&1; then\n\
    echo "GPU detected! Starting Ollama with GPU support..."\n\
    export OLLAMA_GPU=1\n\
else\n\
    echo "No GPU detected. Starting Ollama in CPU mode..."\n\
    export OLLAMA_GPU=0\n\
fi\n\
\n\
# Start Ollama in background\n\
echo "Starting Ollama server..."\n\
ollama serve &\n\
OLLAMA_PID=$!\n\
\n\
# Wait for Ollama to be ready\n\
echo "Waiting for Ollama to be ready..."\n\
sleep 15\n\
\n\
# Pull required models (start with smaller models for testing)\n\
echo "Pulling CodeLlama 7B model..."\n\
ollama pull codellama:7b &\n\
\n\
echo "Pulling Llama2 7B model..."\n\
ollama pull llama2:7b &\n\
\n\
# Wait for models to download\n\
wait\n\
\n\
echo "Models downloaded successfully!"\n\
echo "Starting FastAPI application..."\n\
\n\
# Start the application\n\
uvicorn main:app --host 0.0.0.0 --port 3005 --reload' > /app/start.sh

RUN chmod +x /app/start.sh

# Expose ports
EXPOSE 3005
EXPOSE 11434

# Run the startup script
CMD ["/app/start.sh"]