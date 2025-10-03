# Production Deployment Guide

## Preventing Disk Space Issues

### 1. **Resource Management**
- Set memory limits for all containers
- Use separate volumes for persistent data
- Implement automatic cleanup policies

### 2. **Storage Strategy**
- **Database**: Use managed PostgreSQL (AWS RDS, Google Cloud SQL)
- **File Storage**: Use S3, Google Cloud Storage, or Azure Blob
- **Container Storage**: Use ephemeral storage for containers

### 3. **Monitoring & Alerts**
- Set up disk usage alerts (alert at 80% usage)
- Monitor container resource usage
- Implement log rotation

## Production Environment Setup

### Option 1: AWS ECS/Fargate (Recommended)
```yaml
# ecs-task-definition.json
{
  "family": "voiceframe",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "1024",
  "memory": "2048",
  "containerDefinitions": [
    {
      "name": "api",
      "image": "your-registry/voiceframe-api:latest",
      "memory": 1024,
      "essential": true,
      "portMappings": [
        {
          "containerPort": 8000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "DATABASE_URL",
          "value": "postgresql://user:pass@rds-endpoint:5432/voiceframe"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/voiceframe",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
```

### Option 2: Google Cloud Run
```yaml
# cloud-run.yaml
apiVersion: serving.knative.dev/v1
kind: Service
metadata:
  name: voiceframe-api
spec:
  template:
    metadata:
      annotations:
        autoscaling.knative.dev/maxScale: "10"
        run.googleapis.com/memory: "2Gi"
        run.googleapis.com/cpu: "2"
    spec:
      containers:
      - image: gcr.io/your-project/voiceframe-api:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          value: "postgresql://user:pass@cloud-sql-endpoint:5432/voiceframe"
        resources:
          limits:
            memory: "2Gi"
            cpu: "2"
```

### Option 3: Kubernetes
```yaml
# k8s-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: voiceframe-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: voiceframe-api
  template:
    metadata:
      labels:
        app: voiceframe-api
    spec:
      containers:
      - name: api
        image: your-registry/voiceframe-api:latest
        ports:
        - containerPort: 8000
        resources:
          requests:
            memory: "1Gi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "1"
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: voiceframe-secrets
              key: database-url
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
```

## Database Setup

### AWS RDS
```bash
# Create RDS instance
aws rds create-db-instance \
  --db-instance-identifier voiceframe-prod \
  --db-instance-class db.t3.micro \
  --engine postgres \
  --master-username voiceframe \
  --master-user-password your-secure-password \
  --allocated-storage 20 \
  --storage-type gp2 \
  --backup-retention-period 7 \
  --multi-az \
  --storage-encrypted
```

### Google Cloud SQL
```bash
# Create Cloud SQL instance
gcloud sql instances create voiceframe-prod \
  --database-version=POSTGRES_15 \
  --tier=db-f1-micro \
  --region=us-central1 \
  --storage-type=SSD \
  --storage-size=20GB \
  --backup \
  --enable-bin-log
```

## File Storage Setup

### AWS S3
```bash
# Create S3 bucket
aws s3 mb s3://voiceframe-prod-files --region us-east-1

# Set up lifecycle policy for cleanup
aws s3api put-bucket-lifecycle-configuration \
  --bucket voiceframe-prod-files \
  --lifecycle-configuration file://lifecycle.json
```

### Google Cloud Storage
```bash
# Create GCS bucket
gsutil mb gs://voiceframe-prod-files

# Set up lifecycle policy
gsutil lifecycle set lifecycle.json gs://voiceframe-prod-files
```

## Monitoring Setup

### 1. **Health Checks**
```python
# backend/main.py
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }
```

### 2. **Metrics Collection**
```python
# Add to requirements.txt
prometheus-client==0.19.0

# backend/metrics.py
from prometheus_client import Counter, Histogram, generate_latest

REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint'])
REQUEST_DURATION = Histogram('http_request_duration_seconds', 'HTTP request duration')

@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type="text/plain")
```

### 3. **Logging Configuration**
```python
# backend/logging_config.py
import logging
import sys
from pythonjsonlogger import jsonlogger

def setup_logging():
    logHandler = logging.StreamHandler(sys.stdout)
    formatter = jsonlogger.JsonFormatter()
    logHandler.setFormatter(formatter)
    logger = logging.getLogger()
    logger.addHandler(logHandler)
    logger.setLevel(logging.INFO)
```

## Security Considerations

### 1. **Environment Variables**
- Use secrets management (AWS Secrets Manager, Google Secret Manager)
- Never commit secrets to version control
- Rotate secrets regularly

### 2. **Network Security**
- Use VPCs and private subnets
- Implement WAF rules
- Enable DDoS protection

### 3. **Container Security**
- Scan images for vulnerabilities
- Use non-root users in containers
- Keep base images updated

## Backup Strategy

### 1. **Database Backups**
- Automated daily backups
- Point-in-time recovery
- Cross-region backup replication

### 2. **File Backups**
- S3 versioning enabled
- Cross-region replication
- Lifecycle policies for cost optimization

### 3. **Configuration Backups**
- Infrastructure as Code (Terraform, CloudFormation)
- Version control for all configurations
- Regular disaster recovery testing

## Cost Optimization

### 1. **Resource Right-sizing**
- Monitor actual usage and adjust limits
- Use auto-scaling policies
- Implement spot instances for non-critical workloads

### 2. **Storage Optimization**
- Use appropriate storage classes
- Implement lifecycle policies
- Regular cleanup of unused resources

### 3. **Monitoring Costs**
- Set up billing alerts
- Use cost allocation tags
- Regular cost reviews and optimization
