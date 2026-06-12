FROM python:3.11-slim

# ------------------------------------------------------------------
# System dependencies
# ------------------------------------------------------------------
RUN apt-get update && apt-get install -y \
    openssl \
    ca-certificates \
    curl \
    && rm -rf /var/lib/apt/lists/*

# ------------------------------------------------------------------
# Application setup
# ------------------------------------------------------------------
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY . .

# ------------------------------------------------------------------
# Runtime configuration
# ------------------------------------------------------------------
EXPOSE 9000

# IMPORTANT:
# PKI data is mounted at /pki via docker-compose
# Directories are created by the application at runtime

CMD ["python", "-m", "app.main"]
