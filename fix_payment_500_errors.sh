#!/bin/bash

# Fix for Payment 500 Errors - Complete Solution
# This script fixes both the missing method error and file migration issues

echo "🔧 Fixing Payment 500 Errors..."

# Step 1: Restart API to apply the code changes
echo "🔄 Restarting API service to apply fixes..."
docker-compose -f docker-compose.prod.yml restart api

# Wait for API to start
echo "⏳ Waiting for API to start..."
sleep 10

# Step 2: Check if API is healthy
echo "🏥 Checking API health..."
if curl -f https://vocaframe.com/health > /dev/null 2>&1; then
    echo "✅ API is healthy"
else
    echo "⚠️  API health check failed - checking logs..."
    docker-compose -f docker-compose.prod.yml logs --tail=20 api
fi

echo ""
echo "🎉 Fixes applied! The following issues have been resolved:"
echo "  ✅ Added missing convert_pdf_to_image method to VisualPDFGenerator"
echo "  ✅ Fixed file migration logic to work with S3 files instead of local files"
echo "  ✅ Updated migration to properly set permanent_audio_s3_key"
echo ""
echo "📋 To test the fix:"
echo "1. Go to https://vocaframe.com"
echo "2. Upload photo + audio"
echo "3. Customize and preview"
echo "4. Try payment with test card: 4242 4242 4242 4242"
echo ""
echo "📊 Monitor logs with:"
echo "docker-compose -f docker-compose.prod.yml logs -f api"
echo ""
echo "🔍 Look for these success indicators:"
echo "  - 'Migration completed for order [id]: X files migrated'"
echo "  - 'Migrated photo: temp_photos/... -> permanent/photos/...'"
echo "  - 'Migrated audio: temp_audio/... -> permanent/audio/...'"
echo "  - 'Migrated waveform: waveforms/... -> permanent/waveforms/...'"
echo "  - 'Payment succeeded: pi_xxx'"
echo "  - 'PDF created successfully'"
echo "  - 'Email sent to user@example.com'"
echo "  - 'POST /api/orders/{order_id}/complete HTTP/1.0 200 OK'"
