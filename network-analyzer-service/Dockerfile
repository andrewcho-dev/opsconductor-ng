FROM python:3.11-slim

# Install system dependencies for packet capture
RUN apt-get update && apt-get install -y \
    tcpdump \
    tshark \
    netcat-openbsd \
    nmap \
    iperf3 \
    curl \
    net-tools \
    iproute2 \
    dnsutils \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user for security (but with necessary capabilities)
RUN useradd -m -u 1000 netanalyzer && \
    chown -R netanalyzer:netanalyzer /app

# Grant necessary capabilities for packet capture
RUN setcap cap_net_raw,cap_net_admin+eip /usr/bin/tcpdump && \
    setcap cap_net_raw,cap_net_admin+eip /usr/bin/tshark

USER netanalyzer

# Expose service port
EXPOSE 3006

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:3006/health || exit 1

# Start the service
CMD ["python", "main.py"]