#!/bin/bash

echo "🧹 Docker Cleanup Script"
echo "========================"

echo "📊 Current Docker usage:"
docker system df

echo ""
echo "🗑️  Cleaning up unused Docker resources..."

# Remove unused containers
echo "  - Removing stopped containers..."
docker container prune -f

# Remove unused images
echo "  - Removing unused images..."
docker image prune -f

# Remove unused volumes (be careful with this!)
echo "  - Removing unused volumes..."
docker volume prune -f

# Remove unused networks
echo "  - Removing unused networks..."
docker network prune -f

# Remove build cache
echo "  - Removing build cache..."
docker builder prune -f

echo ""
echo "📊 Docker usage after cleanup:"
docker system df

echo ""
echo "✅ Docker cleanup complete!"
echo ""
echo "💡 To reclaim even more space, you can run:"
echo "   docker system prune -a --volumes"
echo "   (This will remove ALL unused images, not just dangling ones)"
