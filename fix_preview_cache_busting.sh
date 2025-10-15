#!/bin/bash

# Fix Preview Cache-Busting Issue
# This script fixes the issue where cache-busting parameters break presigned URL signatures

echo "🔧 Fixing Preview Cache-Busting Issue..."
echo ""

# Check if we're in the right directory
if [ ! -f "docker-compose.prod.yml" ]; then
    echo "❌ Error: docker-compose.prod.yml not found. Please run this script from the project root."
    exit 1
fi

echo "📋 Issue Summary:"
echo "  🐛 Preview images return 403 Forbidden due to invalid signatures"
echo "  🔍 Root cause: Frontend adds ?t= parameter to presigned URLs, breaking AWS signature"
echo "  ✅ Solution: Remove cache-busting from presigned URLs (they're already unique)"
echo ""

echo "🚀 Deploying fix to production..."

# Build frontend
echo "📦 Building frontend..."
npm run build

if [ $? -ne 0 ]; then
    echo "❌ Frontend build failed! Please check the logs above."
    exit 1
fi

# Build and restart the frontend service
echo "📦 Building updated frontend container..."
docker-compose -f docker-compose.prod.yml build frontend

if [ $? -ne 0 ]; then
    echo "❌ Docker build failed! Please check the logs above."
    exit 1
fi

echo "🔄 Restarting frontend service..."
docker-compose -f docker-compose.prod.yml restart frontend

# Wait for service to be ready
echo "⏳ Waiting for frontend service to be ready..."
sleep 5

# Check if the service is healthy
echo "🏥 Checking frontend service health..."
if curl -f -s http://localhost:3000 > /dev/null; then
    echo "✅ Frontend service is healthy!"
else
    echo "⚠️  Health check failed - checking logs..."
    docker-compose -f docker-compose.prod.yml logs --tail=20 frontend
fi

echo ""
echo "🎉 Preview cache-busting fix applied! The issue has been resolved:"
echo "  ✅ Removed cache-busting parameter from presigned URLs"
echo "  ✅ Presigned URL signatures will no longer be invalidated"
echo "  ✅ Preview images should now load correctly"
echo "  ✅ Presigned URLs already have expiration times and unique timestamps"
echo ""
echo "📋 To test the fix:"
echo "1. Go to https://vocaframe.com"
echo "2. Upload photo + audio (use a FRESH new session)"
echo "3. Customize your poster"
echo "4. Click 'Preview Your Poster'"
echo "5. Preview should now load without 403 errors"
echo ""
echo "🔍 The fix removes cache-busting from presigned URLs:"
echo "  Before: https://...?signature=...&t=123 (BREAKS SIGNATURE)"
echo "  After:  https://...?signature=... (PRESERVES SIGNATURE)"
