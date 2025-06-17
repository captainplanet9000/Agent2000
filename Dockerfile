# Use the official Python image as the base image
FROM python:3.10-slim

# Set environment variables
ENV PYTHONPATH="${PYTHONPATH}:/app"
ENV PYTHONUNBUFFERED=1

# Set the working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Create necessary directories
RUN mkdir -p /app/python/helpers

# Copy the application code
COPY . /app/

# Copy the python/helpers directory if it exists
COPY python/helpers /app/python/helpers/

# Expose the port the app runs on
EXPOSE 8080

# Command to run the application
CMD ["python", "run_ui.py"]
