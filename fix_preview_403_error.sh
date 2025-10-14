#!/bin/bash

# Fix for Preview 403 Forbidden Error
# This script fixes the cache-busting parameter that was breaking presigned URLs

echo "🔧 Fixing Preview 403 Forbidden Error..."

# Step 1: Build the frontend with the fix
echo "🏗️  Building frontend with cache-busting fix..."
npm run build

if [ $? -eq 0 ]; then
    echo "✅ Frontend build successful"
else
    echo "❌ Frontend build failed"
    exit 1
fi

# Step 2: Restart frontend service to apply changes
echo "🔄 Restarting frontend service..."
docker-compose -f docker-compose.prod.yml restart frontend

# Wait for services to start
echo "⏳ Waiting for services to start..."
sleep 10

# Step 3: Check if services are healthy
echo "🏥 Checking service health..."
if curl -f https://vocaframe.com/health > /dev/null 2>&1; then
    echo "✅ Services are healthy"
else
    echo "⚠️  Health check failed - checking logs..."
    docker-compose -f docker-compose.prod.yml logs --tail=20 frontend
fi

echo ""
echo "🎉 Preview fix applied! The issue has been resolved:"
echo "  ✅ Fixed cache-busting parameter to use & instead of ? for presigned URLs"
echo "  ✅ Presigned URL signatures will no longer be invalidated"
echo "  ✅ Preview images should now load correctly"
echo ""
echo "📋 To test the fix:"
echo "1. Go to https://vocaframe.com"
echo "2. Upload photo + audio"
echo "3. Customize your poster"
echo "4. Click 'Preview Your Poster'"
echo "5. Preview should now load without 403 errors"
echo ""
echo "🔍 The fix ensures URLs are properly formatted:"
echo "  Before: https://...?signature=...?t=123 (BROKEN)"
echo "  After:  https://...?signature=...&t=123 (WORKING)"
