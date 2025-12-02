# 🏗️ Workspace Documentation

## Überblick

Diese Dokumentation beschreibt die Entwicklungsumgebung und Best Practices für die Arbeit am Chat System.

## Development Environment Setup

### Voraussetzungen

- Python 3.10+
- Git
- Docker & Docker Compose
- VS Code (empfohlen) oder PyCharm

### Initial Setup

```bash
# Repository klonen
git clone https://github.com/Thomas-Heisig/chat_system.git
cd chat_system

# Virtual Environment erstellen
python -m venv venv
source venv/bin/activate  # Linux/Mac
# oder
venv\Scripts\activate     # Windows

# Dependencies installieren
pip install -r requirements.txt

# Development Tools installieren
pip install black isort flake8 mypy pytest pytest-asyncio pytest-cov

# Pre-commit Hooks installieren (optional aber empfohlen)
pip install pre-commit
pre-commit install

# .env Datei erstellen
cp .env.example .env
# .env anpassen mit deinem Editor

# Datenbank initialisieren
python -c "from database.connection import init_database; init_database()"
```

## Projekt-Struktur

```
chat_system/
├── .devcontainer/          # VS Code DevContainer-Konfiguration
├── .github/                # GitHub Actions CI/CD
│   └── workflows/
│       ├── ci.yml          # Main CI Pipeline
│       └── security.yml    # Security Scans
├── config/                 # Anwendungs-Konfiguration
├── database/               # Datenbankschicht
├── docs/                   # Technische Dokumentation
├── k8s/                    # Kubernetes-Manifests
├── routes/                 # API-Endpunkte
├── services/               # Business Logic
├── tests/                  # Unit & Integration Tests
├── workspace/              # Development Dokumentation
├── ARCHITECTURE.md         # System-Architektur
├── DEPLOYMENT.md           # Deployment-Guide
├── SECURITY.md             # Security Policy
└── README.md               # Projekt-Übersicht
```

## Development Workflow

### Testing

```bash
# Alle Tests
pytest

# Mit Coverage
pytest --cov=. --cov-report=html

# Spezifische Tests
pytest tests/unit/test_message_service.py
```

### Code Quality

```bash
# Formatieren
black . && isort .

# Linting
flake8 .

# Type Checking
mypy .
```

---

**Happy Coding! 🚀**
