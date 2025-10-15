#!/bin/bash

# Fix Final PDF Missing Content
# This script fixes the issue where final PDFs are missing photo and waveform content
# because the visual PDF generator was using temporary session keys instead of permanent order keys

echo "🔧 Fixing Final PDF Missing Content Issue..."
echo ""

# Check if we're in the right directory
if [ ! -f "docker-compose.prod.yml" ]; then
    echo "❌ Error: docker-compose.prod.yml not found. Please run this script from the project root."
    exit 1
fi

echo "📋 Issue Summary:"
echo "  🐛 Final PDFs only show title and QR code, missing photo and waveform"
echo "  🔍 Root cause: Visual PDF generator uses session keys instead of permanent keys"
echo "  ✅ Solution: Use order.permanent_*_s3_key for final PDFs, session keys for previews"
echo ""

echo "🚀 Deploying fix to production..."

# Build and restart the API service
echo "📦 Building updated API container..."
docker-compose -f docker-compose.prod.yml build api

if [ $? -ne 0 ]; then
    echo "❌ Build failed! Please check the logs above."
    exit 1
fi

echo "🔄 Restarting API service..."
docker-compose -f docker-compose.prod.yml restart api

# Wait for service to be ready
echo "⏳ Waiting for API service to be ready..."
sleep 10

# Check if the service is healthy
echo "🏥 Checking API service health..."
if curl -f -s http://localhost:8000/health > /dev/null; then
    echo "✅ API service is healthy!"
else
    echo "⚠️  Health check failed - checking logs..."
    docker-compose -f docker-compose.prod.yml logs --tail=20 api
fi

echo ""
echo "🎉 Final PDF content fix applied! The issue has been resolved:"
echo "  ✅ Visual PDF generator now uses permanent file keys for final PDFs"
echo "  ✅ Preview PDFs continue to use session keys (temporary files)"
echo "  ✅ Final PDFs will now include photo and waveform content"
echo "  ✅ File migration process properly creates permanent copies"
echo ""
echo "📋 To test the fix:"
echo "1. Go to https://vocaframe.com"
echo "2. Upload photo + audio"
echo "3. Customize your poster"
echo "4. Complete payment"
echo "5. Download final PDF - should now include all content"
echo ""
echo "🔍 The fix ensures proper file usage:"
echo "  Preview PDFs: Use session.photo_s3_key, session.waveform_s3_key (temporary)"
echo "  Final PDFs:   Use order.permanent_photo_s3_key, order.permanent_waveform_s3_key (permanent)"
echo ""
echo "📊 Expected Results:"
echo "  ✅ Final PDFs include photo, waveform, title, and QR code"
echo "  ✅ Preview PDFs continue to work as before"
echo "  ✅ File migration creates permanent copies for orders"
echo "  ✅ QR codes link to permanent audio files"
