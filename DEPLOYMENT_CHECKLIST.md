# VoiceFrame Production Deployment Checklist

## Pre-Deployment Requirements

### ✅ Server Requirements
- [ ] Ubuntu 20.04 LTS or 22.04 LTS
- [ ] Minimum 4GB RAM (8GB+ recommended)
- [ ] Minimum 50GB disk space (100GB+ recommended)
- [ ] Docker and Docker Compose installed
- [ ] Node.js 18+ installed
- [ ] Git installed

### ✅ External Services
- [ ] AWS S3 bucket created and configured
- [ ] Stripe account set up with live keys
- [ ] SendGrid account configured
- [ ] Domain name registered (optional)

### ✅ Environment Configuration
- [ ] `.env` file created from `env.example`
- [ ] Database credentials configured
- [ ] AWS S3 credentials configured
- [ ] Stripe keys configured (live keys for production)
- [ ] SendGrid API key configured
- [ ] Secret key generated and configured
- [ ] Admin password set
- [ ] Base URL configured

## Deployment Steps

### ✅ Initial Setup
- [ ] Clone repository to `/opt/voiceframe`
- [ ] Set proper permissions
- [ ] Make scripts executable
- [ ] Run volume setup script

### ✅ Frontend Build
- [ ] Install npm dependencies
- [ ] Build frontend for production
- [ ] Verify build output in `dist/` directory

### ✅ Docker Setup
- [ ] Build Docker images
- [ ] Start services with production compose file
- [ ] Verify all services are healthy
- [ ] Check container logs for errors

### ✅ Database Setup
- [ ] Run Alembic migrations
- [ ] Create admin user
- [ ] Verify database connectivity
- [ ] Test database operations

### ✅ SSL Configuration (Optional)
- [ ] Generate SSL certificates
- [ ] Configure nginx for HTTPS
- [ ] Test SSL configuration
- [ ] Redirect HTTP to HTTPS

### ✅ Monitoring Setup
- [ ] Set up volume monitoring
- [ ] Configure log rotation
- [ ] Set up automated backups
- [ ] Configure health checks

### ✅ Security Hardening
- [ ] Configure firewall (UFW)
- [ ] Set up automatic security updates
- [ ] Review and secure environment variables
- [ ] Configure rate limiting

## Post-Deployment Verification

### ✅ Service Health
- [ ] All containers running and healthy
- [ ] API responding to health checks
- [ ] Database accessible
- [ ] Redis accessible
- [ ] Celery workers processing tasks

### ✅ Application Functionality
- [ ] Frontend loads correctly
- [ ] User registration works
- [ ] File uploads work
- [ ] PDF generation works
- [ ] Email notifications work
- [ ] Payment processing works

### ✅ Performance
- [ ] Response times acceptable (<2s)
- [ ] Memory usage within limits
- [ ] Disk usage monitored
- [ ] No memory leaks detected

### ✅ Monitoring
- [ ] Volume monitoring active
- [ ] Log rotation configured
- [ ] Automated backups working
- [ ] Alert notifications configured

## Volume Management

### Expected Volume Sizes
- **PostgreSQL**: 1-5GB (grows with data)
- **Redis**: 100MB-1GB (cache data)
- **Temp Files**: 0-10GB (auto-cleaned)

### Volume Monitoring Commands
```bash
# Check current usage
./scripts/monitor-volumes.sh

# Clean up old files
./scripts/cleanup-volumes.sh

# Watch mode
./scripts/monitor-volumes.sh --watch
```

## Troubleshooting

### Common Issues
- [ ] **Out of disk space**: Run cleanup scripts
- [ ] **Services won't start**: Check logs and environment
- [ ] **Database connection issues**: Verify credentials
- [ ] **SSL certificate issues**: Check certificate paths

### Useful Commands
```bash
# Check service status
docker-compose -f docker-compose.prod.yml ps

# View logs
docker-compose -f docker-compose.prod.yml logs -f

# Check disk usage
df -h

# Monitor volumes
./scripts/monitor-volumes.sh

# Run backup
./scripts/backup.sh
```

## Maintenance Schedule

### Daily
- [ ] Check service health
- [ ] Monitor disk usage
- [ ] Review error logs

### Weekly
- [ ] Run volume cleanup
- [ ] Check backup status
- [ ] Review performance metrics

### Monthly
- [ ] Update system packages
- [ ] Review security logs
- [ ] Test disaster recovery

## Emergency Contacts

- **System Administrator**: [Your contact info]
- **Database Administrator**: [Your contact info]
- **External Services**:
  - AWS Support: [Contact info]
  - Stripe Support: [Contact info]
  - SendGrid Support: [Contact info]

## Notes

- Keep this checklist updated as you make changes
- Document any custom configurations
- Record any issues and their solutions
- Update contact information as needed
