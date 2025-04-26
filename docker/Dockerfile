FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    software-properties-common \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements files
COPY requirements.txt .
COPY frontend/requirements.txt frontend-requirements.txt
COPY backend/requirements.txt backend-requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir -r frontend-requirements.txt
RUN pip install --no-cache-dir -r backend-requirements.txt

# Copy application code
COPY . .

# Create necessary directories and set permissions
RUN mkdir -p /app/frontend/logs && \
    chmod -R 777 /app/frontend/logs

# Create a script to run both services with debugging
RUN echo '#!/bin/bash\n\
if [ "$SERVICE" = "frontend" ]; then\n\
  cd /app && streamlit run frontend/main.py --server.address 0.0.0.0 --server.port 8501\n\
elif [ "$SERVICE" = "backend" ]; then\n\
  cd /app/backend && uvicorn api.main:app --host 0.0.0.0 --port 8000\n\
else\n\
  echo "Please specify SERVICE=frontend or SERVICE=backend"\n\
  exit 1\n\
fi' > /app/run.sh && chmod +x /app/run.sh

# Set timezone (replace "America/New_York" with your timezone)
ENV TZ=America/New_York
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# Set the entrypoint
ENTRYPOINT ["/app/run.sh"] 