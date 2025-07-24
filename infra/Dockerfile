# Use Python 3.12 slim image
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Add build arg for env file
ARG ENV_FILE=.env
ENV ENV_FILE=${ENV_FILE}

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Copy the specified env file to .env
COPY ${ENV_FILE} .env

# Set environment variable for Flask
ENV FLASK_APP=app.py
ENV PORT=8080

# Expose port 8080
EXPOSE 8080

# Create directory for model cache
RUN mkdir -p /model-cache

# Run the application
CMD ["python", "app.py"]
