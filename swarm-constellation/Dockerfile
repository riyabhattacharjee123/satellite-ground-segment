# Use a lightweight Python base
FROM python:3.11-slim

# Set the working directory inside the container
WORKDIR /app

# Install system libraries required by netCDF4
RUN apt-get update && apt-get install -y --no-install-recommends \
    libhdf5-dev \
    libnetcdf-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy our source code into the working directory
COPY src/ .