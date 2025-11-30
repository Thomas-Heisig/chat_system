🚀 Universal Chat System
Ein hochmodernes, modulares Chat-System mit KI-Integration, RAG-Funktionalität und Enterprise-Features.

✨ Features
🔥 Kernfunktionen
Echtzeit-Chat mit WebSocket-Verbindungen

KI-Integration mit Ollama/OpenAI Support

Modulares RAG-System mit mehreren Vector-Datenbanken

Pluggable Database Adapters (SQLite, PostgreSQL, MongoDB)

RESTful API für erweiterte Funktionalitäten

Admin Dashboard mit Tab-basierter Konfiguration

🛡️ Enterprise Features
JWT Authentifizierung mit bcrypt Passwort-Hashing

Umfassendes Logging mit verschiedenen Levels

Rate Limiting für API-Endpoints

CORS-Konfiguration für Cross-Origin Requests

Health Monitoring mit System-Metriken

Docker Support mit Multi-Service Setup

📊 RAG System
Multiple Vector Databases: ChromaDB, Qdrant, Pinecone

Dokumenten-Verarbeitung mit konfigurierbarem Chunking

Embedding-Modell Auswahl

Semantische Suche mit Cosine Similarity

Dokumenten-Management mit Upload und Indexierung

🎨 Admin Dashboard
Chat Interface mit Echtzeit-Nachrichten

System Einstellungen Konfiguration

RAG System Management

Datenbank Administration

Benutzer & Auth Verwaltung

Monitoring & Logs Dashboard

🏗️ Projektstruktur
text
universal-chat-system/
├── 🐍 main.py                          # Hauptanwendung
├── 📋 requirements.txt                 # Python-Abhängigkeiten
├── 🔧 .env.example                     # Umgebungsvariablen Template
├── 🐳 docker-compose.yml              # Multi-Service Docker Setup
├── 🐳 Dockerfile                      # Multi-Stage Container Build
├── 📊 docs/
│   └── 📖 API.md                      # API-Dokumentation
├── ⚙️ config/
│   ├── __init__.py
│   ├️ settings.py                     # Zentrale Konfiguration
│   ├️ validation.py                   # Einstellungsvalidierung
│   └️ database_config.py              # Modulare DB-Konfiguration
├── 🗄️ database/
│   ├── __init__.py
│   ├── 🔗 connection.py               # Datenbankverbindung
│   ├── 📐 models.py                   # SQLAlchemy Modelle
│   ├── 📂 repositories.py             # Datenbank-Operationen
│   └── 🔌 adapters/                   # Modulare DB-Adapter
│       ├── __init__.py
│       ├── base_adapter.py            # Abstract Base Adapter
│       ├── sqlite_adapter.py          # SQLite Implementation
│       ├── postgres_adapter.py        # PostgreSQL Implementation
│       └── mongodb_adapter.py         # MongoDB Implementation
├── 🔌 websocket/
│   ├── __init__.py
│   ├── 👥 manager.py                  # Connection-Management
│   └── 🎯 handlers.py                 # WebSocket-Nachrichten
├── 🛣️ routes/
│   ├── __init__.py
│   ├── 💬 chat.py                     # Chat-UI Routes
│   ├── 📨 messages.py                 # API Message Routes
│   ├── ⚙️ settings.py                # Settings Management API
│   ├── 📚 rag.py                      # RAG System API
│   ├── 🗄️ database.py                # Database Admin API
│   └── 👨‍💼 admin.py                  # Admin Dashboard API
├── 🛠️ services/
│   ├── __init__.py
│   ├── 🤖 ai_service.py               # Ollama/OpenAI Integration
│   ├── 🔐 auth_service.py             # JWT & Password Hashing
│   ├── ⚙️ settings_service.py         # Runtime Configuration
│   ├── 📨 message_service.py          # Nachrichten Business-Logik
│   ├── 📁 file_service.py             # File Upload & Management
│   ├── 📋 project_service.py          # Projekt & Ticket Management
│   └── 📚 rag/                        # Modulares RAG-System
│       ├── __init__.py
│       ├── base_rag.py                # Base RAG Provider Interface
│       ├── chroma_rag.py              # ChromaDB Implementation
│       ├── qdrant_rag.py              # Qdrant Implementation
│       └── document_processor.py      # Dokumenten-Verarbeitung
├── 🎨 templates/
│   ├── 🏠 base.html                   # Base Template
│   ├── 🏠 index.html                  # Haupt-App mit Tabs
│   └── 🔧 components/                 # UI Components
│       ├── 💬 chat.html               # Chat Interface
│       ├── ⚙️ settings.html           # Settings Panel
│       ├── 📚 rag.html                # RAG Configuration
│       ├── 🗄️ database.html           # Database Management
│       ├── 📋 projects.html           # Project Management
│       ├── 📁 files.html              # File Manager
│       ├── 👥 users.html              # User Management
│       ├── 📊 monitoring.html         # Monitoring Dashboard
│       └── 🔗 integrations.html       # Integration Settings
├── ⚡ static/
│   ├── 🎨 css/
│   │   ├── 🎨 main.css                # Haupt-Stylesheet
│   │   ├── 🎨 tabs.css                # Tab Navigation
│   │   ├── 🎨 components.css          # UI Components
│   │   └── 🎨 themes.css              # Dark/Light Themes
│   ├── ⚡ js/
│   │   ├── ⚡ app.js                   # Haupt-App Logik
│   │   ├── 🔌 websocket.js            # WebSocket Client
│   │   ├── ⚙️ settings.js             # Settings Management
│   │   ├── 📚 rag.js                  # RAG System Interface
│   │   ├── 🗄️ database.js             # Database Admin
│   │   └── 🔧 api.js                  # API Client
│   └── 🖼️ images/
├── 📁 uploads/                        # File Upload Directory
├── 🧪 tests/                          # Test Suite
│   ├── __init__.py
│   ├── test_api.py
│   ├── test_services.py
│   └── test_rag.py
└── 📝 logs/                           # Application Logs
🚀 Installation & Setup
Voraussetzungen
Python 3.9+

pip (Python Package Manager)

Docker & Docker Compose (optional)

1. Lokale Installation
bash
# Repository klonen
git clone <repository-url>
cd universal-chat-system

# Virtuelle Umgebung erstellen und aktivieren
python -m venv chat_env
source chat_env/bin/activate  # Linux/MacOS
# oder
chat_env\Scripts\activate     # Windows

# Abhängigkeiten installieren
pip install -r requirements.txt
2. Konfiguration anpassen
bash
# Umgebungsvariablen konfigurieren
cp .env.example .env
# .env Datei mit Editor anpassen
3. Mit Docker (Empfohlen)
bash
# Alle Services starten (App, PostgreSQL, Redis, Ollama, ChromaDB)
docker-compose up -d

# Nur bestimmte Services
docker-compose up app db redis -d
⚙️ Konfiguration
Umgebungsvariablen (.env)
env
# APP KONFIGURATION
APP_NAME=Universal Chat System
APP_ENVIRONMENT=development
APP_DEBUG=true
APP_SECRET_KEY=your-super-secret-key-change-in-production

# SERVER KONFIGURATION
HOST=0.0.0.0
PORT=8000
RELOAD=true

# DATENBANK
DATABASE_TYPE=sqlite  # sqlite, postgresql, mongodb
DATABASE_URL=sqlite:///./chat.db
POSTGRES_URL=postgresql://user:pass@localhost:5432/chatdb
MONGODB_URL=mongodb://localhost:27017/chatdb

# VECTOR DATABASE (RAG)
VECTOR_DB_TYPE=chroma  # chroma, qdrant, pinecone
CHROMA_DB_PATH=./chroma_db
QDRANT_URL=http://localhost:6333

# AI KONFIGURATION
AI_ENABLED=true
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=llama2
OPENAI_API_KEY=your-openai-key

# SICHERHEIT
JWT_SECRET_KEY=your-jwt-secret-key
JWT_ALGORITHM=HS256
CORS_ORIGINS=["http://localhost:3000", "http://127.0.0.1:3000"]
RATE_LIMIT_ENABLED=true

# LOGGING
LOG_LEVEL=INFO
LOG_FILE=logs/chat_system.log
Verfügbare Log-Levels
DEBUG - Detaillierte Debug-Informationen

INFO - Allgemeine Betriebsinformationen

WARNING - Warnungen und Fehler

ERROR - Kritische Fehler

🎯 Start der Anwendung
Entwicklungsumgebung
bash
python main.py
Produktionsumgebung
bash
# .env anpassen für Production
APP_ENVIRONMENT=production
APP_DEBUG=false
RELOAD=false

# Server starten
python main.py
Docker Production
bash
docker-compose -f docker-compose.prod.yml up -d
🌐 Zugriff
Nach dem Start sind folgende Endpoints verfügbar:

Endpoint	Beschreibung	Typ
http://localhost:8000/	Admin Dashboard	Web UI
http://localhost:8000/health	Health-Check	JSON API
http://localhost:8000/status	Detaillierter Systemstatus	JSON API
http://localhost:8000/docs	API Dokumentation (Swagger)	Web UI
ws://localhost:8000/ws	WebSocket Endpoint	WebSocket
📡 API Endpoints
Health & Monitoring
http
GET /health
GET /status
GET /info
Chat & Messages
http
GET /api/messages
GET /api/messages/recent
GET /api/messages/user/{username}
GET /api/messages/stats
POST /api/messages
RAG System
http
GET /api/rag/status
POST /api/rag/documents
GET /api/rag/documents
DELETE /api/rag/documents/{doc_id}
POST /api/rag/query
Settings Management
http
GET /api/settings/general
PUT /api/settings/general
GET /api/settings/ai  
PUT /api/settings/ai
GET /api/settings/rag
PUT /api/settings/rag
Database Administration
http
GET /api/database/status
POST /api/database/backup
POST /api/database/optimize
GET /api/database/stats
🎨 Admin Dashboard
Tab Übersicht
💬 Chat - Echtzeit-Chat Interface mit KI-Integration

⚙️ Settings - Systemkonfiguration und Einstellungen

📚 RAG System - Vector Database Management

🗄️ Database - Datenbank Administration

📋 Projects - Projekt und Ticket Management

📁 Files - Dateimanager und Uploads

👥 Users - Benutzerverwaltung und Authentifizierung

📊 Monitoring - System-Monitoring und Logs

🔗 Integrations - Externe Integrationen

🔌 RAG System Provider
Unterstützte Vector Databases
ChromaDB (Lokal) - Einfache Einrichtung, gut für Entwicklung

Qdrant (Cloud/self-hosted) - Production-grade mit erweiterten Features

Pinecone (Cloud) - Vollständig managed Service

Dokumenten-Verarbeitung
Automatisches Chunking mit konfigurierbarer Größe

Overlap für bessere Kontexterhaltung

Multiple Dateiformate: PDF, DOCX, TXT, MD

Embedding Generation mit Sentence Transformers

🗄️ Datenbank Adapter
Unterstützte Datenbanken
SQLite (Standard) - Einfache Entwicklung

PostgreSQL - Production-ready mit erweiterten Features

MongoDB - Document-based für flexible Schemata

Migration zwischen Datenbanken
bash
# Export von SQLite zu PostgreSQL
curl -X POST http://localhost:8000/api/database/migrate \
  -H "Content-Type: application/json" \
  -d '{"source": "sqlite", "target": "postgresql"}'
🐳 Docker Setup
Services im Docker Compose
app - Hauptanwendung

db - PostgreSQL Datenbank

redis - Caching und Sessions

ollama - Lokale LLM Integration

chromadb - Vector Database

qdrant - Alternative Vector Database

Starten bestimmter Services
bash
# Nur App und PostgreSQL
docker-compose up app db -d

# Vollständiges Setup mit AI
docker-compose up app db redis ollama chromadb -d

# Production Setup
docker-compose -f docker-compose.prod.yml up -d
🔧 Entwicklung
Projektstruktur erweitern
bash
# Neuen RAG Provider hinzufügen
touch services/rag/pinecone_rag.py

# Neue Route erstellen
touch routes/analytics.py

# Neues Service erstellen
touch services/analytics_service.py
Tests ausführen
bash
# Unit Tests
python -m pytest tests/

# Mit Coverage
python -m pytest --cov=app tests/

# Spezifische Tests
python -m pytest tests/test_rag.py -v
Logs einsehen
bash
# Log-Datei anzeigen
tail -f logs/chat_system.log

# Docker Logs
docker-compose logs -f app

# System Status im Browser
curl http://localhost:8000/status | jq
🐛 Problembehandlung
Häufige Probleme
WebSocket-Verbindung fehlgeschlagen

Firewall-Einstellungen prüfen

Port 8000 freigeben

WebSocket Support im Browser prüfen

Datenbank-Fehler

Berechtigungen für Datenbank-Datei prüfen

Connection String validieren

Datenbank-Service läuft (bei PostgreSQL/MongoDB)

RAG System initialisiert nicht

Vector Database Service läuft

Embedding-Modell verfügbar

Ausreichend Speicherplatz

Debug-Modus aktivieren
env
APP_DEBUG=true
LOG_LEVEL=DEBUG
📈 Monitoring & Metriken
System-Health
bash
curl http://localhost:8000/status
Antwort beinhaltet:

Speichernutzung und CPU-Auslastung

Aktive WebSocket-Verbindungen

Datenbank-Statistiken

RAG System Status

Service Health Checks

Log-Analyse
bash
# Fehler anzeigen
grep "ERROR" logs/chat_system.log

# WebSocket-Aktivität
grep "WebSocket" logs/chat_system.log

# Performance-Metriken
grep "Time:" logs/chat_system.log

# RAG System Aktivität
grep "RAG" logs/chat_system.log
🤝 Beitragen
Repository forken

Feature-Branch erstellen: git checkout -b feature/NeuesFeature

Änderungen committen: git commit -am 'Neues Feature hinzufügen'

Branch pushen: git push origin feature/NeuesFeature

Pull Request erstellen

📄 Lizenz
Dieses Projekt ist unter der MIT-Lizenz lizenziert.

🆘 Support
Bei Problemen oder Fragen:

Issues im Repository öffnen

Logs zur Problembeschreibung beifügen

Konfiguration und Umgebungsdetails angeben

Erwartetes vs. tatsächliches Verhalten beschreiben

🚀 Viel Spaß mit dem Universal Chat System!