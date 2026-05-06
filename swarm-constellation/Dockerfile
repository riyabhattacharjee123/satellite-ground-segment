# Use a lightweight Python base
FROM python:3.11-slim

# Set the working directory inside the container
WORKDIR /app

# Install dependencies
RUN pip install --no-cache-dir skyfield

# Copy our source code into the container
COPY src/satellite_node.py .

# Create the data directory
RUN mkdir /app/data

# Run the script when the container starts
CMD ["python", "satellite_node.py"]