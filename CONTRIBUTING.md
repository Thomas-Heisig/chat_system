# 🤝 Contributing to Universal Chat System

Thank you for your interest in contributing to the Universal Chat System!

## 📚 Complete Contributing Guide

For comprehensive contribution guidelines, please see:

**[📖 Complete Contributing Guide](docs/07-contributing/README.md)**

This includes:
- Code of Conduct
- Getting Started for Contributors
- Development Workflow
- Coding Standards
- Testing Requirements
- Documentation Standards
- Pull Request Process
- Issue Guidelines

## Quick Links

- **[Getting Started](docs/07-contributing/getting-started.md)** - First-time contributors
- **[Development Workflow](docs/07-contributing/development-workflow.md)** - Git workflow
- **[Coding Standards](docs/07-contributing/coding-standards.md)** - Code style
- **[Testing Guide](docs/07-contributing/testing-requirements.md)** - Testing guidelines
- **[PR Process](docs/07-contributing/pull-request-process.md)** - Pull request guidelines

## Quick Start for Contributors

### 1. Fork and Clone

```bash
git clone https://github.com/YOUR-USERNAME/chat_system.git
cd chat_system
```

### 2. Set Up Development Environment

```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
pip install -r requirements-dev.txt
pre-commit install
```

### 3. Create Feature Branch

```bash
git checkout -b feature/your-feature-name
```

### 4. Make Changes

- Follow coding standards
- Write tests
- Update documentation
- Ensure all tests pass

### 5. Submit Pull Request

```bash
git add .
git commit -m "Add your feature"
git push origin feature/your-feature-name
```

Then open a Pull Request on GitHub.

## Ways to Contribute

### 🐛 Report Bugs
Found a bug? [Open an issue](https://github.com/Thomas-Heisig/chat_system/issues)

### 💡 Suggest Features
Have an idea? [Open a feature request](https://github.com/Thomas-Heisig/chat_system/issues)

### 📝 Improve Documentation
- Fix typos
- Add examples
- Translate documentation
- Update outdated content

### 🔧 Submit Code
- Fix bugs
- Implement features
- Improve performance
- Add tests

## Code of Conduct

### Our Pledge

We are committed to providing a welcoming and inspiring community:

- ✅ Be respectful and inclusive
- ✅ Provide constructive feedback
- ✅ Focus on what is best for the community
- ✅ Show empathy towards others

### Unacceptable Behavior

- ❌ Harassment or discrimination
- ❌ Trolling or insulting comments
- ❌ Personal or political attacks
- ❌ Publishing others' private information

## Getting Help

- **Documentation**: [Full Documentation](docs/README.md)
- **Discussions**: [GitHub Discussions](https://github.com/Thomas-Heisig/chat_system/discussions)
- **Issues**: [GitHub Issues](https://github.com/Thomas-Heisig/chat_system/issues)

---

**Thank you for contributing to the Universal Chat System! 🙏**

For detailed guidelines, see the [Complete Contributing Guide](docs/07-contributing/README.md).

## Code of Conduct

### Unsere Verpflichtung

Wir verpflichten uns, eine offene und einladende Umgebung zu schaffen:

- ✅ Respektvoller Umgang
- ✅ Konstruktives Feedback
- ✅ Fokus auf das Beste für die Community
- ✅ Empathie gegenüber anderen

### Unakzeptables Verhalten

- ❌ Belästigung oder Diskriminierung
- ❌ Trolling oder beleidigende Kommentare
- ❌ Persönliche oder politische Angriffe
- ❌ Veröffentlichung privater Informationen

## Getting Started

### Voraussetzungen

```bash
Python 3.9+
pip
git
Docker (optional, empfohlen)
```

### Repository forken

1. Forken Sie das Repository auf GitHub
2. Klonen Sie Ihren Fork:
```bash
git clone https://github.com/IHR-USERNAME/chat_system.git
cd chat_system
```

### Entwicklungsumgebung einrichten

```bash
# Virtuelle Umgebung erstellen
python -m venv venv
source venv/bin/activate  # Linux/MacOS
# oder
venv\Scripts\activate  # Windows

# Dependencies installieren
pip install -r requirements.txt

# Pre-commit hooks installieren
pre-commit install

# .env Datei erstellen
cp .env.example .env
# Bearbeiten Sie .env mit Ihrem Editor
```

### Mit Docker

```bash
# Services starten
docker-compose up -d

# Logs ansehen
docker-compose logs -f app
```

## Development Workflow

### Branch-Strategie

- `main`: Stable production code
- `develop`: Development branch
- `feature/*`: New features
- `bugfix/*`: Bug fixes
- `hotfix/*`: Urgent production fixes

### Feature entwickeln

```bash
# Von develop abzweigen
git checkout develop
git pull origin develop

# Feature-Branch erstellen
git checkout -b feature/neue-feature

# Änderungen machen
# ... code, test, commit ...

# Branch pushen
git push origin feature/neue-feature

# Pull Request erstellen auf GitHub
```

### Commit-Nachrichten

Folgen Sie dem Conventional Commits Standard:

```
type(scope): subject

body (optional)

footer (optional)
```

**Types:**
- `feat`: Neues Feature
- `fix`: Bug Fix
- `docs`: Dokumentation
- `style`: Formatierung
- `refactor`: Code-Refactoring
- `test`: Tests hinzufügen/ändern
- `chore`: Build/Dependencies

**Beispiele:**
```bash
feat(agents): Add dialog agent with context management
fix(voice): Fix transcription service initialization
docs(readme): Update installation instructions
```

## Pull Request Process

### Vor dem PR

- [ ] Code funktioniert lokal
- [ ] Tests geschrieben und bestanden
- [ ] Dokumentation aktualisiert
- [ ] Code formatiert (Black, isort)
- [ ] Linting ohne Fehler (flake8)
- [ ] Type hints hinzugefügt
- [ ] CHANGELOG.md aktualisiert

### PR erstellen

1. **Title**: Kurz und beschreibend
   ```
   feat(agents): Implement multi-agent orchestration system
   ```

2. **Description**: Verwenden Sie die PR-Vorlage
   ```markdown
   ## Änderungen
   - Neue Feature X hinzugefügt
   - Bug Y behoben
   
   ## Motivation
   Warum ist diese Änderung notwendig?
   
   ## Testing
   Wie wurde getestet?
   
   ## Screenshots
   (Falls UI-Änderungen)
   
   ## Checklist
   - [x] Tests hinzugefügt
   - [x] Dokumentation aktualisiert
   - [x] Breaking changes dokumentiert
   ```

3. **Reviews**: Mind. 1 Approval erforderlich

4. **CI/CD**: Alle Checks müssen grün sein

### Nach dem Merge

```bash
# Branch lokal löschen
git checkout develop
git branch -d feature/neue-feature

# Remote branch löschen
git push origin --delete feature/neue-feature
```

## Coding Standards

### Python Style Guide

Wir folgen PEP 8 mit einigen Anpassungen:

```python
# ✅ RICHTIG
from typing import Dict, List, Optional


class MyService:
    """
    Service für X.
    
    Attributes:
        config: Service-Konfiguration
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
    
    async def process(self, data: List[str]) -> Optional[Dict]:
        """
        Verarbeitet Daten.
        
        Args:
            data: Liste von Eingabedaten
            
        Returns:
            Verarbeitetes Ergebnis oder None
        """
        result = await self._internal_process(data)
        return result


# ❌ FALSCH (keine Type hints, keine Docstrings)
class MyService:
    def __init__(self, config):
        self.config = config
    
    def process(self, data):
        return self._internal_process(data)
```

### Code-Formatierung

```bash
# Black für Code-Formatierung
black .

# isort für Import-Sortierung
isort .

# flake8 für Linting
flake8 .

# mypy für Type Checking
mypy .
```

### Naming Conventions

```python
# Variablen und Funktionen: snake_case
user_name = "John"
def get_user_data(): pass

# Klassen: PascalCase
class UserService: pass

# Konstanten: UPPER_SNAKE_CASE
MAX_RETRY_COUNT = 3
API_BASE_URL = "https://api.example.com"

# Private: führendes Unterstrich
def _internal_helper(): pass
_private_var = 42
```

## Testing

### Unit Tests

```python
import pytest


class TestUserService:
    """Tests für UserService"""
    
    def test_create_user(self):
        """Test user creation"""
        service = UserService()
        user = service.create_user("john", "john@example.com")
        
        assert user is not None
        assert user.username == "john"
        assert user.email == "john@example.com"
    
    def test_create_user_duplicate(self):
        """Test duplicate user creation fails"""
        service = UserService()
        service.create_user("john", "john@example.com")
        
        with pytest.raises(ValueError):
            service.create_user("john", "john@example.com")
```

### Integration Tests

```python
import pytest
from fastapi.testclient import TestClient
from main import app


client = TestClient(app)


def test_api_health():
    """Test health endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
```

### Tests ausführen

```bash
# Alle Tests
pytest

# Mit Coverage
pytest --cov=. --cov-report=html

# Spezifische Tests
pytest tests/test_agents.py -v

# Tests mit Markers
pytest -m "slow"  # nur langsame Tests
pytest -m "not slow"  # ohne langsame Tests
```

### Test Coverage

Minimum 80% Code Coverage für neue Features.

```bash
# Coverage Report anzeigen
coverage report
coverage html
# Öffne htmlcov/index.html
```

## Documentation

### Docstrings

Verwenden Sie Google-Style Docstrings:

```python
def complex_function(
    param1: str,
    param2: int,
    optional_param: Optional[bool] = None
) -> Dict[str, Any]:
    """
    Kurze Beschreibung der Funktion.
    
    Längere Beschreibung mit mehr Details über
    die Funktion und ihr Verhalten.
    
    Args:
        param1: Beschreibung von Parameter 1
        param2: Beschreibung von Parameter 2
        optional_param: Optionaler Parameter. Defaults to None.
    
    Returns:
        Dictionary mit Ergebnissen:
        - key1: Beschreibung
        - key2: Beschreibung
    
    Raises:
        ValueError: Wenn param2 negativ ist
        RuntimeError: Bei internen Fehlern
    
    Example:
        >>> result = complex_function("test", 42)
        >>> print(result['key1'])
        'some_value'
    """
    if param2 < 0:
        raise ValueError("param2 must be non-negative")
    
    return {"key1": "value1", "key2": param2}
```

### README und Guides

- README.md: Hauptdokumentation
- ARCHITECTURE.md: Architektur-Übersicht
- API-Docs: Automatisch via FastAPI
- Guides: Im `docs/` Verzeichnis

## Review-Prozess

### Als Author

- Reagieren Sie zeitnah auf Feedback
- Seien Sie offen für Vorschläge
- Erklären Sie Ihre Entscheidungen
- Markieren Sie resolved Kommentare

### Als Reviewer

- Seien Sie konstruktiv und höflich
- Fragen Sie bei Unklarheiten nach
- Approven Sie nur vollständige PRs
- Verwenden Sie Review-Kommentare:
  - 💬 Comment: Frage/Diskussion
  - ⚠️ Request Changes: Muss geändert werden
  - ✅ Approve: Sieht gut aus

## Community

### Kommunikation

- **GitHub Discussions**: Allgemeine Diskussionen
- **GitHub Issues**: Bug Reports, Feature Requests
- **Pull Requests**: Code Reviews
- **Discord** (optional): Real-time Chat

### Hilfe bekommen

1. Prüfen Sie die Dokumentation
2. Suchen Sie in Issues/Discussions
3. Erstellen Sie ein Issue mit Details
4. Seien Sie geduldig und respektvoll

## Lizenz

Durch Ihren Beitrag stimmen Sie zu, dass Ihr Code unter der MIT-Lizenz veröffentlicht wird.

## Anerkennungen

Alle Contributors werden in der README.md und im CHANGELOG.md erwähnt.

Vielen Dank für Ihren Beitrag! 🎉
