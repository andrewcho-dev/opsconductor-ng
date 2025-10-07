#!/bin/bash
# Start vLLM with Qwen2.5-14B-Instruct-AWQ model
# 131K context window, optimized for RTX 3060 12GB

echo "=========================================="
echo "Starting vLLM with Qwen2.5-14B-Instruct-AWQ"
echo "Context: 131K tokens"
echo "GPU: RTX 3060 12GB"
echo "=========================================="

# Check if model is already running
if pgrep -f "vllm.entrypoints.openai.api_server" > /dev/null; then
    echo "⚠️  vLLM is already running!"
    echo "Stop it first with: sudo pkill -f vllm.entrypoints.openai.api_server"
    exit 1
fi

# Check GPU availability
if ! nvidia-smi > /dev/null 2>&1; then
    echo "❌ NVIDIA GPU not detected!"
    exit 1
fi

echo ""
echo "📊 GPU Status:"
nvidia-smi --query-gpu=name,memory.total,memory.free --format=csv,noheader
echo ""

# Start vLLM server
echo "🚀 Starting vLLM server..."
echo ""

python3 -m vllm.entrypoints.openai.api_server \
  --model Qwen/Qwen2.5-14B-Instruct-AWQ \
  --dtype auto \
  --port 8000 \
  --max-model-len 131072 \
  --gpu-memory-utilization 0.85 \
  --enforce-eager \
  --quantization awq \
  --host 0.0.0.0