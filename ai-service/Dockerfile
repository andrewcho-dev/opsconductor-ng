FROM python:3.13-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive

WORKDIR /app

# Install system dependencies including CUDA toolkit
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    git \
    build-essential \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Install Ollama
RUN curl -fsSL https://ollama.ai/install.sh | sh

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Download spaCy model
RUN python -m spacy download en_core_web_sm

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