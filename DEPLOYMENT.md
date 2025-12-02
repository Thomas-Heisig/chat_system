# 🚀 Deployment Guide

Umfassender Leitfaden für das Deployment des Chat Systems in verschiedenen Umgebungen.

## Inhaltsverzeichnis

- [Voraussetzungen](#voraussetzungen)
- [Lokales Development](#lokales-development)
- [Docker Deployment](#docker-deployment)
- [Kubernetes Deployment](#kubernetes-deployment)
- [Cloud Deployment](#cloud-deployment)
- [Konfiguration](#konfiguration)
- [Monitoring](#monitoring)
- [Troubleshooting](#troubleshooting)

## Voraussetzungen

### Minimum Requirements
- Python 3.9+
- 2 GB RAM
- 10 GB Disk Space
- PostgreSQL 13+ oder SQLite

### Empfohlene Requirements
- Python 3.11
- 8 GB RAM
- 50 GB Disk Space
- PostgreSQL 15
- Redis 7
- 4 CPU Cores

## Lokales Development

### 1. Repository klonen

```bash
git clone https://github.com/Thomas-Heisig/chat_system.git
cd chat_system
```

### 2. Virtuelle Umgebung erstellen

```bash
python -m venv venv
source venv/bin/activate  # Linux/MacOS
# oder
venv\Scripts\activate  # Windows
```

### 3. Dependencies installieren

```bash
pip install -r requirements.txt
```

### 4. Umgebungsvariablen konfigurieren

```bash
cp .env.example .env
# Bearbeiten Sie .env mit Ihren Einstellungen
```

### 5. Datenbank initialisieren

```bash
# SQLite (Standard)
python -c "from database.connection import init_database; init_database()"

# PostgreSQL
export DATABASE_URL="postgresql://user:pass@localhost:5432/chatdb"
python -c "from database.connection import init_database; init_database()"
```

### 6. Anwendung starten

```bash
python main.py
```

Die Anwendung läuft auf http://localhost:8000

## Docker Deployment

### Mit Docker Compose (Empfohlen)

```bash
# Alle Services starten
docker-compose up -d

# Logs verfolgen
docker-compose logs -f

# Services stoppen
docker-compose down
```

### Einzelner Container

```bash
# Image bauen
docker build -t chat-system:latest .

# Container starten
docker run -d \
  --name chat-system \
  -p 8000:8000 \
  -v $(pwd)/uploads:/app/uploads \
  -v $(pwd)/logs:/app/logs \
  --env-file .env \
  chat-system:latest
```

### Docker Compose Konfiguration

```yaml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://postgres:password@db:5432/chatdb
      - REDIS_URL=redis://redis:6379/0
    volumes:
      - ./uploads:/app/uploads
      - ./logs:/app/logs
    depends_on:
      - db
      - redis
    restart: unless-stopped

  db:
    image: postgres:15
    environment:
      POSTGRES_DB: chatdb
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    restart: unless-stopped

volumes:
  postgres_data:
```

## Kubernetes Deployment

### 1. Namespace erstellen

```bash
kubectl create namespace chat-system
```

### 2. Secrets erstellen

```bash
kubectl create secret generic chat-system-secrets \
  --from-env-file=.env \
  --namespace=chat-system
```

### 3. ConfigMap erstellen

```yaml
# configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: chat-system-config
  namespace: chat-system
data:
  APP_NAME: "Chat System"
  APP_ENVIRONMENT: "production"
  HOST: "0.0.0.0"
  PORT: "8000"
```

```bash
kubectl apply -f configmap.yaml
```

### 4. Deployment erstellen

```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: chat-system
  namespace: chat-system
spec:
  replicas: 3
  selector:
    matchLabels:
      app: chat-system
  template:
    metadata:
      labels:
        app: chat-system
    spec:
      containers:
      - name: chat-system
        image: your-registry/chat-system:latest
        ports:
        - containerPort: 8000
        envFrom:
        - configMapRef:
            name: chat-system-config
        - secretRef:
            name: chat-system-secrets
        resources:
          requests:
            memory: "1Gi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "1000m"
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
          initialDelaySeconds: 10
          periodSeconds: 5
```

```bash
kubectl apply -f deployment.yaml
```

### 5. Service erstellen

```yaml
# service.yaml
apiVersion: v1
kind: Service
metadata:
  name: chat-system
  namespace: chat-system
spec:
  selector:
    app: chat-system
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8000
  type: LoadBalancer
```

```bash
kubectl apply -f service.yaml
```

### 6. Horizontal Pod Autoscaler

```yaml
# hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: chat-system-hpa
  namespace: chat-system
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: chat-system
  minReplicas: 3
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

```bash
kubectl apply -f hpa.yaml
```

## Cloud Deployment

### AWS (EC2 + RDS)

```bash
# 1. RDS PostgreSQL erstellen
aws rds create-db-instance \
  --db-instance-identifier chat-system-db \
  --db-instance-class db.t3.medium \
  --engine postgres \
  --allocated-storage 50 \
  --master-username admin \
  --master-user-password YourPassword

# 2. EC2 Instance starten
# Verwenden Sie AWS Console oder CLI

# 3. Application deployen
scp -r . ec2-user@your-instance-ip:/opt/chat-system
ssh ec2-user@your-instance-ip
cd /opt/chat-system
docker-compose up -d
```

### Google Cloud Platform (GKE)

```bash
# 1. GKE Cluster erstellen
gcloud container clusters create chat-system \
  --num-nodes=3 \
  --machine-type=n1-standard-2 \
  --region=europe-west1

# 2. Credentials holen
gcloud container clusters get-credentials chat-system \
  --region=europe-west1

# 3. Deployen
kubectl apply -f k8s/
```

### Azure (AKS)

```bash
# 1. Resource Group erstellen
az group create --name chat-system-rg --location westeurope

# 2. AKS Cluster erstellen
az aks create \
  --resource-group chat-system-rg \
  --name chat-system-aks \
  --node-count 3 \
  --node-vm-size Standard_D2_v3 \
  --enable-addons monitoring \
  --generate-ssh-keys

# 3. Credentials holen
az aks get-credentials \
  --resource-group chat-system-rg \
  --name chat-system-aks

# 4. Deployen
kubectl apply -f k8s/
```

## Konfiguration

### Wichtige Umgebungsvariablen

```bash
# Application
APP_NAME="Chat System"
APP_ENVIRONMENT=production
APP_DEBUG=false
SECRET_KEY="change-me-in-production"

# Server
HOST=0.0.0.0
PORT=8000
WORKERS=4

# Database
DATABASE_URL=postgresql://user:pass@host:5432/db

# Redis
REDIS_URL=redis://host:6379/0

# AI Services
AI_ENABLED=true
OLLAMA_URL=http://ollama:11434
OPENAI_API_KEY=sk-...

# Voice
WHISPER_ENABLED=true
TTS_ENABLED=true

# Security
JWT_SECRET_KEY="change-me"
CORS_ORIGINS=["https://yourdomain.com"]

# Monitoring
LOG_LEVEL=INFO
SENTRY_DSN=https://...
```

### Feature Flags

```bash
# Multi-Agent System
FEATURE_MULTIAGENT=true

# Voice & Audio
FEATURE_VOICE=true

# Workflow Automation
FEATURE_WORKFLOWS=true

# ELYZA Fallback
ENABLE_ELYZA_FALLBACK=true
```

## Monitoring

### Prometheus Metrics

```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'chat-system'
    static_configs:
      - targets: ['chat-system:8000']
    metrics_path: '/metrics'
```

### Grafana Dashboards

Importieren Sie vorkonfigurierte Dashboards aus `monitoring/grafana/`

### Logging

```bash
# Logs ansehen (Docker)
docker-compose logs -f app

# Logs ansehen (Kubernetes)
kubectl logs -f deployment/chat-system -n chat-system

# Logs aggregieren (ELK Stack)
# Konfiguration in docker-compose.elk.yml
```

## Troubleshooting

### Application startet nicht

```bash
# Prüfen Sie Logs
docker-compose logs app

# Prüfen Sie Umgebungsvariablen
docker-compose config

# Testen Sie Datenbankverbindung
psql -h localhost -U postgres -d chatdb
```

### Hohe CPU-Auslastung

```bash
# Prüfen Sie laufende Prozesse
docker stats

# Reduzieren Sie Worker-Anzahl
export WORKERS=2
```

### Speicherprobleme

```bash
# Prüfen Sie Memory Usage
docker stats

# Erhöhen Sie Container-Limits
docker-compose up -d --scale app=1 --no-recreate
```

### Datenbank-Migration

```bash
# Backup erstellen
pg_dump chatdb > backup.sql

# Migration durchführen
alembic upgrade head

# Bei Fehler: Rollback
alembic downgrade -1
```

## Backup & Recovery

### Datenbank Backup

```bash
# PostgreSQL
pg_dump -h localhost -U postgres chatdb > backup_$(date +%Y%m%d).sql

# Restore
psql -h localhost -U postgres chatdb < backup_20240101.sql
```

### File Uploads Backup

```bash
# Backup
tar -czf uploads_backup.tar.gz uploads/

# Restore
tar -xzf uploads_backup.tar.gz
```

## Performance-Tuning

### Database Optimization

```sql
-- Indexes erstellen
CREATE INDEX idx_messages_created ON messages(created_at);
CREATE INDEX idx_messages_user ON messages(user_id);

-- Vacuum
VACUUM ANALYZE;
```

### Caching

```python
# Redis Cache konfigurieren
CACHE_ENABLED=true
CACHE_TTL=3600
```

### Load Balancing

```nginx
# nginx.conf
upstream chat_system {
    server chat-system-1:8000;
    server chat-system-2:8000;
    server chat-system-3:8000;
}

server {
    listen 80;
    location / {
        proxy_pass http://chat_system;
    }
}
```

## Sicherheit

### SSL/TLS

```bash
# Let's Encrypt
certbot --nginx -d yourdomain.com
```

### Firewall

```bash
# UFW
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw enable
```

### Updates

```bash
# System updates
apt update && apt upgrade -y

# Python dependencies
pip install --upgrade -r requirements.txt

# Docker images
docker-compose pull
docker-compose up -d
```

## Support

Bei Problemen:
1. Prüfen Sie die Logs
2. Suchen Sie in GitHub Issues
3. Erstellen Sie ein Issue mit Details
4. Kontaktieren Sie support@chatsystem.example.com
