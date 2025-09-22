FROM python:3.11-slim

# Install system dependencies for network analysis
RUN apt-get update && apt-get install -y \
    tcpdump \
    net-tools \
    iproute2 \
    iptables \
    nmap \
    curl \
    procps \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip install --no-cache-dir \
    fastapi==0.104.1 \
    uvicorn==0.24.0 \
    requests==2.31.0 \
    psutil==5.9.6 \
    scapy==2.5.0 \
    python-multipart==0.0.6 \
    pydantic==2.5.0

WORKDIR /app

# Copy application files
COPY . .

# Expose probe API port
EXPOSE 3007

# Run the probe service
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "3007"]