#!/bin/bash

echo "🔴 Enabling red circle debug mode..."

# Set the environment variable
export DEBUG_PHOTO_CIRCLE=true

# Add it to .env file for persistence
echo "DEBUG_PHOTO_CIRCLE=true" >> .env

echo "✅ Environment variable set: DEBUG_PHOTO_CIRCLE=$DEBUG_PHOTO_CIRCLE"

# Check if Docker containers are running
if docker-compose ps | grep -q "Up"; then
    echo "🔄 Restarting Docker containers to apply debug mode..."
    docker-compose down
    docker-compose up -d
    echo "✅ Containers restarted with debug mode enabled"
else
    echo "ℹ️  Docker containers not running. Start them with:"
    echo "   docker-compose up -d"
fi

echo ""
echo "🔴 Red circle debug mode is now enabled!"
echo "   When you generate a preview with a circle photo, you'll see a red circle instead of the actual photo."
echo ""
echo "To disable debug mode:"
echo "   export DEBUG_PHOTO_CIRCLE=false"
echo "   docker-compose restart"
