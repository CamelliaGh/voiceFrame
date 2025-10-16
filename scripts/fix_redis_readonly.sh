#!/bin/bash

# Fix Redis read-only issue for Celery
# This script fixes the Redis configuration that prevents Celery from writing to Redis

echo "Fixing Redis read-only configuration..."

# Check if Redis container is running
if ! docker-compose ps redis | grep -q "Up"; then
    echo "Redis container is not running. Starting Redis..."
    docker-compose up redis -d
    sleep 5
fi

# Fix the read-only configuration
echo "Setting Redis to allow writes..."
docker-compose exec redis redis-cli CONFIG SET replica-read-only no
docker-compose exec redis redis-cli CONFIG SET slave-read-only no

# Verify the configuration
echo "Verifying Redis configuration..."
docker-compose exec redis redis-cli CONFIG GET "*read-only*"

echo "Redis configuration fixed. Celery workers should now be able to connect."
echo "If you need to restart Celery workers:"
echo "  docker-compose restart celery-worker celery-beat"
