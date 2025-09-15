#!/bin/bash
echo "Starting OpsConductor AI Service..."

# Check for GPU availability
if nvidia-smi > /dev/null 2>&1; then
    echo "GPU detected! Starting Ollama with GPU support..."
    export OLLAMA_GPU=1
else
    echo "No GPU detected. Starting Ollama in CPU mode..."
    export OLLAMA_GPU=0
fi

# Start Ollama in background
echo "Starting Ollama server..."
ollama serve &
OLLAMA_PID=$!

# Wait for Ollama to be ready
echo "Waiting for Ollama to be ready..."
sleep 15

# Pull required models (start with smaller models for testing)
echo "Pulling CodeLlama 7B model..."
ollama pull codellama:7b

echo "Pulling Llama2 7B model..."
ollama pull llama2:7b

echo "Models downloaded successfully!"
echo "Starting FastAPI application..."

# Start the application
uvicorn main:app --host 0.0.0.0 --port 3005 --reload