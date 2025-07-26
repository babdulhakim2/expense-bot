# Use Python 3.12 slim image
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# No need for .env file - using Cloud Run secrets

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

# Set environment variable for Flask
ENV FLASK_APP=app.py
ENV PORT=8080

# Expose port 8080
EXPOSE 8080

# Create directory for model cache
RUN mkdir -p /model-cache

# Run the application
CMD ["python", "app.py"]
