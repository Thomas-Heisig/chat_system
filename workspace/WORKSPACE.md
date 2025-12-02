# 💼 Chat System - Workspace Guide

## Willkommen im Chat System Workspace

Dieser Guide hilft dir beim Einstieg in die Entwicklung am Chat System.

## Quick Start

### 1. Repository Setup

```bash
# Repository klonen
git clone https://github.com/Thomas-Heisig/chat_system.git
cd chat_system

# Branch erstellen
git checkout -b feature/my-feature

# Dependencies installieren
pip install -r requirements.txt
```

### 2. Entwicklungsumgebung

#### Option A: DevContainer (Empfohlen)

```bash
# In VS Code öffnen
code .

# F1 drücken und auswählen:
# "Dev Containers: Reopen in Container"
```

Vorteile:
- ✅ Alle Dependencies vorinstalliert
- ✅ Konsistente Entwicklungsumgebung
- ✅ Python Extensions pre-configured
- ✅ Database und Services ready

#### Option B: Lokale Entwicklung

```bash
# Virtuelle Umgebung
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Dependencies
pip install -r requirements.txt

# Pre-commit hooks
pre-commit install
```

### 3. Erste Schritte

```bash
# Datenbank initialisieren
python -c "from database.connection import init_database; init_database()"

# Server starten
uvicorn main:app --reload

# In Browser öffnen
open http://localhost:8000
```

## Projektstruktur

```
chat_system/
├── main.py                 # FastAPI Application Entry Point
├── routes/                 # API Endpoints
│   ├── chat.py            # Chat & WebSocket Routes
│   ├── dictionary.py      # Dictionary API
│   ├── wiki.py            # Wiki API
│   ├── plugins.py         # Plugin System API
│   └── virtual_rooms.py   # Virtual Rooms API
├── services/              # Business Logic Layer
│   ├── message_service.py # Message Handling
│   ├── elyza_service.py   # AI Fallback
│   ├── dictionary_service.py
│   ├── wiki_service.py
│   └── ...
├── core/                  # Core Functionality
│   └── auth.py           # Authentication & RBAC
├── database/             # Database Layer
│   ├── connection.py     # DB Connection
│   ├── models.py         # Data Models
│   └── repositories.py   # Data Access
├── config/               # Configuration
│   ├── settings.py       # App Settings
│   └── validation.py     # Config Validation
├── tests/                # Test Suite
│   ├── test_dictionary.py
│   ├── test_wiki.py
│   └── ...
├── docs/                 # Additional Documentation
├── k8s/                  # Kubernetes Manifests
│   └── manifests/
├── .github/              # GitHub Actions
│   └── workflows/
│       └── ci.yml
└── workspace/            # Development Docs
    └── WORKSPACE.md      # This file
```

## Entwicklungs-Workflow

### 1. Feature entwickeln

```bash
# Branch erstellen
git checkout -b feature/new-feature

# Code schreiben
# ... edit files ...

# Tests schreiben
# ... add tests ...

# Tests ausführen
pytest tests/test_new_feature.py

# Linting
black .
flake8 .
isort .
```

### 2. Commit Guidelines

Wir folgen [Conventional Commits](https://www.conventionalcommits.org/):

```bash
# Format
<type>(<scope>): <subject>

# Beispiele
feat(chat): add WebSocket reconnection logic
fix(auth): correct JWT token validation
docs(readme): update installation instructions
test(wiki): add unit tests for page creation
refactor(services): extract common logic to base class
```

**Types**:
- `feat`: Neue Feature
- `fix`: Bug Fix
- `docs`: Dokumentation
- `style`: Code-Formatierung
- `refactor`: Code-Refactoring
- `test`: Tests
- `chore`: Build/Tools

### 3. Pull Request erstellen

```bash
# Changes committen
git add .
git commit -m "feat(wiki): add page versioning"

# Push to remote
git push origin feature/new-feature

# PR erstellen via GitHub UI oder CLI
gh pr create --title "Add Wiki Page Versioning" --body "..."
```

**PR Template**:
```markdown
## Beschreibung
Was macht diese PR?

## Änderungen
- [ ] Neue Funktion X
- [ ] Bug Fix Y
- [ ] Tests hinzugefügt

## Testing
Wie wurde getestet?

## Screenshots
Wenn UI-Änderungen

## Checklist
- [ ] Tests laufen durch
- [ ] Dokumentation aktualisiert
- [ ] Changelog aktualisiert
```

## Testing

### Unit Tests

```bash
# Alle Tests
pytest

# Einzelner Test
pytest tests/test_wiki.py

# Mit Coverage
pytest --cov=services --cov-report=html

# Coverage Report
open htmlcov/index.html
```

### Integration Tests

```bash
# Docker-Compose für Integration Tests
docker-compose -f docker-compose.test.yml up -d

# Tests ausführen
pytest tests/integration/

# Cleanup
docker-compose -f docker-compose.test.yml down -v
```

### API Tests (Manual)

```bash
# Mit HTTPie
http POST localhost:8000/api/wiki/pages title="Test" content="Content" author="dev"

# Mit curl
curl -X POST http://localhost:8000/api/wiki/pages \
  -H "Content-Type: application/json" \
  -d '{"title":"Test","content":"Content","author":"dev"}'
```

## Code Quality

### Linting & Formatting

```bash
# Black (Code Formatter)
black .

# isort (Import Sorter)
isort .

# flake8 (Linter)
flake8 .

# mypy (Type Checker)
mypy services/

# Alle auf einmal
pre-commit run --all-files
```

### Pre-commit Hooks

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/psf/black
    rev: 23.3.0
    hooks:
      - id: black
  - repo: https://github.com/PyCQA/isort
    rev: 5.12.0
    hooks:
      - id: isort
  - repo: https://github.com/PyCQA/flake8
    rev: 6.0.0
    hooks:
      - id: flake8
```

## Debugging

### VS Code Launch Config

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "FastAPI",
      "type": "python",
      "request": "launch",
      "module": "uvicorn",
      "args": [
        "main:app",
        "--reload",
        "--host", "0.0.0.0",
        "--port", "8000"
      ],
      "jinja": true,
      "justMyCode": false
    },
    {
      "name": "Pytest",
      "type": "python",
      "request": "launch",
      "module": "pytest",
      "args": ["-v"],
      "console": "integratedTerminal"
    }
  ]
}
```

### Logging

```python
from config.settings import enhanced_logger

# Debug logging
enhanced_logger.debug("Debug message", extra_data=value)

# Info
enhanced_logger.info("Operation completed", duration_ms=123)

# Warning
enhanced_logger.warning("Deprecated API used", endpoint="/old/api")

# Error
enhanced_logger.error("Operation failed", error=str(e))
```

## Häufige Aufgaben

### Neue Route hinzufügen

```python
# 1. In routes/my_route.py
from fastapi import APIRouter

router = APIRouter(prefix="/api/myroute", tags=["myroute"])

@router.get("/")
async def get_items():
    return {"items": []}

# 2. In main.py registrieren
from routes.my_route import router as myroute_router
app.include_router(myroute_router)
```

### Neuen Service erstellen

```python
# services/my_service.py
from typing import Dict, Any
from config.settings import logger

class MyService:
    """
    Beschreibung des Service
    """
    
    def __init__(self):
        logger.info("MyService initialized")
    
    async def do_something(self, param: str) -> Dict[str, Any]:
        """
        Macht etwas tolles
        """
        return {"result": param}

# Singleton instance
_my_service = None

def get_my_service() -> MyService:
    global _my_service
    if _my_service is None:
        _my_service = MyService()
    return _my_service
```

### Database Model hinzufügen

```python
# In database/models.py
from sqlalchemy import Column, String, DateTime
from datetime import datetime

class MyModel(Base):
    __tablename__ = "my_table"
    
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.now)
```

### Migration erstellen (Alembic)

```bash
# Migration generieren
alembic revision --autogenerate -m "Add my_table"

# Migration anwenden
alembic upgrade head

# Rollback
alembic downgrade -1
```

## Umgebungsvariablen

### Entwicklung (.env)

```bash
# App
APP_ENVIRONMENT=development
LOG_LEVEL=DEBUG

# Database
DATABASE_URL=sqlite:///./chat_system.db

# Features
AI_ENABLED=true
ENABLE_ELYZA_FALLBACK=true
WEBSOCKET_ENABLED=true

# Ollama (lokal)
OLLAMA_BASE_URL=http://localhost:11434
```

### Testing (.env.test)

```bash
APP_ENVIRONMENT=testing
DATABASE_URL=sqlite:///./test.db
LOG_LEVEL=INFO
```

## Performance Profiling

### cProfile

```bash
# Mit cProfile starten
python -m cProfile -o profile.stats main.py

# Stats analysieren
python -c "import pstats; p = pstats.Stats('profile.stats'); p.sort_stats('cumulative').print_stats(20)"
```

### Memory Profiling

```bash
# memory_profiler installieren
pip install memory-profiler

# Decorator verwenden
@profile
def my_function():
    pass

# Ausführen
python -m memory_profiler my_script.py
```

## Dokumentation

### API Dokumentation

FastAPI generiert automatisch:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- OpenAPI JSON: http://localhost:8000/openapi.json

### Code Dokumentation

```python
def my_function(param: str) -> Dict[str, Any]:
    """
    Kurze Beschreibung (eine Zeile)
    
    Längere Beschreibung mit mehr Details.
    Kann mehrere Absätze haben.
    
    Args:
        param: Beschreibung des Parameters
    
    Returns:
        Dict mit result
        
    Raises:
        ValueError: Wenn param ungültig
        
    Example:
        >>> my_function("test")
        {'result': 'test'}
    """
    pass
```

## Troubleshooting

### Problem: Import Errors

```bash
# Prüfe Python Path
echo $PYTHONPATH

# Setze PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:/path/to/chat_system"
```

### Problem: Database Locked

```bash
# Finde Prozess
lsof chat_system.db

# Kill Prozess
kill -9 <PID>
```

### Problem: Port Already in Use

```bash
# Finde Prozess auf Port 8000
lsof -i :8000

# Kill Prozess
kill -9 <PID>

# Oder anderen Port verwenden
uvicorn main:app --port 8001
```

## Nützliche Tools

### VS Code Extensions
- Python
- Pylance
- Python Docstring Generator
- GitLens
- REST Client
- Docker
- Kubernetes

### CLI Tools
- **httpie**: `http localhost:8000/api/endpoint`
- **jq**: `curl ... | jq`
- **gh**: GitHub CLI
- **docker-compose**: Container Management

## Ressourcen

### Interne Docs
- [README.md](../README.md)
- [ARCHITECTURE.md](../ARCHITECTURE.md)
- [DEPLOYMENT.md](../DEPLOYMENT.md)
- [SECURITY.md](../SECURITY.md)

### Externe Links
- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [Pydantic Docs](https://docs.pydantic.dev/)
- [SQLAlchemy Docs](https://docs.sqlalchemy.org/)
- [pytest Docs](https://docs.pytest.org/)

### Community
- GitHub Issues: Bug Reports & Features
- Discussions: Fragen & Ideen
- Wiki: Erweiterte Guides

## Kontakt

- **Maintainer**: Thomas Heisig
- **Issues**: https://github.com/Thomas-Heisig/chat_system/issues
- **Discussions**: https://github.com/Thomas-Heisig/chat_system/discussions

---
Happy Coding! 🚀

*Letzte Aktualisierung: 2025-12-02*
