# VoiceFrame - Getting Started Guide

This guide will help you set up and run the VoiceFrame project locally.

## Prerequisites

- Docker and Docker Compose
- Node.js (v16 or higher)
- npm or yarn

## Quick Start

### 1. Start the Backend Services

```bash
# Start all backend services (API, Database, Redis, Celery)
docker-compose up -d
```

This command starts:
- **API** (FastAPI backend) on port 8000
- **Database** (PostgreSQL) on port 5432
- **Redis** (cache/broker) on port 6379
- **Celery Worker** (background tasks)
- **Celery Beat** (scheduled tasks)

### 2. Start the Frontend

```bash
# Install dependencies (first time only)
npm install

# Start the development server
npm run dev
```

The frontend will be available at `http://localhost:5173`

## Alternative Startup Options

### Start Services Individually

```bash
# Start only backend services
docker-compose up -d db redis api celery-worker celery-beat

# Start only the database
docker-compose up -d db

# Start only the API
docker-compose up -d api

# Start only Redis
docker-compose up -d redis
```

### Start with Logs Visible

```bash
# Start with logs in foreground
docker-compose up

# Start specific service with logs
docker-compose up api
```

## Useful Commands

### Service Management

```bash
# Check service status
docker-compose ps

# View logs
docker-compose logs

# View logs for specific service
docker-compose logs api
docker-compose logs celery-worker
docker-compose logs db

# Follow logs in real-time
docker-compose logs -f api

# Restart a service
docker-compose restart api
docker-compose restart celery-worker

# Stop all services
docker-compose down

# Stop and remove volumes (clears database)
docker-compose down -v

# Rebuild and start services
docker-compose up --build -d
```

### Database Management

```bash
# Access database shell
docker-compose exec db psql -U audioposter -d audioposter

# Run database migrations
docker-compose exec api alembic upgrade head

# Create new migration
docker-compose exec api alembic revision --autogenerate -m "Description"
```

### Development Commands

```bash
# Install Python dependencies
docker-compose exec api pip install -r requirements.txt

# Run tests
docker-compose exec api python -m pytest

# Access API container shell
docker-compose exec api bash

# Access Celery worker shell
docker-compose exec celery-worker bash
```

## Environment Configuration

The project uses these environment variables (configured in `docker-compose.yml`):

### Database
- `DATABASE_URL`: PostgreSQL connection string
- `POSTGRES_DB`: Database name (audioposter)
- `POSTGRES_USER`: Database user (audioposter)
- `POSTGRES_PASSWORD`: Database password

### Redis
- `REDIS_URL`: Redis connection string

### AWS S3
- `AWS_ACCESS_KEY_ID`: S3 access key
- `AWS_SECRET_ACCESS_KEY`: S3 secret key
- `S3_BUCKET`: S3 bucket name (audioposter-bucket)
- `S3_REGION`: S3 region (us-east-2)

### Application
- `DEBUG`: Debug mode (true/false)
- `BASE_URL`: Base URL for the application

## Access Points

### Frontend
- **Main App**: http://localhost:5173
- **Development Server**: http://localhost:5173 (with hot reload)

### Backend API
- **API Base**: http://localhost:8000
- **Health Check**: http://localhost:8000/health
- **API Documentation**: http://localhost:8000/docs
- **Interactive API**: http://localhost:8000/redoc

### Database
- **Host**: localhost
- **Port**: 5432
- **Database**: audioposter
- **Username**: audioposter
- **Password**: audioposter_password

### Redis
- **Host**: localhost
- **Port**: 6379

## First Time Setup

### Complete Setup Process

1. **Clone the repository** (if not already done):
   ```bash
   git clone <repository-url>
   cd voiceFrame
   ```

2. **Start backend services**:
   ```bash
   docker-compose up -d
   ```

3. **Wait for services to be healthy**:
   ```bash
   # Check if all services are running
   docker-compose ps
   
   # Check API health
   curl http://localhost:8000/health
   ```

4. **Install frontend dependencies**:
   ```bash
   npm install
   ```

5. **Start the frontend**:
   ```bash
   npm run dev
   ```

6. **Verify everything is working**:
   - Open http://localhost:8000/health (should return `{"status": "healthy"}`)
   - Open http://localhost:5173 (should show the VoiceFrame app)

## Troubleshooting

### Common Issues

#### Services won't start
```bash
# Check Docker is running
docker --version

# Check if ports are available
lsof -i :8000
lsof -i :5432
lsof -i :6379
```

#### Database connection issues
```bash
# Check database logs
docker-compose logs db

# Restart database
docker-compose restart db
```

#### API not responding
```bash
# Check API logs
docker-compose logs api

# Restart API
docker-compose restart api
```

#### Frontend not loading
```bash
# Check if backend is running
curl http://localhost:8000/health

# Check frontend logs in terminal
# Look for proxy errors in browser console
```

#### Celery tasks not processing
```bash
# Check Celery worker logs
docker-compose logs celery-worker

# Restart Celery worker
docker-compose restart celery-worker
```

### Reset Everything

If you need to start completely fresh:

```bash
# Stop all services and remove volumes
docker-compose down -v

# Remove all containers and images
docker-compose down --rmi all

# Rebuild everything
docker-compose up --build -d

# Reinstall frontend dependencies
rm -rf node_modules package-lock.json
npm install
```

## Development Workflow

### Making Changes

1. **Backend changes**: Services will auto-reload when you modify Python files
2. **Frontend changes**: Vite will hot-reload when you modify React files
3. **Database changes**: Create and run migrations
4. **Template changes**: Restart API service to reload templates

### Testing Changes

```bash
# Test API endpoints
curl http://localhost:8000/health

# Test file upload
curl -X POST http://localhost:8000/api/session/test/photo \
  -F "photo=@test-image.jpg"

# Check Celery tasks
docker-compose logs celery-worker
```

## Production Deployment

For production deployment, see the [DEPLOYMENT.md](DEPLOYMENT.md) guide.

## Support

If you encounter issues:

1. Check the logs: `docker-compose logs`
2. Verify all services are running: `docker-compose ps`
3. Check the troubleshooting section above
4. Review the [CHANGELOG.md](CHANGELOG.md) for recent changes
5. Check the [QUICK_REFERENCE.md](QUICK_REFERENCE.md) for common commands

---

**Happy coding! 🚀**

