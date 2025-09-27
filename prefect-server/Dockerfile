FROM prefecthq/prefect:2.14-python3.11

# Install PostgreSQL client and psycopg2
RUN apt-get update && apt-get install -y \
    postgresql-client \
    libpq-dev \
    gcc \
    && pip install psycopg2-binary \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Verify psycopg2 installation
RUN python -c "import psycopg2; print('psycopg2 installed successfully')"