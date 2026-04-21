#!/bin/bash

echo "Building and running VIB Credit Card Classifier with Docker..."

# Build Docker image
echo "Building Docker image..."
docker build -t vib-classifier .

# Stop and remove existing container if exists
echo "Stopping existing container..."
docker stop vib-credit-card-classifier 2>/dev/null || true
docker rm vib-credit-card-classifier 2>/dev/null || true

# Run container
echo "Starting container..."
docker run -d \
  --name vib-credit-card-classifier \
  -p 8501:8501 \
  vib-classifier

echo ""
echo "Container started successfully!"
echo "Access the app at: http://localhost:8501"
echo ""
echo "Useful commands:"
echo "  docker logs -f vib-credit-card-classifier  # View logs"
echo "  docker stop vib-credit-card-classifier     # Stop container"
echo "  docker start vib-credit-card-classifier    # Start container"
