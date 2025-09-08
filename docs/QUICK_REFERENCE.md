# AudioPoster - Quick Reference Guide

## 🚨 Critical Requirements (Never Change)

1. **Permanent Audio Storage**: Audio files linked via QR codes MUST remain accessible indefinitely
   - Posters are printed and used as wall frames
   - Files cannot be deleted
   - Use permanent S3 URLs or CloudFront distribution

2. **Fixed Pricing Model**: $2.99 for all users and templates
   - No premium tiers
   - All templates available to everyone
   - Simplified user experience

## 🔧 Current System Status

### ✅ Working Components
- FastAPI backend with Docker
- React frontend with TypeScript
- PostgreSQL database with Alembic
- Redis + Celery for background tasks
- Audio processing and waveform generation
- PDF generation (code-based and visual templates)
- Stripe payment integration
- Visual template system (Canva/Figma support)

### 🎨 Available Templates
- **Modern**: Clean design with purple accents
- **Classic**: Traditional layout
- **Vintage**: Retro aesthetic
- **Elegant**: Sophisticated design

## 🚀 Quick Commands

### Start the System
```bash
docker-compose up -d
```

### Check Status
```bash
docker-compose ps
```

### View Logs
```bash
docker-compose logs api
docker-compose logs celery-worker
```

### Restart Services
```bash
docker-compose restart api
docker-compose restart celery-worker
```

## 🔑 Environment Variables

### Required for S3
```bash
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret
S3_BUCKET=audioposter-bucket
S3_REGION=us-east-2
```

### Quick S3 Bucket Policy
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "PublicReadForPreviewFiles",
            "Effect": "Allow",
            "Principal": "*",
            "Action": "s3:GetObject",
            "Resource": "arn:aws:s3:::audioposter-bucket/*"
        }
    ]
}
```
**Replace**: `audioposter-bucket` with your actual bucket name

### Required for Stripe
```bash
STRIPE_SECRET_KEY=your_stripe_key
STRIPE_WEBHOOK_SECRET=your_webhook_secret
```

## 📁 Key File Locations

- **Backend**: `backend/`
- **Frontend**: `src/`
- **Templates**: `templates/`
- **Database**: `alembic/`
- **Docker**: `docker-compose.yml`

## 🐛 Common Issues & Fixes

### 1. Celery Not Processing Tasks
- Check if worker is running: `docker-compose ps celery-worker`
- Restart worker: `docker-compose restart celery-worker`

### 2. API Not Responding
- Check container status: `docker-compose ps api`
- Restart API: `docker-compose restart api`

### 3. Database Connection Issues
- Check if database is healthy: `docker-compose ps db`
- Run migrations: `docker-compose exec api alembic upgrade head`

### 4. File Upload Errors
- Check S3 credentials in environment
- Verify S3 bucket permissions
- Check local storage directory permissions

## 🔄 Development Workflow

1. **Make Changes** to code
2. **Restart Services** if needed: `docker-compose restart api`
3. **Test Endpoints** with curl or frontend
4. **Check Logs** for errors: `docker-compose logs api`

## 📱 Testing Checklist

- [ ] Photo upload works
- [ ] Audio upload and processing works
- [ ] Template selection works
- [ ] PDF preview generation works
- [ ] Payment processing works
- [ ] Order completion works
- [ ] Permanent audio access works

## 🎯 Next Development Priorities

1. **Template System**: Add more visual templates
2. **Audio Features**: Support more formats, custom waveforms
3. **User Experience**: Template previews, drag-and-drop
4. **Performance**: CDN integration, caching optimization

---

**Remember**: Always check the full `CHANGELOG.md` for detailed implementation history and decisions.
