# 📊 VoiceFrame Data Management Strategy

## 🎯 **Current Situation Analysis**

### **✅ What You're Doing Right:**
- **No file storage on server** - Using S3 for all file storage
- **Small database footprint** - Only 63MB for all data
- **Clean architecture** - Separation of concerns

### **📈 Current Disk Usage:**
- **Project Directory**: 294MB (mostly `node_modules` and `venv`)
- **Database**: 63MB (very reasonable!)
- **Docker Images**: 24GB (13GB reclaimable)
- **Docker Volumes**: 10GB (mostly unused)

## 🧹 **Data Cleanup Strategy**

### **1. Automatic Cleanup for Unpaid Users**

You're absolutely right! Here's the recommended approach:

#### **Session Lifecycle:**
```
User creates session → 24 hours → Session expires → Cleanup
User creates session → 7 days → No payment → Cleanup
User pays → Session becomes permanent → Keep forever
```

#### **Cleanup Rules:**
- **Expired sessions**: Delete immediately after expiration
- **Unpaid sessions**: Delete after 7 days
- **Paid sessions**: Keep permanently
- **S3 files**: Use lifecycle policies for automatic cleanup

### **2. Database Cleanup Script**

Run the cleanup script regularly:

```bash
# Check current database stats
python scripts/data_cleanup.py

# Set up automated cleanup (cron job)
# Run daily at 2 AM
0 2 * * * cd /path/to/voiceframe && python scripts/data_cleanup.py
```

### **3. Docker Cleanup**

Reclaim unused Docker space:

```bash
# Safe cleanup (recommended)
./scripts/docker_cleanup.sh

# Aggressive cleanup (removes ALL unused images)
docker system prune -a --volumes
```

## 📋 **Recommended Cleanup Schedule**

### **Daily:**
- Clean up expired sessions
- Clean up old unpaid sessions (>7 days)

### **Weekly:**
- Run Docker cleanup
- Check database size
- Review S3 storage usage

### **Monthly:**
- Full system cleanup
- Review and optimize database indexes
- Check for orphaned S3 files

## 🗄️ **Database Optimization**

### **Current Database Size: 63MB**
This is very reasonable! For context:
- **1,000 sessions**: ~1MB
- **10,000 sessions**: ~10MB
- **100,000 sessions**: ~100MB

### **Optimization Strategies:**

#### **1. Index Optimization**
```sql
-- Add indexes for cleanup queries
CREATE INDEX IF NOT EXISTS idx_sessions_created_at ON sessions(created_at);
CREATE INDEX IF NOT EXISTS idx_sessions_expires_at ON sessions(expires_at);
CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status);
```

#### **2. Partitioning (Future)**
For very large datasets, consider partitioning by date:
```sql
-- Partition sessions table by month
CREATE TABLE sessions_2024_01 PARTITION OF sessions
FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');
```

## ☁️ **S3 Storage Management**

### **Current Strategy:**
- **Temporary files**: `temp_photos/`, `temp_audio/`
- **Permanent files**: `permanent/photos/`, `permanent/audio/`
- **Lifecycle policies**: Auto-delete temp files after 7 days

### **Recommended S3 Lifecycle Policy:**
```json
{
  "Rules": [
    {
      "ID": "DeleteTempFiles",
      "Status": "Enabled",
      "Filter": {
        "Prefix": "temp_"
      },
      "Expiration": {
        "Days": 7
      }
    },
    {
      "ID": "TransitionToIA",
      "Status": "Enabled",
      "Filter": {
        "Prefix": "permanent/"
      },
      "Transitions": [
        {
          "Days": 30,
          "StorageClass": "STANDARD_IA"
        },
        {
          "Days": 90,
          "StorageClass": "GLACIER"
        }
      ]
    }
  ]
}
```

## 📊 **Monitoring & Alerts**

### **Set up alerts for:**
- **Database size** > 1GB
- **S3 storage** > 100GB
- **Disk usage** > 80%
- **Failed cleanup jobs**

### **Monitoring Queries:**
```sql
-- Database size
SELECT pg_size_pretty(pg_database_size('voiceframe'));

-- Session counts
SELECT
  COUNT(*) as total_sessions,
  COUNT(CASE WHEN expires_at < NOW() THEN 1 END) as expired,
  COUNT(CASE WHEN created_at < NOW() - INTERVAL '7 days' THEN 1 END) as old_unpaid
FROM sessions;

-- Storage usage by type
SELECT
  CASE
    WHEN photo_s3_key LIKE 'temp_%' THEN 'temp_photos'
    WHEN audio_s3_key LIKE 'temp_%' THEN 'temp_audio'
    WHEN photo_s3_key LIKE 'permanent/%' THEN 'permanent_photos'
    WHEN audio_s3_key LIKE 'permanent/%' THEN 'permanent_audio'
  END as storage_type,
  COUNT(*) as count
FROM sessions
GROUP BY storage_type;
```

## 🚀 **Production Recommendations**

### **1. Automated Cleanup**
```bash
# Add to crontab
0 2 * * * cd /app && python scripts/data_cleanup.py >> /var/log/cleanup.log 2>&1
0 3 * * 0 cd /app && ./scripts/docker_cleanup.sh >> /var/log/docker_cleanup.log 2>&1
```

### **2. Database Maintenance**
```sql
-- Weekly VACUUM and ANALYZE
VACUUM ANALYZE sessions;
VACUUM ANALYZE orders;
```

### **3. Monitoring Integration**
- Add cleanup metrics to your Prometheus monitoring
- Set up alerts for failed cleanup jobs
- Monitor database growth trends

## 💡 **Key Takeaways**

1. **✅ Your approach is correct** - No file storage on server
2. **✅ Database is small** - 63MB is very reasonable
3. **✅ Cleanup strategy needed** - For unpaid users after 7 days
4. **✅ Docker cleanup** - Can reclaim 13GB of unused space
5. **✅ S3 lifecycle policies** - Automate temp file cleanup

Your data management strategy is solid! The main opportunity is implementing automated cleanup for unpaid users, which will keep your database lean and efficient. 🎯
