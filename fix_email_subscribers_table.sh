#!/bin/bash

# Fix for 500 Error: Missing EmailSubscriber Table
# This script creates the missing email_subscribers table in production

echo "🔧 Fixing EmailSubscriber table issue..."

# Step 1: Apply the migration
echo "📦 Applying database migration..."
docker-compose -f docker-compose.prod.yml exec api alembic upgrade head

if [ $? -eq 0 ]; then
    echo "✅ Migration applied successfully"
else
    echo "❌ Migration failed. Trying manual table creation..."

    # Step 2: If migration fails, create table manually
    echo "🛠️  Creating table manually..."
    docker-compose -f docker-compose.prod.yml exec db psql -U audioposter -d audioposter -c "
    CREATE TABLE IF NOT EXISTS email_subscribers (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        email VARCHAR(255) NOT NULL,
        is_active BOOLEAN DEFAULT true,
        subscribed_at TIMESTAMP DEFAULT now(),
        unsubscribed_at TIMESTAMP,
        source VARCHAR(100),
        consent_data TEXT,
        consent_updated_at TIMESTAMP,
        data_processing_consent BOOLEAN DEFAULT false,
        marketing_consent BOOLEAN DEFAULT false,
        analytics_consent BOOLEAN DEFAULT false
    );

    CREATE UNIQUE INDEX IF NOT EXISTS ix_email_subscribers_email ON email_subscribers(email);
    "

    if [ $? -eq 0 ]; then
        echo "✅ Table created manually"
    else
        echo "❌ Manual table creation failed"
        exit 1
    fi
fi

# Step 3: Restart the API to ensure clean state
echo "🔄 Restarting API service..."
docker-compose -f docker-compose.prod.yml restart api

# Step 4: Check if API is healthy
echo "🏥 Checking API health..."
sleep 5
curl -f https://vocaframe.com/health || echo "⚠️  Health check failed - check logs"

echo "🎉 Fix complete! Try the payment again."
echo ""
echo "📋 To verify the fix worked:"
echo "1. Go to https://vocaframe.com"
echo "2. Upload photo + audio"
echo "3. Customize and preview"
echo "4. Try payment with test card: 4242 4242 4242 4242"
echo ""
echo "📊 Check logs with:"
echo "docker-compose -f docker-compose.prod.yml logs -f api"
