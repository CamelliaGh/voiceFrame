#!/bin/bash
# Cleanup script to prevent disk space issues

echo "🧹 Cleaning up Docker resources..."

# Remove unused containers, networks, images, and build cache
docker system prune -f

# Remove unused volumes
docker volume prune -f

# Remove unused images
docker image prune -f

# Show current disk usage
echo "📊 Current Docker disk usage:"
docker system df

echo "✅ Cleanup complete!"
