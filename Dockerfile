# Use a slim version of Python 3.13 for a smaller image size
FROM python:3.13-slim

# Set the working directory inside the container
# This is usually always /app
WORKDIR /app

# Prevent Python from writing .pyc files and enable unbuffered logging
# This prevents Python from creating new .pyc files inside the container while running
# (different from .pyc extension in .dockerignore)
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy only requirements first to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Set the PYTHONPATH so the container can find modules in /src
ENV PYTHONPATH=/app/src

# Command to run your bot in the container
CMD ["python", "src/main.py"]
