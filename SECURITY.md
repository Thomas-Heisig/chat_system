# 🔒 Security Policy

## Sicherheitsgrundsätze

Das Chat System implementiert mehrschichtige Sicherheitsmaßnahmen zum Schutz von Daten und Systemen.

## Unterstützte Versionen

Wir bieten Sicherheitsupdates für folgende Versionen:

| Version | Unterstützt          |
| ------- | -------------------- |
| 2.0.x   | ✅ Ja                |
| 1.x.x   | ⚠️ Nur kritische Fixes |
| < 1.0   | ❌ Nein              |

## Sicherheitsfunktionen

### 1. Authentifizierung

#### ⚠️ Default Admin Credentials (KRITISCH)

**Beim ersten Start wird ein Default-Admin-User erstellt:**
- **Username**: `admin`
- **Password**: `admin123`
- **Status**: `force_password_change=True`

**WICHTIG - Sicherheitsmaßnahmen:**

1. **Automatische Passwort-Änderung erzwungen**:
   - Der Admin-User hat `force_password_change=True` gesetzt
   - System erfordert Passwort-Änderung beim ersten Login
   - Zugriff wird blockiert bis Passwort geändert wurde

2. **Best Practices für Admin-Setup**:
   ```bash
   # Nach dem ersten Start SOFORT das Passwort ändern!
   # Verwenden Sie ein sicheres Passwort:
   # - Mindestens 12 Zeichen
   # - Mix aus Groß-/Kleinbuchstaben, Zahlen, Sonderzeichen
   # - Keine Wörter aus Wörterbüchern
   # - Verwenden Sie einen Password Manager
   
   # Beispiel für starkes Passwort generieren:
   python -c "import secrets; import string; chars = string.ascii_letters + string.digits + string.punctuation; print(''.join(secrets.choice(chars) for _ in range(20)))"
   ```

3. **Produktions-Deployment**:
   - ❌ **NIEMALS** das Default-Passwort in Produktion verwenden
   - ✅ Passwort sofort nach Deployment ändern
   - ✅ Admin-Account umbenennen (von "admin" zu etwas Eindeutigem)
   - ✅ 2FA aktivieren (wenn implementiert)
   - ✅ Monitoring für fehlgeschlagene Login-Versuche aktivieren

4. **Automatisierte Überprüfung**:
   ```python
   # Das System loggt Warnungen beim Start:
   # ⚠️ Default admin user created - PASSWORD CHANGE REQUIRED ON FIRST LOGIN
   # 🔐 Default credentials: admin / admin123 (You will be prompted to change this)
   ```

#### JWT (JSON Web Tokens)
- **Implementierung**: python-jose mit RS256-Algorithmus
- **Token-Lebensdauer**: 
  - Access Token: 15 Minuten
  - Refresh Token: 7 Tage
- **Speicherung**: Tokens niemals im localStorage, nur in httpOnly Cookies

```python
# Beispiel Token-Konfiguration
JWT_SECRET_KEY = os.getenv("APP_SECRET_KEY")  # Mind. 32 Zeichen
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_MINUTES = 15
```

#### Passwort-Hashing
- **Algorithmus**: bcrypt mit automatischem Salting
- **Work Factor**: 12 Runden (Standard)
- **Anforderungen**: 
  - Mindestlänge: 8 Zeichen
  - Mindestens 1 Großbuchstabe, 1 Kleinbuchstabe, 1 Zahl

```python
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
hashed_password = pwd_context.hash(plain_password)
```

### 2. Autorisierung

#### Role-Based Access Control (RBAC)

```python
# Benutzer-Rollen
ROLES = {
    "admin": ["read", "write", "delete", "manage_users"],
    "moderator": ["read", "write", "moderate"],
    "user": ["read", "write_own"],
    "guest": ["read"]
}
```

#### Resource-basierte Permissions
- Benutzer können nur eigene Ressourcen bearbeiten
- Admins haben volle Kontrolle
- Audit-Log für alle privilegierten Aktionen

### 3. API-Sicherheit

#### Rate Limiting
- **Default**: 100 Requests pro Minute pro IP
- **Authentication-Endpoints**: 5 Requests pro Minute
- **Implementierung**: SlowAPI

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.post("/api/auth/login")
@limiter.limit("5/minute")
async def login(...):
    ...
```

#### CORS (Cross-Origin Resource Sharing)
- Whitelist-basiert, keine Wildcards in Production
- Credentials erlaubt nur für vertrauenswürdige Origins
- Pre-flight Request-Caching

```python
CORS_ORIGINS = [
    "https://chat.example.com",
    "https://app.example.com"
]  # Niemals "*" in Production!
```

#### Input-Validierung
- **Pydantic Models** für alle Requests
- Typ-Checking und Constraint-Validation
- SQL-Injection-Schutz durch Parametrisierung
- XSS-Schutz durch HTML-Escaping

```python
from pydantic import BaseModel, constr, validator

class MessageCreate(BaseModel):
    content: constr(min_length=1, max_length=5000)
    
    @validator('content')
    def sanitize_content(cls, v):
        return html.escape(v)
```

### 4. Datenbank-Sicherheit

#### Verbindungssicherheit
- SSL/TLS für Produktions-Datenbanken
- Connection String Encryption
- Getrennte Read/Write-Credentials

```python
# Sichere PostgreSQL-Verbindung
DATABASE_URL = "postgresql://user:pass@host:5432/db?sslmode=require"
```

#### Daten-Verschlüsselung
- **At Rest**: Verschlüsselte Datenbank-Volumes
- **In Transit**: TLS 1.3 für alle Verbindungen
- **Sensitive Fields**: Zusätzliche Verschlüsselung mit Fernet

```python
from cryptography.fernet import Fernet

cipher = Fernet(ENCRYPTION_KEY)
encrypted_data = cipher.encrypt(sensitive_data.encode())
```

#### SQL-Injection Prevention
- ORM (SQLAlchemy) mit Parametrisierung
- Keine String-Konkatenation für Queries
- Input-Sanitization

### 5. Secrets Management

#### Best Practices
✅ **Richtig:**
- Secrets in Umgebungsvariablen
- Kubernetes Secrets für K8s-Deployments
- AWS Secrets Manager / Azure Key Vault für Cloud
- Verschlüsselte `.env`-Dateien für Entwicklung

❌ **Falsch:**
- Hardcoded Secrets im Code
- Secrets im Git-Repository
- Secrets in Logs
- Secrets in Error Messages

#### Secrets Rotation
```bash
# Regelmäßige Rotation (empfohlen: alle 90 Tage)
APP_SECRET_KEY          # JWT-Signierung
DATABASE_PASSWORD       # DB-Zugriff
API_KEYS                # Externe Services
ENCRYPTION_KEY          # Daten-Verschlüsselung
```

### 6. Netzwerk-Sicherheit

#### Firewall-Regeln
```bash
# Nur notwendige Ports öffnen
- 443 (HTTPS)     # Public
- 8000 (App)      # Internal Only
- 5432 (Postgres) # Database Network Only
- 6379 (Redis)    # Internal Only
```

#### Reverse Proxy
- Nginx oder Traefik vor Application
- SSL/TLS Termination
- Request-Filtering
- DDoS-Protection

```nginx
# Nginx-Konfiguration
server {
    listen 443 ssl http2;
    server_name chat.example.com;
    
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    ssl_protocols TLSv1.3;
    
    # Security Headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Strict-Transport-Security "max-age=31536000" always;
    
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

### 7. Logging & Monitoring

#### Security Logging
Alle sicherheitsrelevanten Events werden geloggt:
- Login-Versuche (erfolgreich und fehlgeschlagen)
- Privilegierte Aktionen
- Rate Limit Violations
- Autorisierungs-Fehler
- Änderungen an Benutzerrechten

```python
enhanced_logger.security(
    "Failed login attempt",
    username=username,
    ip_address=request.client.host,
    user_agent=request.headers.get("User-Agent")
)
```

#### Sensitive Data Redaction
```python
# Logs niemals Passwörter, Tokens oder API-Keys enthalten
logger.info(f"User {user.username} logged in")  # ✅ OK
logger.info(f"Password: {password}")            # ❌ NIEMALS!
```

### 8. Dependency Security

#### Dependency Scanning
```bash
# Regelmäßige Scans auf bekannte Vulnerabilities
pip install safety
safety check --json

# Oder mit GitHub Dependabot
# .github/dependabot.yml konfiguriert
```

#### Update-Strategie
- **Kritische Security-Patches**: Sofort
- **Major Updates**: Nach Testing
- **Pinned Versions** in requirements.txt
- Regelmäßige Dependency-Reviews

```bash
# requirements.txt mit Pinned Versions
fastapi==0.104.1        # Nicht: fastapi>=0.100
pydantic==2.5.0         # Nicht: pydantic>2.0
```

### 9. WebSocket-Sicherheit

#### Authentifizierung
- Token-basierte WS-Authentifizierung
- Origin-Validierung
- Connection Rate Limiting

```python
@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str, token: str):
    # Token validieren
    if not validate_token(token):
        await websocket.close(code=1008)
        return
    # ...
```

#### Message-Validierung
- Alle eingehenden Messages validieren
- Max. Message-Größe enforcing
- Sanitization von User-Content

### 10. Error Handling

#### Sichere Error-Responses
✅ **Production:**
```json
{
    "error": "Authentication failed",
    "code": "AUTH_FAILED"
}
```

❌ **Development (niemals in Production!):**
```json
{
    "error": "Invalid password for user admin@example.com",
    "traceback": "...",
    "database_query": "SELECT * FROM users WHERE email='admin@example.com'"
}
```

#### Custom Exception Handler
```python
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    
    if settings.APP_ENVIRONMENT == "production":
        return JSONResponse(
            status_code=500,
            content={"error": "Internal server error", "code": "INTERNAL_ERROR"}
        )
    else:
        # In Development mehr Details
        return JSONResponse(
            status_code=500,
            content={"error": str(exc), "type": type(exc).__name__}
        )
```

## Schwachstellen melden

### Responsible Disclosure

Wenn Sie eine Sicherheitslücke finden:

1. **NICHT** öffentlich ein Issue erstellen
2. **NICHT** die Schwachstelle ausnutzen
3. Kontaktieren Sie uns vertraulich:
   - Email: security@example.com (TODO: Echte Adresse eintragen)
   - PGP-Key: [Link zum Public Key]

### Was in Ihrem Report enthalten sein sollte:

- Beschreibung der Schwachstelle
- Schritte zur Reproduktion
- Potentielle Auswirkungen
- Proof-of-Concept (falls verfügbar)
- Vorschläge zur Behebung (optional)

### Response-Zeiten:

- **Kritisch**: < 24 Stunden
- **Hoch**: < 7 Tage
- **Mittel**: < 30 Tage
- **Niedrig**: Nächste Release

### Anerkennung:

Wir führen eine Security Hall of Fame für verantwortungsvolle Disclosure. Mit Ihrer Erlaubnis werden Sie dort genannt.

## Security Checklists

### Development

- [ ] Niemals Secrets im Code
- [ ] Input-Validierung für alle User-Inputs
- [ ] Output-Encoding gegen XSS
- [ ] Parametrisierte Queries gegen SQL-Injection
- [ ] HTTPS nur (außer lokale Entwicklung)
- [ ] Security Headers gesetzt
- [ ] Dependencies aktuell halten
- [ ] Code-Reviews für Security-relevanten Code

### Deployment

- [ ] Sichere Secrets-Verwaltung
- [ ] TLS 1.3 konfiguriert
- [ ] Firewall-Regeln aktiv
- [ ] Rate Limiting aktiviert
- [ ] Monitoring & Alerting eingerichtet
- [ ] Backup-Strategie implementiert
- [ ] Incident Response Plan vorhanden
- [ ] Security-Logs zentralisiert

### Operations

- [ ] Regelmäßige Security-Updates
- [ ] Log-Reviews durchführen
- [ ] Access-Reviews (wer hat Zugriff worauf?)
- [ ] Penetration Testing (jährlich)
- [ ] Disaster Recovery Tests
- [ ] Security-Training für Team

## Security-Features Roadmap

### Implementiert ✅

- JWT-Authentifizierung
- bcrypt Passwort-Hashing
- Rate Limiting
- CORS-Konfiguration
- Input-Validierung mit Pydantic
- Strukturiertes Security-Logging
- RBAC-System
- ExternalAIUnavailableError für AI-Ausfälle

### In Progress 🚧

- 2FA (Two-Factor Authentication)
- OAuth2-Integration (Google, GitHub)
- API-Key-Management
- IP-Whitelisting
- Advanced Audit Logging

### Geplant 📋

- End-to-End Verschlüsselung für Messages
- Hardware Security Module (HSM) Integration
- Certificate Pinning
- WAF (Web Application Firewall)
- DDoS-Protection
- Anomaly Detection

## Compliance

### DSGVO / GDPR

- ✅ Recht auf Vergessenwerden (User-Löschung)
- ✅ Datenportabilität (Export-Funktion)
- ✅ Daten-Verschlüsselung
- ✅ Zugriffskontrolle
- ✅ Audit-Logging
- ⚠️ Privacy Policy (TODO)
- ⚠️ Cookie Consent (TODO)

### ISO 27001

Wir orientieren uns an ISO 27001 Standards:
- Risiko-Assessment
- Access Control
- Encryption
- Incident Management
- Business Continuity

## Externe Security-Tools

### Empfohlene Tools

```bash
# Static Analysis
bandit -r .                    # Python Security Scanner
semgrep --config=auto .        # Multi-Language SAST

# Dependency Scanning
safety check                   # Known Vulnerabilities
pip-audit                      # PyPI Security Advisories

# Dynamic Analysis
OWASP ZAP                      # Web App Security Scanner
nikto -h localhost:8000        # Web Server Scanner

# Secret Scanning
truffleHog --regex             # Git History
detect-secrets scan            # Prevent Secret Commits
```

### CI/CD Integration

GitHub Actions Workflow für Security Checks:
```yaml
# .github/workflows/security.yml
name: Security Checks

on: [push, pull_request]

jobs:
  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Run Bandit
        run: |
          pip install bandit
          bandit -r . -f json -o bandit-report.json
      
      - name: Dependency Check
        run: |
          pip install safety
          safety check --json
      
      - name: CodeQL Analysis
        uses: github/codeql-action/analyze@v2
```

## Kontakt

Für Security-Fragen:
- **Email**: security@example.com (TODO: Echte Adresse)
- **PGP**: [Public Key Link]
- **Bug Bounty**: [Link zum Programm, falls vorhanden]

## Changelog

### 2024-12-02
- Initial Security Policy erstellt
- RBAC-System dokumentiert
- ExternalAIUnavailableError für AI-Fehlerbehandlung

### Frühere Versionen
- Siehe Git History

---

**Zuletzt aktualisiert**: 2024-12-02  
**Nächste Review**: 2025-03-02
