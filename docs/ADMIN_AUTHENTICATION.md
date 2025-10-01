# Admin Panel Authentication Guide

The VoiceFrame admin panel supports multiple authentication methods to suit different use cases, from simple development setups to production-ready user management.

## 🎯 Quick Start (Recommended for Development)

The simplest way to get started is with **Simple Password Authentication**:

```bash
# Run the setup script
python3 scripts/setup_admin_auth.py

# Choose option 1 (Simple Password)
# Set your password (default: admin123)
```

Then use it in your requests:
```bash
curl -H "Authorization: Bearer admin123" \
     http://localhost:8000/admin/simple/test
```

## 🔐 Authentication Methods

### 1. Simple Password Authentication (Development)

**Best for:** Development, testing, single-user setups

**Setup:**
```bash
# Add to your .env file
ADMIN_PASSWORD=your-secure-password
```

**Usage:**
```bash
# Test endpoint
curl -H "Authorization: Bearer your-secure-password" \
     http://localhost:8000/admin/simple/test

# Access any admin endpoint
curl -H "Authorization: Bearer your-secure-password" \
     http://localhost:8000/admin/stats
```

**Endpoints:**
- `POST /admin/simple/login` - Login with password
- `GET /admin/simple/test` - Test authentication

### 2. API Key Authentication (Current Method)

**Best for:** API-only access, automated scripts

**Setup:**
```bash
# Add to your .env file
ADMIN_API_KEY=your-secure-api-key
```

**Usage:**
```bash
curl -H "Authorization: Bearer your-secure-api-key" \
     http://localhost:8000/admin/stats
```

**Endpoints:**
- All `/admin/*` endpoints (except auth endpoints)

### 3. JWT Username/Password Authentication (Production)

**Best for:** Production environments, multiple admin users

**Setup:**
```bash
# 1. Run database migrations (if not already done)
# 2. Create admin user
python3 scripts/create_admin_user.py

# 3. Login to get JWT token
curl -X POST http://localhost:8000/admin/auth/login \
     -H "Content-Type: application/json" \
     -d '{"username": "admin", "password": "your-password"}'
```

**Usage:**
```bash
# 1. Login to get token
TOKEN=$(curl -s -X POST http://localhost:8000/admin/auth/login \
     -H "Content-Type: application/json" \
     -d '{"username": "admin", "password": "your-password"}' \
     | jq -r '.access_token')

# 2. Use token for requests
curl -H "Authorization: Bearer $TOKEN" \
     http://localhost:8000/admin/auth/me
```

**Endpoints:**
- `POST /admin/auth/login` - Login with username/password
- `GET /admin/auth/me` - Get current user info
- `POST /admin/auth/users` - Create admin user (superuser only)
- `GET /admin/auth/users` - List admin users (superuser only)
- `PUT /admin/auth/users/{user_id}` - Update admin user
- `DELETE /admin/auth/users/{user_id}` - Delete admin user (superuser only)

## 🛠️ Setup Scripts

### Quick Setup
```bash
python3 scripts/setup_admin_auth.py
```

### Create Admin User (JWT method)
```bash
python3 scripts/create_admin_user.py
```

### Seed Admin Data
```bash
python3 scripts/seed_admin_data.py
```

## 🔧 Configuration

### Environment Variables

Add these to your `.env` file:

```bash
# Simple Password Authentication
ADMIN_PASSWORD=your-secure-password

# API Key Authentication
ADMIN_API_KEY=your-secure-api-key

# JWT Authentication (uses existing SECRET_KEY)
SECRET_KEY=your-jwt-secret-key
```

### Database Setup (JWT method only)

The JWT authentication method requires the `admin_users` table. If you're using Alembic migrations:

```bash
# Create migration
alembic revision --autogenerate -m "Add admin user authentication"

# Apply migration
alembic upgrade head
```

## 📚 API Examples

### Simple Password Authentication

```bash
# Test authentication
curl -H "Authorization: Bearer admin123" \
     http://localhost:8000/admin/simple/test

# Access admin stats
curl -H "Authorization: Bearer admin123" \
     http://localhost:8000/admin/stats
```

### API Key Authentication

```bash
# Access admin stats
curl -H "Authorization: Bearer your-api-key" \
     http://localhost:8000/admin/stats

# List fonts
curl -H "Authorization: Bearer your-api-key" \
     http://localhost:8000/admin/fonts
```

### JWT Authentication

```bash
# Login
curl -X POST http://localhost:8000/admin/auth/login \
     -H "Content-Type: application/json" \
     -d '{"username": "admin", "password": "password123"}'

# Response:
# {
#   "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
#   "token_type": "bearer",
#   "expires_in": 1800,
#   "user": {
#     "id": "123e4567-e89b-12d3-a456-426614174000",
#     "username": "admin",
#     "email": "admin@example.com",
#     "is_superuser": true
#   }
# }

# Use token
curl -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..." \
     http://localhost:8000/admin/auth/me
```

## 🔒 Security Considerations

### Development
- Use Simple Password or API Key authentication
- Set strong passwords/keys
- Don't commit credentials to version control

### Production
- Use JWT authentication with proper user management
- Set strong `SECRET_KEY` for JWT signing
- Implement proper password policies
- Use HTTPS for all admin access
- Consider implementing rate limiting
- Regular security audits

## 🚨 Troubleshooting

### "No module named uvicorn"
```bash
# Install dependencies in virtual environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### "Invalid admin API key"
- Check your `.env` file has `ADMIN_API_KEY` set
- Restart your backend server after changing environment variables
- Verify the API key in the Authorization header

### "Invalid authentication credentials" (JWT)
- Check username/password are correct
- Verify JWT token hasn't expired (30 minutes)
- Ensure user account is active

### Database connection issues
- Check your `DATABASE_URL` in `.env`
- Ensure PostgreSQL is running
- Run database migrations if needed

## 📖 Additional Resources

- [FastAPI Security Documentation](https://fastapi.tiangolo.com/tutorial/security/)
- [JWT.io](https://jwt.io/) - JWT token debugger
- [Postman Collection](docs/postman/) - API testing collection
