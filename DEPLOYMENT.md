# 🚀 Chat System - Deployment-Dokumentation

## Übersicht

Dieses Dokument beschreibt verschiedene Deployment-Optionen für das Chat System, von lokaler Entwicklung bis hin zu Production-Kubernetes-Deployments.

## Voraussetzungen

### Allgemein
- Docker 24.0+ und Docker Compose 2.0+
- Python 3.10+ (für lokale Entwicklung)
- Git

### Für Kubernetes Deployment
- kubectl
- Helm 3.0+ (optional)
- Kubernetes Cluster (1.25+)

### Für Cloud Deployment
- AWS CLI / gcloud CLI / Azure CLI (je nach Provider)
- Terraform (optional, für Infrastructure as Code)

## Lokale Entwicklung

### Option 1: Docker Compose (Empfohlen)

```bash
# Repository klonen
git clone https://github.com/Thomas-Heisig/chat_system.git
cd chat_system

# Environment-Datei erstellen
cp .env.example .env

# Wichtige Variablen anpassen
nano .env

# System starten
docker-compose up -d

# Logs überprüfen
docker-compose logs -f app

# System stoppen
docker-compose down
```

### Option 2: Lokaler Python-Server

```bash
# Virtuelle Umgebung erstellen
python -m venv venv
source venv/bin/activate  # Linux/Mac
# oder
venv\Scripts\activate     # Windows

# Dependencies installieren
pip install -r requirements.txt

# Datenbank initialisieren
python -c "from database.connection import init_database; init_database()"

# Server starten
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Option 3: DevContainer (VS Code)

```bash
# Öffne Projekt in VS Code
code .

# Drücke F1 und wähle:
# "Dev Containers: Reopen in Container"

# Container wird automatisch gebaut und gestartet
# Alle Dependencies sind vorinstalliert
```

## Umgebungsvariablen

### Minimal-Konfiguration (.env)

```bash
# Application
APP_NAME=ChatSystem
APP_VERSION=1.0.0
APP_ENVIRONMENT=development

# Security
SECRET_KEY=your-very-secure-secret-key-change-this-in-production

# Database
DATABASE_URL=sqlite:///./chat_system.db

# Features
AI_ENABLED=true
ENABLE_ELYZA_FALLBACK=true
WEBSOCKET_ENABLED=true
```

### Production-Konfiguration

```bash
# Application
APP_NAME=ChatSystem
APP_VERSION=1.0.0
APP_ENVIRONMENT=production

# Security
SECRET_KEY=use-a-strong-random-secret-key-here
JWT_SECRET_KEY=another-strong-secret-for-jwt
JWT_ALGORITHM=HS256
JWT_EXPIRATION_MINUTES=60

# Database (PostgreSQL)
DATABASE_URL=postgresql://chatuser:securepassword@postgres:5432/chatdb
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=10

# Redis
REDIS_URL=redis://:password@redis:6379/0
REDIS_MAX_CONNECTIONS=50

# AI Services
OLLAMA_BASE_URL=http://ollama:11434
OPENAI_API_KEY=sk-...
ENABLE_ELYZA_FALLBACK=true

# Storage
STORAGE_TYPE=s3
STORAGE_BUCKET=chat-system-files
STORAGE_REGION=eu-central-1
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key

# Vector Database
VECTOR_DB_TYPE=qdrant
QDRANT_URL=http://qdrant:6333
QDRANT_API_KEY=your-qdrant-key

# Monitoring
SENTRY_DSN=https://...@sentry.io/...
LOG_LEVEL=INFO

# CORS
CORS_ORIGINS=https://yourdomain.com,https://app.yourdomain.com

# Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_PER_MINUTE=100
```

## Docker Deployment

### Single Container

```bash
# Image bauen
docker build -t chat-system:latest .

# Container starten
docker run -d \
  --name chat-system \
  -p 8000:8000 \
  -e DATABASE_URL=sqlite:///./chat_system.db \
  -e SECRET_KEY=your-secret-key \
  -v $(pwd)/data:/app/data \
  chat-system:latest

# Logs ansehen
docker logs -f chat-system

# Container stoppen
docker stop chat-system
docker rm chat-system
```

### Docker Compose (Multi-Container)

Das mitgelieferte `docker-compose.yml` startet:
- FastAPI App
- PostgreSQL
- Redis
- ChromaDB (Vector DB)
- Nginx (Reverse Proxy)

```bash
# Starten
docker-compose up -d

# Status prüfen
docker-compose ps

# Logs aller Services
docker-compose logs -f

# Einzelner Service
docker-compose logs -f app

# Neustart
docker-compose restart app

# Stoppen und aufräumen
docker-compose down -v
```

## Kubernetes Deployment

### Voraussetzungen

```bash
# Namespace erstellen
kubectl create namespace chat-system

# Secrets erstellen
kubectl create secret generic chat-secrets \
  --from-literal=secret-key=your-secret-key \
  --from-literal=jwt-secret=your-jwt-secret \
  --from-literal=database-password=your-db-password \
  --namespace=chat-system
```

### ConfigMap erstellen

```bash
kubectl create configmap chat-config \
  --from-literal=APP_ENVIRONMENT=production \
  --from-literal=DATABASE_URL=postgresql://chatuser:password@postgres:5432/chatdb \
  --from-literal=REDIS_URL=redis://redis:6379/0 \
  --namespace=chat-system
```

### Deployment anwenden

```bash
# Alle Manifeste anwenden
kubectl apply -f k8s/manifests/ --namespace=chat-system

# Oder einzeln
kubectl apply -f k8s/manifests/deployment.yaml --namespace=chat-system
kubectl apply -f k8s/manifests/service.yaml --namespace=chat-system
kubectl apply -f k8s/manifests/ingress.yaml --namespace=chat-system

# Status prüfen
kubectl get pods -n chat-system
kubectl get svc -n chat-system
kubectl get ingress -n chat-system

# Logs ansehen
kubectl logs -f deployment/chat-system -n chat-system

# Pod beschreiben
kubectl describe pod <pod-name> -n chat-system
```

### Scaling

```bash
# Horizontal skalieren
kubectl scale deployment chat-system --replicas=3 -n chat-system

# Auto-Scaling (HPA)
kubectl autoscale deployment chat-system \
  --cpu-percent=70 \
  --min=2 \
  --max=10 \
  -n chat-system
```

### Updates

```bash
# Rolling Update
kubectl set image deployment/chat-system \
  app=chat-system:v1.1.0 \
  -n chat-system

# Update-Status
kubectl rollout status deployment/chat-system -n chat-system

# Rollback
kubectl rollout undo deployment/chat-system -n chat-system
```

## Cloud Provider Deployment

### AWS ECS

```bash
# ECR Repository erstellen
aws ecr create-repository --repository-name chat-system

# Login zu ECR
aws ecr get-login-password --region eu-central-1 | \
  docker login --username AWS --password-stdin \
  <account-id>.dkr.ecr.eu-central-1.amazonaws.com

# Image taggen und pushen
docker tag chat-system:latest \
  <account-id>.dkr.ecr.eu-central-1.amazonaws.com/chat-system:latest
docker push <account-id>.dkr.ecr.eu-central-1.amazonaws.com/chat-system:latest

# ECS Task Definition und Service über AWS Console oder CLI erstellen
```

### Google Cloud Run

```bash
# Zu Google Container Registry pushen
docker tag chat-system:latest gcr.io/<project-id>/chat-system:latest
docker push gcr.io/<project-id>/chat-system:latest

# Deploy zu Cloud Run
gcloud run deploy chat-system \
  --image gcr.io/<project-id>/chat-system:latest \
  --platform managed \
  --region europe-west1 \
  --allow-unauthenticated \
  --set-env-vars DATABASE_URL=...,REDIS_URL=...
```

### Azure Container Instances

```bash
# Login zu Azure
az login

# Container Registry erstellen
az acr create --resource-group chat-rg --name chatregistry --sku Basic

# Image pushen
az acr build --registry chatregistry --image chat-system:latest .

# Container Instance erstellen
az container create \
  --resource-group chat-rg \
  --name chat-system \
  --image chatregistry.azurecr.io/chat-system:latest \
  --dns-name-label chat-system-unique \
  --ports 8000 \
  --environment-variables \
    DATABASE_URL=... \
    REDIS_URL=...
```

## Datenbank-Setup

### PostgreSQL Initialisierung

```bash
# Docker Container
docker run --name postgres \
  -e POSTGRES_USER=chatuser \
  -e POSTGRES_PASSWORD=securepassword \
  -e POSTGRES_DB=chatdb \
  -p 5432:5432 \
  -v postgres_data:/var/lib/postgresql/data \
  -d postgres:15

# Migrations laufen lassen (wenn Alembic konfiguriert)
alembic upgrade head
```

### Redis Setup

```bash
# Docker Container
docker run --name redis \
  -p 6379:6379 \
  -v redis_data:/data \
  -d redis:7-alpine \
  redis-server --appendonly yes --requirepass yourpassword
```

## Health Checks & Monitoring

### Health Check Endpoints

```bash
# Basic Health
curl http://localhost:8000/health

# Detailed Health
curl http://localhost:8000/health/detailed

# Metrics (Prometheus)
curl http://localhost:8000/metrics
```

### Kubernetes Health Probes

Bereits in `k8s/manifests/deployment.yaml` konfiguriert:

```yaml
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

## Backup & Recovery

### Datenbank Backup

```bash
# PostgreSQL
docker exec postgres pg_dump -U chatuser chatdb > backup_$(date +%Y%m%d).sql

# Restore
docker exec -i postgres psql -U chatuser chatdb < backup_20251202.sql
```

### Datei-Backup

```bash
# Uploads sichern
docker cp chat-system:/app/uploads ./backup/uploads_$(date +%Y%m%d)

# Oder mit Volume
docker run --rm \
  -v chat_uploads:/data \
  -v $(pwd)/backup:/backup \
  alpine tar czf /backup/uploads_$(date +%Y%m%d).tar.gz /data
```

## Troubleshooting

### Container startet nicht

```bash
# Logs prüfen
docker logs chat-system

# Container inspizieren
docker inspect chat-system

# In Container shell
docker exec -it chat-system /bin/bash
```

### Kubernetes Pod Probleme

```bash
# Pod Status
kubectl get pods -n chat-system

# Pod Logs
kubectl logs <pod-name> -n chat-system

# Pod beschreiben
kubectl describe pod <pod-name> -n chat-system

# Events ansehen
kubectl get events -n chat-system --sort-by='.lastTimestamp'
```

### Datenbank-Verbindungsprobleme

```bash
# Prüfe ob DB erreichbar ist
docker exec chat-system nc -zv postgres 5432

# Teste Verbindung
docker exec -it chat-system python -c "
from database.connection import check_database_health
print(check_database_health())
"
```

### Performance-Probleme

```bash
# Container Ressourcen prüfen
docker stats chat-system

# Kubernetes Ressourcen
kubectl top pods -n chat-system

# Logs auf Errors durchsuchen
kubectl logs deployment/chat-system -n chat-system | grep ERROR
```

## Sicherheits-Best-Practices

### 1. Secrets Management
- **Niemals** Secrets in Code oder Git
- Nutze Kubernetes Secrets oder Cloud Secret Manager
- Rotiere Secrets regelmäßig

### 2. Network Security
- Verwende private Netzwerke für DB/Redis
- Aktiviere TLS/SSL für alle Verbindungen
- Konfiguriere Network Policies in Kubernetes

### 3. Image Security
- Nutze offizielle Base Images
- Scanne Images auf Vulnerabilities
- Verwende spezifische Tags (nicht `latest`)

### 4. Access Control
- Minimale Berechtigungen (Principle of Least Privilege)
- RBAC in Kubernetes aktivieren
- Audit Logging aktivieren

## CI/CD Integration

Die GitHub Actions Workflows (`.github/workflows/ci.yml`) automatisieren:
- Linting (flake8, black)
- Testing (pytest)
- Docker Image Build
- Deployment zu Staging/Production

```bash
# Manueller Workflow-Trigger
gh workflow run ci.yml
```

## Support & Wartung

### Updates einspielen

```bash
# Git Pull neueste Version
git pull origin main

# Dependencies aktualisieren
pip install -r requirements.txt --upgrade

# Image neu bauen
docker-compose build

# Neu starten
docker-compose up -d
```

### Monitoring Alerts (TODO)

Konfiguriere Alerts für:
- Hohe CPU/Memory-Auslastung
- Database Connection Failures
- High Error Rates
- Disk Space

## Weitere Ressourcen

- [ARCHITECTURE.md](./ARCHITECTURE.md) - Architektur-Details
- [SECURITY.md](./SECURITY.md) - Sicherheits-Guidelines
- [README.md](./README.md) - Projekt-Übersicht
- [GitHub Issues](https://github.com/Thomas-Heisig/chat_system/issues) - Bug Reports & Feature Requests

---
*Letzte Aktualisierung: 2025-12-02*
