# Installation Guide

Comprehensive installation instructions for the Universal Chat System.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Local Installation](#local-installation)
- [Docker Installation](#docker-installation)
- [Production Installation](#production-installation)
- [Verification](#verification)
- [Next Steps](#next-steps)

## Prerequisites

### Required Software

| Software | Minimum Version | Purpose |
|----------|----------------|---------|
| Python | 3.9+ | Application runtime |
| pip | Latest | Package management |
| Git | 2.0+ | Version control |

### Optional Software

| Software | Purpose | Recommended |
|----------|---------|-------------|
| Docker | Containerization | Yes (Production) |
| Docker Compose | Orchestration | Yes (Production) |
| PostgreSQL | Database | Yes (Production) |
| Redis | Caching | Yes (Performance) |
| Ollama | Local AI | Yes (AI Features) |

### System Requirements

**Minimum:**
- CPU: 2 cores
- RAM: 4 GB
- Disk: 10 GB free space
- OS: Linux, macOS, Windows

**Recommended (with AI):**
- CPU: 4+ cores
- RAM: 8+ GB
- Disk: 20+ GB free space
- GPU: Optional (for AI performance)

## Local Installation

### Step 1: Clone Repository

```bash
git clone https://github.com/Thomas-Heisig/chat_system.git
cd chat_system
```

### Step 2: Create Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate on Linux/macOS
source venv/bin/activate

# Activate on Windows
venv\Scripts\activate

# Verify activation
which python  # Should show venv/bin/python
```

### Step 3: Install Dependencies

#### Core Dependencies

```bash
pip install -r requirements.txt
```

#### Optional Dependencies

```bash
# Development dependencies (testing, linting)
pip install -r requirements-dev.txt

# All optional features
pip install -e ".[all]"

# Specific features
pip install -e ".[postgres]"  # PostgreSQL support
pip install -e ".[mongodb]"   # MongoDB support
pip install -e ".[voice]"     # Voice processing
```

### Step 4: Configure Environment

```bash
# Copy example configuration
cp .env.example .env

# Edit configuration
nano .env  # or your preferred editor
```

See [Configuration Guide](configuration.md) for detailed options.

### Step 5: Initialize Database

Database is automatically initialized on first run:

```bash
python main.py
```

Or manually:

```bash
python -c "from database.connection import init_database; init_database()"
```

### Step 6: Verify Installation

```bash
# Check application health
curl http://localhost:8000/health

# Check API documentation
open http://localhost:8000/docs
```

## Docker Installation

### Prerequisites

Install Docker and Docker Compose:

```bash
# Check Docker installation
docker --version
docker-compose --version
```

### Option 1: Docker Compose (Recommended)

This starts all services (app, database, redis, ollama, vector db):

```bash
# Start services
docker-compose up -d

# View logs
docker-compose logs -f app

# Check status
docker-compose ps

# Stop services
docker-compose down
```

**Services started:**
- `app`: Chat System application (port 8000)
- `postgres`: PostgreSQL database (port 5432)
- `redis`: Redis cache (port 6379)
- `ollama`: Ollama AI service (port 11434)
- `chroma`: ChromaDB vector database (port 8001)

### Option 2: Docker Only

Build and run just the application:

```bash
# Build image
docker build -t chat-system:latest .

# Run container
docker run -d \
  --name chat-system \
  -p 8000:8000 \
  -v $(pwd)/uploads:/app/uploads \
  -v $(pwd)/logs:/app/logs \
  -e DATABASE_TYPE=sqlite \
  chat-system:latest

# View logs
docker logs -f chat-system

# Stop container
docker stop chat-system
docker rm chat-system
```

### Option 3: Production Docker Compose

```bash
# Use production compose file
docker-compose -f docker-compose.prod.yml up -d

# Scale workers
docker-compose -f docker-compose.prod.yml up -d --scale app=4

# View logs
docker-compose -f docker-compose.prod.yml logs -f
```

### Docker Environment Configuration

Create `.env` file for Docker:

```bash
# Application
APP_ENVIRONMENT=production
APP_DEBUG=false
APP_SECRET_KEY=your-secret-key-here

# Database
DATABASE_TYPE=postgresql
DATABASE_URL=postgresql://chatuser:chatpass@postgres:5432/chatdb

# Redis
REDIS_URL=redis://redis:6379/0

# Ollama
OLLAMA_URL=http://ollama:11434
AI_ENABLED=true

# Vector Database
VECTOR_DB_TYPE=chroma
CHROMA_URL=http://chroma:8001
```

## Production Installation

### Prerequisites

- Linux server (Ubuntu 20.04+ recommended)
- Domain name with DNS configured
- SSL certificate (Let's Encrypt recommended)
- Firewall configured

### Step 1: Server Preparation

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install dependencies
sudo apt install -y python3.9 python3.9-venv python3-pip git nginx certbot

# Create application user
sudo useradd -m -s /bin/bash chatapp
sudo su - chatapp
```

### Step 2: Application Setup

```bash
# Clone repository
git clone https://github.com/Thomas-Heisig/chat_system.git
cd chat_system

# Create virtual environment
python3.9 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install gunicorn
```

### Step 3: Database Setup

#### PostgreSQL

```bash
# Install PostgreSQL
sudo apt install postgresql postgresql-contrib

# Create database and user
sudo -u postgres psql << EOF
CREATE DATABASE chatdb;
CREATE USER chatuser WITH PASSWORD 'secure-password';
GRANT ALL PRIVILEGES ON DATABASE chatdb TO chatuser;
\q
EOF

# Configure in .env
DATABASE_TYPE=postgresql
DATABASE_URL=postgresql://chatuser:secure-password@localhost:5432/chatdb
```

### Step 4: Systemd Service

Create `/etc/systemd/system/chat-system.service`:

```ini
[Unit]
Description=Universal Chat System
After=network.target postgresql.service

[Service]
Type=notify
User=chatapp
Group=chatapp
WorkingDirectory=/home/chatapp/chat_system
Environment="PATH=/home/chatapp/chat_system/venv/bin"
ExecStart=/home/chatapp/chat_system/venv/bin/gunicorn main:app \
    --workers 4 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:8000 \
    --access-logfile /home/chatapp/chat_system/logs/access.log \
    --error-logfile /home/chatapp/chat_system/logs/error.log
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable chat-system
sudo systemctl start chat-system
sudo systemctl status chat-system
```

### Step 5: Nginx Reverse Proxy

Create `/etc/nginx/sites-available/chat-system`:

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /ws {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

Enable site:

```bash
sudo ln -s /etc/nginx/sites-available/chat-system /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### Step 6: SSL Certificate

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx

# Obtain certificate
sudo certbot --nginx -d your-domain.com

# Auto-renewal is configured automatically
```

## Verification

### Health Check

```bash
# Application health
curl http://localhost:8000/health

# Expected output:
# {"status":"healthy","version":"2.0.0"}
```

### Feature Check

```bash
# Check database
curl http://localhost:8000/status | jq .database

# Check AI service
curl http://localhost:8000/status | jq .ai_service

# Check websocket
wscat -c ws://localhost:8000/ws
```

### Web Interface

1. Open browser: `http://localhost:8000`
2. Login with: `admin` / `admin123`
3. Change password when prompted
4. Explore the interface

### API Documentation

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
- OpenAPI Schema: `http://localhost:8000/openapi.json`

## Next Steps

After successful installation:

1. **[Configuration](configuration.md)** - Configure system settings
2. **[First Steps](first-steps.md)** - Learn basic operations
3. **[User Guide](../02-user-guide/README.md)** - Explore features
4. **[Security](../06-operations/security-practices.md)** - Secure your installation

## Troubleshooting

### Common Issues

**Import Errors**
```bash
# Reinstall dependencies
pip install --upgrade -r requirements.txt
```

**Port Already in Use**
```bash
# Check what's using port 8000
sudo lsof -i :8000

# Kill process or change PORT in .env
```

**Database Connection Failed**
```bash
# Check database service
systemctl status postgresql

# Verify DATABASE_URL in .env
```

**Permission Denied**
```bash
# Fix directory permissions
chmod -R 755 /path/to/chat_system
chown -R chatapp:chatapp /path/to/chat_system
```

For more issues, see [Troubleshooting Guide](../06-operations/troubleshooting.md).

## Uninstallation

### Local Installation

```bash
# Stop application
# Press Ctrl+C if running

# Deactivate virtual environment
deactivate

# Remove directory
cd ..
rm -rf chat_system
```

### Docker Installation

```bash
# Stop and remove containers
docker-compose down -v

# Remove images
docker rmi chat-system:latest
```

### Production Installation

```bash
# Stop service
sudo systemctl stop chat-system
sudo systemctl disable chat-system

# Remove service file
sudo rm /etc/systemd/system/chat-system.service
sudo systemctl daemon-reload

# Remove nginx config
sudo rm /etc/nginx/sites-enabled/chat-system
sudo rm /etc/nginx/sites-available/chat-system
sudo systemctl restart nginx

# Remove application
sudo rm -rf /home/chatapp/chat_system

# Optional: Remove user
sudo userdel -r chatapp
```

---

**Version:** 2.0.0  
**Last Updated:** 2025-12-06  
**Language:** English | [Deutsch](installation.de.md)
