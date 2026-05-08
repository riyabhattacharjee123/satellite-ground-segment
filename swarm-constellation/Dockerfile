# Use a lightweight Python base
FROM python:3.11-slim

# Set the working directory inside the container
WORKDIR /app

# Install dependencies from requirements file
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy our source code into the container
COPY src/ .