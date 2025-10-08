#!/bin/bash

# vLLM Startup Script for RTX 3090 Ti (24GB Ampere)
# Note: FP8 KV cache is NOT supported on Ampere GPUs

PROFILE=${1:-balanced}
MODEL_PATH=${2:-"Qwen/Qwen2.5-32B-Instruct-AWQ"}

echo "Starting vLLM with profile: $PROFILE"
echo "Model: $MODEL_PATH"
echo "GPU: RTX 3090 Ti (24GB, Compute 8.6 - Ampere)"
echo ""

case $PROFILE in
  max-context)
    echo "Profile: Maximum Context Window (32K tokens)"
    echo "- Best for: Long documents, large codebases"
    echo "- Context: 32768 tokens"
    echo "- Concurrency: Low (2 sequences)"
    docker run -d --name vllm-server --gpus all -p 8000:8000 --ipc=host \
      vllm-server:3090ti \
      python3 -m vllm.entrypoints.openai.api_server \
      --model "$MODEL_PATH" \
      --quantization awq \
      --dtype half \
      --kv-cache-dtype auto \
      --max-model-len 32768 \
      --max-num-seqs 2 \
      --gpu-memory-utilization 0.95 \
      --port 8000 \
      --host 0.0.0.0
    ;;
    
  balanced)
    echo "Profile: Balanced Boss (16K context)"
    echo "- Best for: Everything text-only (chat, planning, RAG controller, code reviews)"
    echo "- Context: 16000 tokens"
    echo "- KV Cache: FP16 (Ampere doesn't support FP8)"
    docker run -d --name vllm-server --gpus all -p 8000:8000 --ipc=host \
      vllm-server:3090ti \
      python3 -m vllm.entrypoints.openai.api_server \
      --model "$MODEL_PATH" \
      --quantization awq \
      --dtype half \
      --kv-cache-dtype auto \
      --max-model-len 16000 \
      --gpu-memory-utilization 0.9 \
      --port 8000 \
      --host 0.0.0.0
    ;;
    
  high-throughput)
    echo "Profile: High Throughput (8K context, high concurrency)"
    echo "- Best for: API serving, many concurrent requests"
    echo "- Context: 8192 tokens"
    echo "- Concurrency: High (8 sequences)"
    docker run -d --name vllm-server --gpus all -p 8000:8000 --ipc=host \
      vllm-server:3090ti \
      python3 -m vllm.entrypoints.openai.api_server \
      --model "$MODEL_PATH" \
      --quantization awq \
      --dtype half \
      --kv-cache-dtype auto \
      --max-model-len 8192 \
      --max-num-seqs 8 \
      --gpu-memory-utilization 0.85 \
      --port 8000 \
      --host 0.0.0.0
    ;;
    
  *)
    echo "Unknown profile: $PROFILE"
    echo "Available profiles: max-context, balanced, high-throughput"
    exit 1
    ;;
esac

echo ""
echo "Waiting for server to start..."
sleep 5
docker logs vllm-server 2>&1 | tail -20