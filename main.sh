#!/bin/bash
# This script is used to start the application for a Replit environment

# Check if Docker Compose is installed
if ! command -v docker compose &> /dev/null; then
    echo "Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Build and start the Docker containers
cd backend || { echo "Error: backend directory not found"; exit 1; }
docker compose up --build