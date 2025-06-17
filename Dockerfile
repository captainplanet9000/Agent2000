# Use the official Python image as the base image
FROM python:3.10-slim as builder

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH="/app:${PYTHONPATH}"

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

# Copy the application code
COPY . .

# Create the final image
FROM python:3.10-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH="/app:${PYTHONPATH}"

# Set the working directory
WORKDIR /app

# Create necessary directory structure
RUN mkdir -p /app/python/helpers

# Copy installed packages
COPY --from=builder /usr/local/lib/python3.10/site-packages /usr/local/lib/python3.10/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY --from=builder /app /app

# Ensure the python package is in the Python path
RUN echo "import sys; print('Python path:', sys.path)" > /app/check_path.py && \
    python /app/check_path.py

# Expose the port the app runs on
EXPOSE 8080

# Command to run the application
CMD ["python", "run_ui.py"]
