# Use a lightweight Python base
FROM python:3.11-slim

# Set the working directory inside the container
WORKDIR /app

# Install dependencies
RUN pip install --no-cache-dir skyfield fastapi uvicorn requests

# Copy our source code into the container
COPY src/ .