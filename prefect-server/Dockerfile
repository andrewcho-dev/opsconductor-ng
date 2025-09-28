FROM prefecthq/prefect:2.14-python3.11

# Install PostgreSQL client and async drivers
RUN apt-get update && apt-get install -y \
    postgresql-client \
    libpq-dev \
    gcc \
    && pip install asyncpg psycopg2-binary \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Verify async driver installation
RUN python -c "import asyncpg; print('asyncpg installed successfully')"
RUN python -c "import psycopg2; print('psycopg2 installed successfully')"