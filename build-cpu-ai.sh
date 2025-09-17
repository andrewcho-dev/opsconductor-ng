#!/bin/bash
# Build CPU-only versions of AI services for VM environments

echo "Building CPU-only AI services for VM environment..."

# Create CPU-only requirements for vector-service
cd /home/opsconductor/opsconductor-ng/vector-service
grep -v "faiss-gpu" requirements.txt | grep -v "^#" > requirements-cpu.txt
echo "faiss-cpu" >> requirements-cpu.txt

# Build with CPU-only dependencies
docker build --build-arg REQUIREMENTS_FILE=requirements-cpu.txt \
  -f Dockerfile.simple \
  -t opsconductor-ng-vector-service:latest .

echo "Vector service built (CPU-only)"

# For other services, we can use the standard images without CUDA
cd /home/opsconductor/opsconductor-ng

# Build remaining services without GPU 
for service in ai-orchestrator llm-service nlp-service ai-command; do
  echo "Building $service (CPU mode)..."
  docker build -f $service/Dockerfile \
    --build-arg SKIP_CUDA=true \
    -t opsconductor-ng-$service:latest \
    ./$service
done

echo "All AI services built in CPU-only mode"
echo "Start them with: docker compose up -d"