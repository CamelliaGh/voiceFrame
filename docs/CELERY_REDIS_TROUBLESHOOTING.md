# Celery Redis Connection Troubleshooting

## Issue: ReadOnlyError when Celery worker connects to Redis

### Symptoms
```
redis.exceptions.ReadOnlyError: You can't write against a read only replica.
```

This error occurs when the Celery worker tries to connect to Redis but Redis is configured in read-only mode.

### Root Cause
Redis is configured with `replica-read-only yes` and `slave-read-only yes`, which prevents write operations. This can happen due to:
- Default Redis configuration in some Docker images
- Redis being configured as a replica/slave instance
- Configuration conflicts

### Solution

#### Quick Fix (Temporary)
Run the following commands to fix the Redis configuration:

```bash
# Fix Redis read-only configuration
docker-compose exec redis redis-cli CONFIG SET replica-read-only no
docker-compose exec redis redis-cli CONFIG SET slave-read-only no

# Verify the fix
docker-compose exec redis redis-cli CONFIG GET "*read-only*"
```

#### Automated Fix
Use the provided script:

```bash
./scripts/fix_redis_readonly.sh
```

#### Restart Celery Services
After fixing Redis, restart the Celery services:

```bash
docker-compose restart celery-worker celery-beat
```

### Verification
Check that Celery worker is running properly:

```bash
# Check service status
docker-compose ps

# Check Celery worker logs
docker-compose logs celery-worker --tail=20

# Look for these success indicators:
# - "Connected to redis://redis:6379//"
# - "celery@<worker-id> ready."
```

### Prevention
This issue typically occurs when:
1. Redis container is restarted without proper configuration
2. Redis configuration is reset to defaults
3. Redis is configured as a replica instead of master

To prevent this issue:
- Monitor Redis configuration after container restarts
- Use the provided fix script in your deployment pipeline
- Consider using Redis configuration files for persistent settings

### Related Services
This fix affects:
- `celery-worker` - Background task processing
- `celery-beat` - Periodic task scheduling
- Any service that uses Redis for task queuing

### Additional Notes
- The fix is applied at runtime and persists until Redis container restart
- For permanent fixes, consider using Redis configuration files
- This issue is specific to Redis being used as a Celery broker/backend
