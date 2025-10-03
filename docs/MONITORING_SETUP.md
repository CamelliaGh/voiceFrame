# VoiceFrame Monitoring Setup Guide

## 🚀 Quick Start

### 1. **Start the Monitoring Stack**
```bash
# Run the setup script
./scripts/setup_monitoring.sh
```

### 2. **Access Your Monitoring Tools**
- **Grafana Dashboard**: http://localhost:3001 (admin/admin123)
- **Prometheus**: http://localhost:9090
- **VoiceFrame Metrics**: http://localhost:8000/metrics

### 3. **Quick Health Check**
```bash
# Run a one-time health check
python scripts/monitor_system.py

# Watch mode (refreshes every 30 seconds)
python scripts/monitor_system.py --watch 30

# Save report to file
python scripts/monitor_system.py --save health_report.json
```

## 📊 What's Monitored

### **System Metrics**
- ✅ **Disk Space Usage** - Alerts at 80% and 90%
- ✅ **Memory Usage** - Alerts at 80% and 90%
- ✅ **CPU Usage** - Real-time monitoring
- ✅ **Container Health** - All VoiceFrame containers

### **Application Metrics**
- ✅ **API Response Times** - 95th percentile tracking
- ✅ **Request Rates** - Per endpoint monitoring
- ✅ **Error Rates** - 5xx error tracking
- ✅ **PDF Generation** - Success/failure rates
- ✅ **Audio Processing** - Performance metrics
- ✅ **File Uploads** - Size and success tracking

### **Infrastructure Metrics**
- ✅ **Database Connections** - Active connection monitoring
- ✅ **Cache Performance** - Hit/miss ratios
- ✅ **Container Restarts** - Automatic detection

## 🚨 Alerting

### **Critical Alerts** (Immediate Action Required)
- 🚨 Disk usage > 90%
- 🚨 Memory usage > 90%
- 🚨 API completely down
- 🚨 Database down
- 🚨 All containers stopped

### **Warning Alerts** (Monitor Closely)
- ⚠️ Disk usage > 80%
- ⚠️ Memory usage > 80%
- ⚠️ High API response times (>2s)
- ⚠️ High error rates (>5%)
- ⚠️ Container restarts

## 📈 Grafana Dashboards

### **VoiceFrame Overview Dashboard**
- System health overview
- Request rates and response times
- Error rates and success metrics
- Resource usage (CPU, Memory, Disk)
- Container status
- PDF generation metrics

### **Custom Dashboards**
You can create additional dashboards for:
- Database performance
- Cache performance
- User activity patterns
- Business metrics

## 🔧 Configuration

### **Prometheus Configuration**
- **Scrape Interval**: 15 seconds
- **Evaluation Interval**: 15 seconds
- **Retention**: 200 hours (8+ days)

### **Alert Rules**
Located in `monitoring/alert_rules.yml`:
- Disk space alerts
- Memory alerts
- Container health alerts
- API health alerts
- Database alerts
- Redis alerts

### **Alertmanager Configuration**
Located in `monitoring/alertmanager.yml`:
- Email notifications
- Slack webhooks
- Webhook endpoints

## 🛠️ Advanced Usage

### **Custom Metrics**
Add custom metrics to your application:

```python
from backend.metrics import track_pdf_generation, track_error

# Track PDF generation
@track_pdf_generation
async def generate_pdf():
    # Your PDF generation code
    pass

# Track errors
track_error("validation_error", "pdf_generator")
```

### **Adding New Alerts**
Edit `monitoring/alert_rules.yml`:

```yaml
- alert: CustomAlert
  expr: your_metric_expression
  for: 5m
  labels:
    severity: warning
  annotations:
    summary: "Custom alert triggered"
    description: "Description of the alert"
```

### **Custom Dashboards**
1. Go to Grafana (http://localhost:3001)
2. Click "+" → "Dashboard"
3. Add panels with Prometheus queries
4. Save dashboard

## 🔍 Troubleshooting

### **Common Issues**

#### **Prometheus Can't Scrape Metrics**
```bash
# Check if metrics endpoint is accessible
curl http://localhost:8000/metrics

# Check Prometheus targets
# Go to http://localhost:9090/targets
```

#### **Grafana Can't Connect to Prometheus**
```bash
# Check Prometheus is running
docker-compose -f monitoring/docker-compose.monitoring.yml ps

# Check Prometheus logs
docker-compose -f monitoring/docker-compose.monitoring.yml logs prometheus
```

#### **High Memory Usage**
```bash
# Check container memory usage
docker stats

# Restart containers if needed
docker-compose restart
```

### **Useful Commands**

```bash
# Check all container status
docker-compose ps

# View container logs
docker-compose logs api
docker-compose logs db

# Check disk usage
df -h

# Check memory usage
free -h

# Run health check
python scripts/monitor_system.py

# Clean up Docker resources
./scripts/cleanup.sh
```

## 📱 Mobile Monitoring

### **Grafana Mobile App**
1. Download Grafana mobile app
2. Add server: http://your-server:3001
3. Login with admin/admin123
4. Access dashboards on mobile

### **Alert Notifications**
Configure alert notifications for:
- Email alerts
- Slack notifications
- SMS alerts (via webhook services)

## 🔒 Security Considerations

### **Production Setup**
- Change default Grafana password
- Use HTTPS for all endpoints
- Restrict access to monitoring ports
- Use authentication for Prometheus
- Encrypt alert notifications

### **Access Control**
```bash
# Create read-only user in Grafana
# Go to Configuration → Users → New User
# Set role to "Viewer"
```

## 📊 Performance Optimization

### **Reduce Resource Usage**
- Increase scrape intervals for less critical metrics
- Reduce retention period
- Use recording rules for expensive queries
- Optimize dashboard queries

### **Scale Monitoring**
- Use Prometheus federation for multiple instances
- Implement Prometheus clustering
- Use external storage (InfluxDB, TimescaleDB)

## 🆘 Emergency Procedures

### **Disk Space Critical**
```bash
# Immediate cleanup
./scripts/cleanup.sh

# Check largest files
du -sh /* | sort -hr | head -10

# Clean Docker system
docker system prune -a --volumes
```

### **Memory Critical**
```bash
# Restart containers
docker-compose restart

# Check memory usage
docker stats

# Kill high-memory processes
docker-compose down && docker-compose up -d
```

### **API Down**
```bash
# Check container status
docker-compose ps

# Check logs
docker-compose logs api

# Restart API
docker-compose restart api
```

## 📚 Additional Resources

- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Documentation](https://grafana.com/docs/)
- [Docker Monitoring Best Practices](https://docs.docker.com/config/containers/resource_constraints/)
- [Alertmanager Configuration](https://prometheus.io/docs/alerting/latest/configuration/)

## 🎯 Next Steps

1. **Set up alert notifications** (email, Slack)
2. **Create custom dashboards** for your specific needs
3. **Add business metrics** (user registrations, revenue)
4. **Implement log aggregation** (ELK stack)
5. **Set up automated backups** for monitoring data
