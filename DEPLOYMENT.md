# 🚀 Deployment-Dokumentation

## Überblick

Diese Anleitung beschreibt verschiedene Deployment-Optionen für das Chat System und erklärt die notwendigen Konfigurationen.

## Voraussetzungen

### Allgemein
- Python 3.10 oder höher
- Git
- Docker & Docker Compose (für Container-Deployments)
- Kubernetes (für Production Deployments)

### Externe Services (optional)
- PostgreSQL 14+ (für Production)
- Redis 7+ (für Caching)
- Ollama (für AI-Features)
- S3-kompatibler Storage (für File-Uploads)

## Umgebungsvariablen

### Pflicht-Variablen

```bash
# Application
APP_NAME="Chat System"
APP_VERSION="2.0.0"
APP_ENVIRONMENT="production"  # production, staging, development
APP_SECRET_KEY="your-secure-random-secret-key-here"  # WICHTIG: Ändern!

# Server
HOST="0.0.0.0"
PORT=8000

# Database
DATABASE_URL="postgresql://user:password@localhost:5432/chat_system"
# oder für SQLite: "sqlite:///./chat_system.db"
DATABASE_TIMEOUT=30
DATABASE_POOL_SIZE=10
DATABASE_MAX_OVERFLOW=20
```

### Optional-Variablen

```bash
# AI Configuration
AI_ENABLED=true
OLLAMA_BASE_URL="http://localhost:11434"
OLLAMA_DEFAULT_MODEL="llama2"
AI_MAX_RESPONSE_LENGTH=1000
AI_CONTEXT_MESSAGES=10

# Elyza Fallback (Feature Flag)
ENABLE_ELYZA_FALLBACK=true  # Aktiviert regelbasierten Fallback bei AI-Ausfall

# RAG Configuration
RAG_ENABLED=false
VECTOR_STORE_ENABLED=false
CHROMA_PERSIST_DIRECTORY="./chroma_data"

# Redis Cache
REDIS_URL="redis://localhost:6379/0"
REDIS_PASSWORD=""
REDIS_MAX_CONNECTIONS=50

# File Storage
UPLOAD_FOLDER="uploads"
MAX_FILE_SIZE=10485760  # 10 MB in Bytes
STORAGE_REGION="eu-central-1"  # Für S3-kompatible Storages
AWS_ACCESS_KEY_ID=""  # Optional: für S3
AWS_SECRET_ACCESS_KEY=""  # Optional: für S3
S3_BUCKET_NAME=""  # Optional: für S3

# Security
RATE_LIMIT_ENABLED=true
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=60  # Sekunden
CORS_ORIGINS="http://localhost:3000,http://localhost:8000"

# Features
FEATURE_PROJECT_MANAGEMENT=true
FEATURE_TICKET_SYSTEM=true
FEATURE_FILE_UPLOAD=true
FEATURE_USER_AUTHENTICATION=false
WEBSOCKET_ENABLED=true

# Logging
LOG_LEVEL="INFO"  # DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_FORMAT="console"  # console, json
LOG_FILE="logs/chat_system.log"

# Monitoring (optional)
SENTRY_DSN=""  # Optional: für Error Tracking
PROMETHEUS_ENABLED=false
```

### Wichtige Sicherheitshinweise

⚠️ **NIE API-Keys oder Secrets direkt im Code speichern!**

✅ **Best Practices:**
- Verwende `.env` Dateien für lokale Entwicklung (nicht committen!)
- Nutze Kubernetes Secrets für Production
- Rotiere Secrets regelmäßig
- Verwende starke, zufällige Werte für `APP_SECRET_KEY`

## Deployment-Optionen

### 1. Lokale Entwicklung

#### Mit Python Virtual Environment

```bash
# Repository klonen
git clone https://github.com/Thomas-Heisig/chat_system.git
cd chat_system

# Virtual Environment erstellen
python -m venv venv
source venv/bin/activate  # Linux/Mac
# oder
venv\Scripts\activate  # Windows

# Dependencies installieren
pip install -r requirements.txt

# .env Datei erstellen
cp .env.example .env
# .env anpassen mit Editor

# Datenbank initialisieren
python -c "from database.connection import init_database; init_database()"

# Server starten
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

#### Mit Docker Compose

```bash
# Repository klonen
git clone https://github.com/Thomas-Heisig/chat_system.git
cd chat_system

# .env Datei erstellen und anpassen
cp .env.example .env

# Services starten
docker-compose up -d

# Logs verfolgen
docker-compose logs -f

# Services stoppen
docker-compose down
```

Docker Compose startet:
- FastAPI Application (Port 8000)
- PostgreSQL Database (Port 5432)
- Redis Cache (Port 6379)
- Ollama AI (Port 11434, optional)

### 2. Production Deployment mit Docker

#### Single Container

```bash
# Image bauen
docker build -t chat-system:latest .

# Container starten
docker run -d \
  --name chat-system \
  -p 8000:8000 \
  -e DATABASE_URL="postgresql://user:pass@db:5432/chat" \
  -e APP_SECRET_KEY="your-secret-key" \
  -e APP_ENVIRONMENT="production" \
  -e REDIS_URL="redis://redis:6379/0" \
  -e ENABLE_ELYZA_FALLBACK="true" \
  -v /path/to/uploads:/app/uploads \
  -v /path/to/logs:/app/logs \
  chat-system:latest

# Logs anzeigen
docker logs -f chat-system

# Container stoppen
docker stop chat-system
```

#### Mit Docker Compose (Production)

```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  app:
    image: chat-system:latest
    restart: always
    ports:
      - "8000:8000"
    environment:
      - APP_ENVIRONMENT=production
      - DATABASE_URL=postgresql://postgres:password@db:5432/chat_system
      - REDIS_URL=redis://redis:6379/0
      - ENABLE_ELYZA_FALLBACK=true
    depends_on:
      - db
      - redis
    volumes:
      - ./uploads:/app/uploads
      - ./logs:/app/logs
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  db:
    image: postgres:14
    restart: always
    environment:
      POSTGRES_DB: chat_system
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: password
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    restart: always
    volumes:
      - redis_data:/data

volumes:
  postgres_data:
  redis_data:
```

```bash
docker-compose -f docker-compose.prod.yml up -d
```

### 3. Kubernetes Deployment

#### Voraussetzungen
- Kubernetes Cluster (1.24+)
- kubectl konfiguriert
- Container Image in Registry

#### Deployment durchführen

```bash
# Namespace erstellen
kubectl create namespace chat-system

# Secrets erstellen
kubectl create secret generic chat-system-secrets \
  --from-literal=app-secret-key='your-secret-key' \
  --from-literal=db-password='db-password' \
  --from-literal=redis-password='redis-password' \
  -n chat-system

# ConfigMap erstellen
kubectl apply -f k8s/manifests/configmap.yaml -n chat-system

# Deployments anwenden
kubectl apply -f k8s/manifests/database-deployment.yaml -n chat-system
kubectl apply -f k8s/manifests/redis-deployment.yaml -n chat-system
kubectl apply -f k8s/manifests/app-deployment.yaml -n chat-system

# Services erstellen
kubectl apply -f k8s/manifests/services.yaml -n chat-system

# Ingress konfigurieren (optional)
kubectl apply -f k8s/manifests/ingress.yaml -n chat-system

# Status prüfen
kubectl get pods -n chat-system
kubectl get services -n chat-system

# Logs anzeigen
kubectl logs -f deployment/chat-system-api -n chat-system
```

#### Scaling

```bash
# Horizontal skalieren
kubectl scale deployment chat-system-api --replicas=3 -n chat-system

# Autoscaling konfigurieren
kubectl autoscale deployment chat-system-api \
  --cpu-percent=70 \
  --min=2 \
  --max=10 \
  -n chat-system
```

### 4. Cloud-Plattformen

#### AWS (Elastic Beanstalk)

```bash
# EB CLI installieren
pip install awsebcli

# Anwendung initialisieren
eb init -p python-3.10 chat-system

# Environment erstellen
eb create production \
  --instance-type t3.medium \
  --database.engine postgres \
  --envvars APP_ENVIRONMENT=production,ENABLE_ELYZA_FALLBACK=true

# Deployen
eb deploy

# Status
eb status

# Logs
eb logs
```

#### Google Cloud Run

```bash
# Image bauen und pushen
gcloud builds submit --tag gcr.io/PROJECT-ID/chat-system

# Service deployen
gcloud run deploy chat-system \
  --image gcr.io/PROJECT-ID/chat-system \
  --platform managed \
  --region europe-west1 \
  --allow-unauthenticated \
  --set-env-vars "APP_ENVIRONMENT=production,ENABLE_ELYZA_FALLBACK=true"
```

#### Azure (Container Instances)

```bash
# Resource Group erstellen
az group create --name chat-system-rg --location westeurope

# Container Instance erstellen
az container create \
  --resource-group chat-system-rg \
  --name chat-system \
  --image chat-system:latest \
  --cpu 2 \
  --memory 4 \
  --ports 8000 \
  --environment-variables \
    APP_ENVIRONMENT=production \
    ENABLE_ELYZA_FALLBACK=true
```

## Datenbank-Migration

### Initiale Migration

```bash
# Lokal
python -c "from database.connection import init_database; init_database()"

# In Docker Container
docker exec -it chat-system python -c "from database.connection import init_database; init_database()"

# In Kubernetes Pod
kubectl exec -it deployment/chat-system-api -n chat-system -- \
  python -c "from database.connection import init_database; init_database()"
```

### Alembic Migrationen (fortgeschritten)

```bash
# Migration erstellen
alembic revision --autogenerate -m "Add new table"

# Migration anwenden
alembic upgrade head

# Rollback
alembic downgrade -1
```

## Monitoring & Health Checks

### Health Endpoints

```bash
# Basis Health Check
curl http://localhost:8000/health

# Readiness Check (für Kubernetes)
curl http://localhost:8000/health/ready

# Liveness Check (für Kubernetes)
curl http://localhost:8000/health/live
```

### Prometheus Metriken

```bash
# Metriken abrufen (wenn PROMETHEUS_ENABLED=true)
curl http://localhost:8000/metrics
```

### Log-Aggregation

```bash
# Logs in JSON-Format für ELK Stack
LOG_FORMAT=json uvicorn main:app

# Logs an externen Service weiterleiten
docker run -d \
  --log-driver=syslog \
  --log-opt syslog-address=udp://logserver:514 \
  chat-system:latest
```

## Backup & Recovery

### Datenbank-Backup

```bash
# PostgreSQL Backup
pg_dump -h localhost -U postgres -d chat_system > backup.sql

# Restore
psql -h localhost -U postgres -d chat_system < backup.sql

# SQLite Backup
cp chat_system.db chat_system.db.backup
```

### Vollständiges Backup

```bash
# Alle wichtigen Daten sichern
tar -czf backup-$(date +%Y%m%d).tar.gz \
  chat_system.db \
  uploads/ \
  logs/ \
  .env
```

## Troubleshooting

### Häufige Probleme

#### 1. AI Service nicht erreichbar

```bash
# Prüfen ob Ollama läuft
curl http://localhost:11434/api/tags

# Fallback aktivieren
export ENABLE_ELYZA_FALLBACK=true
```

#### 2. Datenbank-Verbindungsfehler

```bash
# PostgreSQL Connection testen
psql -h localhost -U postgres -d chat_system

# Credentials prüfen
echo $DATABASE_URL
```

#### 3. Port bereits belegt

```bash
# Process finden der Port 8000 nutzt
lsof -i :8000

# Process beenden
kill -9 <PID>

# Alternativen Port nutzen
uvicorn main:app --port 8001
```

#### 4. WebSocket-Verbindung schlägt fehl

```bash
# Proxy-Konfiguration prüfen
# Nginx: proxy_set_header Upgrade $http_upgrade;
# Nginx: proxy_set_header Connection "upgrade";

# In Kubernetes: Service-Port richtig mappen
```

### Debug-Modus

```bash
# Ausführliches Logging aktivieren
export LOG_LEVEL=DEBUG
export APP_DEBUG=true

# Server mit Reload starten
uvicorn main:app --reload --log-level debug
```

### Performance-Analyse

```bash
# Mit profiling
python -m cProfile -o profile.stats main.py

# Analyze profile
python -c "import pstats; p = pstats.Stats('profile.stats'); p.sort_stats('cumulative'); p.print_stats(20)"
```

## Sicherheits-Checkliste

- [ ] `APP_SECRET_KEY` geändert und stark gewählt
- [ ] Keine Secrets im Git-Repository
- [ ] HTTPS/TLS konfiguriert (Production)
- [ ] CORS nur für vertrauenswürdige Origins
- [ ] Rate Limiting aktiviert
- [ ] Datenbank-Credentials sicher gespeichert
- [ ] Firewall-Regeln konfiguriert
- [ ] Regelmäßige Updates und Patches
- [ ] Backup-Strategie implementiert
- [ ] Monitoring und Alerting aktiv

## Production-Checkliste

- [ ] Umgebungsvariablen gesetzt
- [ ] Datenbank-Migrationen durchgeführt
- [ ] SSL/TLS-Zertifikate konfiguriert
- [ ] Reverse Proxy (Nginx/Traefik) eingerichtet
- [ ] Logs zentralisiert
- [ ] Monitoring-Dashboard konfiguriert
- [ ] Backup-Automation eingerichtet
- [ ] Health Checks funktionieren
- [ ] Alerting-Regeln definiert
- [ ] Dokumentation aktualisiert
- [ ] Team-Zugriff konfiguriert
- [ ] Disaster Recovery Plan erstellt

## Support

Bei Problemen:
1. Logs prüfen (`logs/chat_system.log`)
2. GitHub Issues durchsuchen
3. Dokumentation konsultieren
4. Issue erstellen mit:
   - Deployment-Methode
   - Fehlermeldung/Logs
   - Umgebungsinformationen
   - Reproduktionsschritte

## Weiterführende Links

- [Docker Dokumentation](https://docs.docker.com/)
- [Kubernetes Dokumentation](https://kubernetes.io/docs/)
- [FastAPI Dokumentation](https://fastapi.tiangolo.com/)
- [PostgreSQL Best Practices](https://wiki.postgresql.org/wiki/Don%27t_Do_This)
