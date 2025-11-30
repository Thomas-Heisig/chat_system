🚀 Chat System (FastAPI + WebSocket)
Ein hochmodernes, serverseitig gerendertes Echtzeit-Chat-System auf Basis von FastAPI und WebSockets mit Enterprise-Features.

✨ Features
🔥 Kernfunktionen
Echtzeit-Chat mit WebSocket-Verbindungen

Persistente Speicherung in SQLite-Datenbank

RESTful API für erweiterte Funktionalitäten

Mehrsprachige Oberfläche (Deutsch, Englisch, Französisch, Spanisch)

Dynamische Themes (Light, Dark, High Contrast)

Responsive Design für alle Geräte

🛡️ Enterprise Features
Umfassendes Logging mit verschiedenen Levels

Rate Limiting für API-Endpoints

CORS-Konfiguration für Cross-Origin Requests

Automatische Reconnect-Logik für WebSockets

Health Monitoring mit System-Metriken

Performance Monitoring mit Request-Timing

📊 Monitoring & Analytics
Live-Statistiken über Nachrichten und Benutzer

Connection-Tracking für WebSocket-Verbindungen

System-Health-Checks mit detaillierten Metriken

Automatische Bereinigung inaktiver Verbindungen

🏗️ Projektstruktur
text
chat_system/
├── 🐍 main.py                          # Hauptanwendung mit Lifespan-Management
├── 📋 requirements.txt                 # Python-Abhängigkeiten
├── 🔧 .env.example                     # Umgebungsvariablen (Template)
├── 📊 docs/
│   └── 📖 API.md                       # API-Dokumentation
├── ⚙️ config/
│   ├── __init__.py
│   ├── ⚙️ settings.py                 # Zentrale Konfiguration
│   └── 🔒 validation.py               # Einstellungsvalidierung
├── 🗄️ database/
│   ├── __init__.py
│   ├── 🔗 connection.py               # Datenbankverbindung mit Logging
│   ├── 📐 models.py                   # Pydantic-Modelle mit Validierung
│   └── 📂 repositories.py             # Datenbank-Operationen
├── 🔌 websocket/
│   ├── __init__.py
│   ├── 👥 manager.py                  # Connection-Management
│   └── 🎯 handlers.py                 # WebSocket-Nachrichtenverarbeitung
├── 🛣️ routes/
│   ├── __init__.py
│   ├── 💬 chat.py                     # Chat-UI Routes
│   └── 📨 messages.py                 # API Message Routes
├── 🎨 static/
│   ├── 🎨 css/
│   │   └── 🎨 style.css               # Responsive CSS mit Themes
│   └── ⚡ js/
│       └── 💬 chat.js                 # Client-seitige Chat-Logik
├── 📄 templates/
│   └── 🏠 index.html                  # Haupt-Template
└── 🛠️ services/
    ├── __init__.py
    └── 📨 message_service.py          # Business-Logik für Nachrichten
🚀 Installation & Setup
Voraussetzungen
Python 3.8+

pip (Python Package Manager)

1. Repository klonen und Setup
bash
# Projektverzeichnis erstellen
mkdir chat_system && cd chat_system

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
3. Datenbank initialisieren
bash
# Die Datenbank wird automatisch beim ersten Start erstellt
python main.py
⚙️ Konfiguration
Umgebungsvariablen (.env)
env
# APP KONFIGURATION
APP_NAME=Chat System
APP_ENVIRONMENT=development
APP_DEBUG=true
APP_SECRET_KEY=your-super-secret-key

# SERVER KONFIGURATION
HOST=0.0.0.0
PORT=8000
RELOAD=true

# DATENBANK
DATABASE_URL=chat.db

# SICHERHEIT
CORS_ORIGINS=["http://localhost:3000", "http://127.0.0.1:3000"]
RATE_LIMIT_ENABLED=true

# LOGGING
LOG_LEVEL=INFO
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
🌐 Zugriff
Nach dem Start sind folgende Endpoints verfügbar:

Endpoint	Beschreibung	Typ
http://localhost:8000/	Chat-Benutzeroberfläche	Web UI
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
Nachrichten API
http
GET /api/messages
GET /api/messages/recent
GET /api/messages/user/{username}
GET /api/messages/stats
GET /api/messages/count
WebSocket Events
javascript
// Verbindung herstellen
const ws = new WebSocket('ws://localhost:8000/ws');

// Nachricht senden
ws.send(JSON.stringify({
    type: 'chat_message',
    username: 'benutzer',
    message: 'Hallo Welt!'
}));
🎨 Themes & Sprachen
Verfügbare Themes
Light - Helles Standard-Theme

Dark - Dunkles Theme für angenehmes Arbeiten

High Contrast - Hoher Kontrast für Barrierefreiheit

Unterstützte Sprachen
🇩🇪 Deutsch (Standard)

🇺🇸 Englisch

🇫🇷 Französisch

🇪🇸 Spanisch

🔧 Entwicklung
Projektstruktur erweitern
bash
# Neue Route hinzufügen
touch routes/ neue_route.py

# Neues Service erstellen
touch services/ neues_service.py

# Statische Dateien hinzufügen
touch static/js/ neues_script.js
touch static/css/ neues_styles.css
Tests ausführen
bash
# (Kommt in zukünftigen Versionen)
python -m pytest tests/
Logs einsehen
bash
# Log-Datei anzeigen
tail -f logs/chat_system.log

# Oder im Browser
curl http://localhost:8000/status | jq
🐛 Problembehandlung
Häufige Probleme
WebSocket-Verbindung fehlgeschlagen

Prüfen Sie die Firewall-Einstellungen

Stellen Sie sicher, dass Port 8000 freigegeben ist

Datenbank-Fehler

Berechtigungen für Datenbank-Datei prüfen

SQLite-Treiber aktualisieren

Rate Limiting Fehler

Rate Limit in .env anpassen

RATE_LIMIT_ENABLED=false für Entwicklung

Debug-Modus
env
APP_DEBUG=true
LOG_LEVEL=DEBUG
📈 Monitoring & Metriken
System-Health
bash
curl http://localhost:8000/status
Antwort beinhaltet:

Speichernutzung

CPU-Auslastung

Aktive WebSocket-Verbindungen

Datenbank-Statistiken

Log-Analyse
bash
# Fehler anzeigen
grep "ERROR" logs/chat_system.log

# WebSocket-Aktivität
grep "WebSocket" logs/chat_system.log

# Performance-Metriken
grep "Time:" logs/chat_system.log
🤝 Beitragen
Repository forken

Feature-Branch erstellen (git checkout -b feature/NeuesFeature)

Änderungen committen (git commit -am 'Neues Feature hinzufügen')

Branch pushen (git push origin feature/NeuesFeature)

Pull Request erstellen

📄 Lizenz
Dieses Projekt ist unter der MIT-Lizenz lizenziert.

🆘 Support
Bei Problemen oder Fragen:

Issues im Repository öffnen

Logs zur Problembeschreibung beifügen

Konfiguration und Umgebungsdetails angeben

🚀 Viel Spaß mit dem Chat System!