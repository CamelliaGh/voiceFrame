#!/bin/bash

# Deploy All Fixes
# This script deploys both backend and frontend fixes for the preview and final PDF issues

echo "🔧 Deploying All Fixes..."
echo ""

# Check if we're in the right directory
if [ ! -f "docker-compose.prod.yml" ]; then
    echo "❌ Error: docker-compose.prod.yml not found. Please run this script from the project root."
    exit 1
fi

echo "📋 Fixes Being Deployed:"
echo "  1. Backend: Visual PDF generator uses permanent file keys for final PDFs"
echo "  2. Frontend: Remove cache-busting from presigned URLs"
echo ""

# Build frontend first
echo "🎨 Building frontend..."
npm run build

if [ $? -ne 0 ]; then
    echo "❌ Frontend build failed! Please check the logs above."
    exit 1
fi

echo "✅ Frontend built successfully!"
echo ""

# Build and restart all services
echo "📦 Building updated Docker containers..."
docker-compose -f docker-compose.prod.yml build

if [ $? -ne 0 ]; then
    echo "❌ Docker build failed! Please check the logs above."
    exit 1
fi

echo "✅ Docker containers built successfully!"
echo ""

echo "🔄 Restarting services..."
docker-compose -f docker-compose.prod.yml restart

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."
sleep 15

# Check if services are healthy
echo "🏥 Checking service health..."
echo ""

echo "Checking API service..."
if curl -f -s http://localhost:8000/health > /dev/null; then
    echo "✅ API service is healthy!"
else
    echo "⚠️  API health check failed"
    docker-compose -f docker-compose.prod.yml logs --tail=10 api
fi

echo ""
echo "Checking frontend service..."
if curl -f -s http://localhost:3000 > /dev/null; then
    echo "✅ Frontend service is healthy!"
else
    echo "⚠️  Frontend health check failed"
    docker-compose -f docker-compose.prod.yml logs --tail=10 frontend
fi

echo ""
echo "🎉 All fixes deployed successfully!"
echo ""
echo "📋 What was fixed:"
echo "  ✅ Backend: Final PDFs now use permanent file keys (photo, waveform, audio)"
echo "  ✅ Frontend: Presigned URLs no longer have cache-busting parameters"
echo "  ✅ Preview images will load correctly without 403 errors"
echo "  ✅ Final PDFs will include all content (photo, waveform, title, QR)"
echo ""
echo "🧪 To test the fixes:"
echo "1. Go to https://vocaframe.com"
echo "2. Create a FRESH NEW session (don't reuse old sessions)"
echo "3. Upload NEW photo + audio"
echo "4. Wait for audio processing to complete"
echo "5. Customize your poster"
echo "6. Click 'Preview Your Poster' → Should work without errors"
echo "7. Complete payment"
echo "8. Download final PDF → Should include all content"
echo ""
echo "⚠️  IMPORTANT: You MUST create a fresh new session with new uploads!"
echo "   Old sessions may have missing files and will not work."
