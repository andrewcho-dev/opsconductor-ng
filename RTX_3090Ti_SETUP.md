# RTX 3090 Ti vLLM Setup Guide

## Hardware Overview

**RTX 3090 Ti Specifications:**
- Architecture: Ampere (Compute Capability 8.6)
- VRAM: 24 GB GDDR6X
- Memory Bandwidth: 1008 GB/s
- **FP8 KV Cache Support: ❌ NO** (requires Ada/Hopper with compute 8.9+)

## What Changed from RTX 3060

| Feature | RTX 3060 | RTX 3090 Ti | Improvement |
|---------|----------|-------------|-------------|
| VRAM | 12 GB | 24 GB | **2x more** ✅ |
| Memory Bandwidth | 360 GB/s | 1008 GB/s | **3x faster** ✅ |
| Max Context (FP16) | ~8K tokens | ~32K tokens | **4x larger** ✅ |
| FP8 KV Cache | ❌ No | ❌ No | Still not supported |

## Key Takeaway

**You CANNOT use FP8 KV cache on the 3090 Ti**, but the 24GB VRAM means you can run:
- **Much larger context windows** (32K+ tokens with FP16 KV cache)
- **Larger models** (32B or even 72B parameter models)
- **Better performance** (3x memory bandwidth = faster inference)

## Quick Start

### 1. Build the Docker Image

```bash
cd /home/opsconductor/opsconductor-ng
docker build -f Dockerfile.vllm.3090ti -t vllm-server:3090ti .
```

### 2. Start the Server (Choose a Profile)

#### Option A: Maximum Context (32K tokens)
Best for: Long documents, large codebases, complex reasoning

```bash
./start_vllm_3090ti.sh max-context
```

#### Option B: Balanced (16K tokens) - **RECOMMENDED**
Best for: General use, multiple users

```bash
./start_vllm_3090ti.sh balanced
```

#### Option C: High Throughput (8K tokens)
Best for: API serving, many concurrent requests

```bash
./start_vllm_3090ti.sh high-throughput
```

### 3. Test the Server

```bash
curl http://localhost:8000/v1/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "Qwen/Qwen2.5-32B-Instruct-AWQ",
    "prompt": "Explain quantum computing in simple terms:",
    "max_tokens": 100
  }'
```

## Manual Configuration

If you want to customize settings:

```bash
docker run -d --name vllm-server --gpus all -p 8000:8000 --ipc=host \
  vllm-server:3090ti \
  python3 -m vllm.entrypoints.openai.api_server \
  --model "Qwen/Qwen2.5-32B-Instruct-AWQ" \
  --quantization awq \
  --dtype half \
  --kv-cache-dtype auto \
  --max-model-len 24576 \
  --max-num-seqs 3 \
  --gpu-memory-utilization 0.92 \
  --port 8000 \
  --host 0.0.0.0
```

### Key Parameters Explained

- `--kv-cache-dtype auto`: Uses FP16 (FP8 not supported on Ampere)
- `--max-model-len`: Maximum context window (tokens)
  - 32768 = Maximum for 24GB with 32B model
  - 16384 = Balanced (recommended)
  - 8192 = High throughput
- `--max-num-seqs`: Concurrent sequences (higher = more throughput, less memory per request)
- `--gpu-memory-utilization`: Fraction of GPU memory to use (0.90-0.95 recommended)

## Memory Calculations

With 24GB VRAM and Qwen2.5-32B-Instruct-AWQ:

| Context Length | KV Cache Memory | Max Concurrent Seqs | Use Case |
|----------------|-----------------|---------------------|----------|
| 32K tokens | ~12 GB | 2 | Long documents |
| 16K tokens | ~6 GB | 4 | Balanced |
| 8K tokens | ~3 GB | 8 | High throughput |

*Note: Model weights take ~8GB with AWQ quantization*

## Monitoring

### Check Server Status
```bash
docker logs vllm-server
```

### Check GPU Usage
```bash
nvidia-smi
```

### Stop Server
```bash
docker stop vllm-server && docker rm vllm-server
```

## Performance Tips

1. **Use AWQ Quantization**: Reduces model size from 64GB to ~8GB
2. **Enable Tensor Parallelism** (if you add another GPU):
   ```bash
   --tensor-parallel-size 2
   ```
3. **Adjust Batch Size**: Lower `--max-num-seqs` for longer contexts
4. **Monitor Memory**: Use `nvidia-smi` to ensure you're not OOM

## Future Upgrade Path

If you need FP8 KV cache support, you'll need to upgrade to:
- **RTX 4090** (24GB, Ada Lovelace, Compute 8.9) - **RECOMMENDED**
- **RTX 4080 Super** (16GB, Ada Lovelace, Compute 8.9)
- **H100** (80GB, Hopper, Compute 9.0) - Data center GPU

The RTX 4090 would give you:
- ✅ FP8 KV cache support (50% memory savings)
- ✅ 64K+ context windows with FP8
- ✅ Same 24GB VRAM
- ✅ Better performance overall

## Troubleshooting

### Error: "CUDA out of memory"
- Reduce `--max-model-len`
- Reduce `--max-num-seqs`
- Lower `--gpu-memory-utilization` to 0.85

### Error: "fp8e4nv data type is not supported"
- You tried to use FP8 KV cache - this is NOT supported on Ampere
- Use `--kv-cache-dtype auto` instead

### Slow Performance
- Check `nvidia-smi` for GPU utilization
- Ensure you're using `--dtype half` (FP16)
- Consider reducing context length for better throughput

## Summary

Your RTX 3090 Ti is a **significant upgrade** from the 3060:
- ✅ 2x more VRAM (24GB vs 12GB)
- ✅ 3x faster memory bandwidth
- ✅ Can run 32K context windows
- ✅ Can run larger models (32B, 72B)
- ❌ Still no FP8 KV cache (need RTX 4090 for that)

**Bottom line**: You can now run much larger contexts and models, but FP8 KV cache requires a newer GPU architecture.