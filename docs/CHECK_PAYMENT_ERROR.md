# Troubleshooting 500 Error on Order Completion

## 🔍 What Happened

**Good news**: The payment went through successfully! ✅

**The issue**: A 500 error occurred when trying to:
- Migrate temporary files to permanent storage
- Generate the final PDF without watermark
- Send the download email

The error is at: `POST /api/orders/{order_id}/complete`

---

## 🛠️ Step 1: Check Backend Logs

SSH into your production server and check the logs:

```bash
# Check recent logs
docker-compose -f docker-compose.prod.yml logs --tail=100 api

# Follow logs in real-time (then try payment again)
docker-compose -f docker-compose.prod.yml logs -f api

# Search for the specific order
docker-compose -f docker-compose.prod.yml logs api | grep "79fa1a45-feff-443f-aaab-e1a7f2dee72c"
```

---

## 🔍 Common Issues and Fixes

### **Issue 1: S3 Permission Denied**

**Log message**: `"File migration failed"` or `"Access Denied"` or `"403 Forbidden"`

**Cause**: AWS credentials missing or incorrect

**Fix**:
```bash
# Check if AWS credentials are set
docker-compose -f docker-compose.prod.yml exec api env | grep AWS

# Should see:
# AWS_ACCESS_KEY_ID=AKIAxxxx
# AWS_SECRET_ACCESS_KEY=xxxxx
# S3_BUCKET=audioposter-bucket
# S3_REGION=us-east-2

# If missing, add to .env and restart
docker-compose -f docker-compose.prod.yml restart api
```

---

### **Issue 2: S3 Files Missing**

**Log message**: `"Photo file is missing"` or `"Audio file is missing"` or `"Waveform file is missing"`

**Cause**: Temporary files were deleted before payment completed

**Fix**: This shouldn't happen, but if it does:
1. Files might have expired (check `SESSION_EXPIRATION` in config)
2. A cleanup job might have run too early
3. Check session expiration settings

---

### **Issue 3: PDF Generation Failing**

**Log message**: Font errors, template errors, or ReportLab errors

**Possible causes**:
- **Missing fonts**: Check `/fonts/` directory
- **Missing templates**: Check `/templates/` directory
- **Missing backgrounds**: Check `/backgrounds/` directory

**Fix**:
```bash
# Check if files exist in container
docker-compose -f docker-compose.prod.yml exec api ls -la /app/fonts/
docker-compose -f docker-compose.prod.yml exec api ls -la /app/templates/
docker-compose -f docker-compose.prod.yml exec api ls -la /app/backgrounds/

# If missing, rebuild
docker-compose -f docker-compose.prod.yml build api
docker-compose -f docker-compose.prod.yml restart api
```

---

### **Issue 4: Email Sending Failing**

**Log message**: `"SendGrid"` or `"Email failed"`

**Cause**: SendGrid API key missing or invalid

**Fix**:
```bash
# Check SendGrid config
docker-compose -f docker-compose.prod.yml exec api env | grep SENDGRID

# Should see:
# SENDGRID_API_KEY=SG.xxxxx
# FROM_EMAIL=your@email.com

# If missing, add to .env and restart
```

---

### **Issue 5: Database Error**

**Log message**: `"database"` or `"postgresql"` errors

**Cause**: Database connection lost or query failed

**Fix**:
```bash
# Check if database is running
docker-compose -f docker-compose.prod.yml ps db

# Check database logs
docker-compose -f docker-compose.prod.yml logs db

# Restart database if needed
docker-compose -f docker-compose.prod.yml restart db api
```

---

### **Issue 6: Memory/Resource Issues**

**Log message**: `"Out of memory"` or process killed

**Cause**: Server running out of resources

**Fix**:
```bash
# Check container resource usage
docker stats

# Check server resources
free -h
df -h

# If low on memory/disk, clean up:
docker system prune -a
docker volume prune
```

---

## 🧪 Testing the Fix

After fixing the issue:

### **Test 1: Try Payment Again**
1. Go to https://vocaframe.com
2. Upload new photo + audio
3. Complete checkout
4. Watch the logs: `docker-compose -f docker-compose.prod.yml logs -f api`

### **Test 2: Manual Order Completion**

If you need to manually complete the failed order:

```bash
# Get order details
docker-compose -f docker-compose.prod.yml exec api python3 -c "
from backend.database import SessionLocal
from backend.models import Order
db = SessionLocal()
order = db.query(Order).filter(Order.id == '79fa1a45-feff-443f-aaab-e1a7f2dee72c').first()
if order:
    print(f'Order status: {order.status}')
    print(f'Payment intent: {order.stripe_payment_intent_id}')
    print(f'Session token: {order.session_token}')
    print(f'Email: {order.email}')
else:
    print('Order not found')
"
```

---

## 📊 Quick Diagnostic Commands

```bash
# Check all service health
docker-compose -f docker-compose.prod.yml ps

# Check API container logs (last 50 lines)
docker-compose -f docker-compose.prod.yml logs --tail=50 api

# Check for errors specifically
docker-compose -f docker-compose.prod.yml logs api | grep -i error

# Check for the specific order
docker-compose -f docker-compose.prod.yml logs api | grep "79fa1a45"

# Check S3 connectivity
docker-compose -f docker-compose.prod.yml exec api python3 -c "
import boto3
import os
s3 = boto3.client('s3',
    aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
    region_name=os.getenv('S3_REGION')
)
try:
    s3.list_objects_v2(Bucket=os.getenv('S3_BUCKET'), MaxKeys=1)
    print('✅ S3 connection works!')
except Exception as e:
    print(f'❌ S3 connection failed: {e}')
"

# Check SendGrid API key
docker-compose -f docker-compose.prod.yml exec api python3 -c "
import os
key = os.getenv('SENDGRID_API_KEY')
if key and key.startswith('SG.'):
    print('✅ SendGrid API key is set')
else:
    print('❌ SendGrid API key is missing or invalid')
"
```

---

## 🔄 Full Service Restart

If all else fails, restart everything:

```bash
cd /opt/voiceframe

# Stop all services
docker-compose -f docker-compose.prod.yml down

# Clean up (optional, removes temp data)
docker system prune -f

# Rebuild and restart
docker-compose -f docker-compose.prod.yml build
docker-compose -f docker-compose.prod.yml up -d

# Check health
docker-compose -f docker-compose.prod.yml ps
docker-compose -f docker-compose.prod.yml logs -f
```

---

## 📝 What to Look For in Logs

When you run the logs command, look for:

### ✅ **Good Signs:**
```
INFO: Payment succeeded: pi_xxx
INFO: File migration completed successfully for order xxx
INFO: PDF generated: pdfs/final_xxx.pdf
INFO: Download email sent to user@example.com
```

### ❌ **Error Signs:**
```
ERROR: File migration failed
ERROR: boto3.exceptions.NoCredentialsError
ERROR: Access Denied
ERROR: Font file not found
ERROR: Template not found
ERROR: SendGrid error
ERROR: Database error
```

---

## 🆘 Emergency Workaround

If you need to manually send the PDF to the customer:

1. **Find the preview PDF** (already generated):
   ```bash
   docker-compose -f docker-compose.prod.yml logs api | grep "preview_"
   ```

2. **Get the S3 URL** and send it manually via email

3. **Refund the payment** in Stripe Dashboard if PDF generation completely fails

---

## 📧 Contact Support Info

If issue persists, provide these details:
- [ ] Full backend logs: `docker-compose logs api > logs.txt`
- [ ] Order ID: `79fa1a45-feff-443f-aaab-e1a7f2dee72c`
- [ ] Environment check: `docker-compose exec api env`
- [ ] Service status: `docker-compose ps`
- [ ] Error message from logs

---

## ✅ Success Checklist

Once fixed, verify:
- [ ] Backend logs show no errors
- [ ] Payment completes successfully
- [ ] PDF is generated
- [ ] Email is sent
- [ ] Download link works
- [ ] No more 500 errors ✅

---

**Next Step**: Run the diagnostic commands above and share the error message from the logs so we can pinpoint the exact issue! 🔍
