# 🔒 Chat System - Security Documentation

## Übersicht

Dieses Dokument beschreibt die Sicherheitsarchitektur, Best Practices und Richtlinien für das Chat System.

## Sicherheits-Prinzipien

### 1. Defense in Depth
Mehrschichtige Sicherheitsmaßnahmen auf allen Ebenen:
- Application Layer Security
- Network Layer Security
- Data Layer Security
- Infrastructure Security

### 2. Principle of Least Privilege
Minimale Berechtigungen für:
- Benutzer-Accounts
- Service-Accounts
- API-Keys
- Database-Zugriffe

### 3. Zero Trust
- Keine implizite Vertrauensstellung
- Jeder Request wird authentifiziert und autorisiert
- Continuous Verification

## Authentication & Authorization

### JWT-basierte Authentifizierung

```python
# Token-Generierung
from datetime import datetime, timedelta
from jose import jwt

def create_access_token(user_id: str, role: str):
    payload = {
        "sub": user_id,
        "role": role,
        "exp": datetime.utcnow() + timedelta(minutes=60)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")
```

### Password Hashing

**WICHTIG**: Niemals Plain-Text Passwörter speichern!

```python
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Hash password
hashed = pwd_context.hash("user_password")

# Verify password
is_valid = pwd_context.verify("user_password", hashed)
```

### Role-Based Access Control (RBAC)

#### Rollen-Hierarchie
```
Admin (alle Rechte)
  └── Moderator (erweiterte Rechte)
      └── User (Standard-Rechte)
          └── Guest (eingeschränkte Rechte)
```

#### Permissions
```python
PERMISSIONS = {
    "admin": ["*"],  # Alle Rechte
    "moderator": [
        "read", "write", "delete",
        "moderate_chat", "manage_users"
    ],
    "user": ["read", "write", "upload"],
    "guest": ["read"]
}
```

#### Implementation (TODO)
Siehe `core/auth.py` für vollständige RBAC-Implementierung.

## API Security

### Rate Limiting

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.post("/api/endpoint")
@limiter.limit("100/minute")
async def protected_endpoint():
    pass
```

**Konfiguration**:
```bash
RATE_LIMIT_ENABLED=true
RATE_LIMIT_PER_MINUTE=100
RATE_LIMIT_BURST=20
```

### CORS Configuration

```python
CORS_ORIGINS = [
    "https://yourdomain.com",
    "https://app.yourdomain.com"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)
```

**WARNUNG**: Verwende NIEMALS `allow_origins=["*"]` in Production!

### Input Validation

Alle Inputs werden mit Pydantic validiert:

```python
from pydantic import BaseModel, validator, constr

class MessageCreate(BaseModel):
    content: constr(min_length=1, max_length=5000)
    room_id: str
    
    @validator('content')
    def sanitize_content(cls, v):
        # XSS-Prävention
        return sanitize_html(v)
```

### SQL Injection Prevention

✅ **Richtig**: ORM-basierte Queries
```python
# SQLAlchemy ORM (sicher)
message = session.query(Message).filter_by(id=message_id).first()
```

❌ **Falsch**: Raw SQL mit String-Interpolation
```python
# NIEMALS SO!
query = f"SELECT * FROM messages WHERE id = {message_id}"
```

### XSS Prevention

```python
import bleach

ALLOWED_TAGS = ['b', 'i', 'u', 'em', 'strong', 'a', 'code', 'pre']
ALLOWED_ATTRIBUTES = {'a': ['href', 'title']}

def sanitize_html(content: str) -> str:
    return bleach.clean(
        content,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        strip=True
    )
```

### CSRF Protection

- Alle State-Changing Operations benötigen gültigen JWT Token
- Token ist an Session gebunden
- Token-Validierung bei jedem Request

## Data Security

### Encryption at Rest

#### Datenbank
- PostgreSQL: Transparent Data Encryption (TDE)
- Backup-Verschlüsselung mit AES-256

```bash
# PostgreSQL TDE aktivieren
ALTER DATABASE chatdb SET default_tablespace = encrypted_tablespace;
```

#### File Storage
- S3 Server-Side Encryption (SSE-S3 oder SSE-KMS)

```python
s3_client.upload_file(
    'file.txt',
    'bucket-name',
    'key',
    ExtraArgs={'ServerSideEncryption': 'AES256'}
)
```

### Encryption in Transit

- Alle Verbindungen über TLS/SSL
- Minimum TLS 1.2
- Starke Cipher Suites

```nginx
# Nginx SSL Configuration
ssl_protocols TLSv1.2 TLSv1.3;
ssl_ciphers 'ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256';
ssl_prefer_server_ciphers on;
```

### Sensitive Data Handling

#### Environment Variables
```bash
# .env (NIEMALS committen!)
SECRET_KEY=use-strong-random-key-here
JWT_SECRET_KEY=another-strong-key
DATABASE_PASSWORD=secure-db-password
```

#### Secrets Management
- **Development**: `.env`-Dateien (nicht in Git)
- **Production**: Kubernetes Secrets / AWS Secrets Manager / HashiCorp Vault

```yaml
# Kubernetes Secret
apiVersion: v1
kind: Secret
metadata:
  name: chat-secrets
type: Opaque
data:
  secret-key: <base64-encoded>
  db-password: <base64-encoded>
```

## Network Security

### Firewall Rules

#### Kubernetes Network Policies
```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: chat-system-policy
spec:
  podSelector:
    matchLabels:
      app: chat-system
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          app: nginx-ingress
    ports:
    - protocol: TCP
      port: 8000
  egress:
  - to:
    - podSelector:
        matchLabels:
          app: postgres
    ports:
    - protocol: TCP
      port: 5432
```

### Service Isolation

- App Server: Public (via Ingress)
- Database: Private network only
- Redis: Private network only
- Internal APIs: Not exposed externally

## WebSocket Security

### Connection Authentication

```python
@router.websocket("/ws/{room_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    room_id: str,
    token: str = Query(...)
):
    # Validate JWT token
    user = await validate_token(token)
    if not user:
        await websocket.close(code=1008)
        return
    
    await websocket.accept()
    # ... handle connection
```

### Rate Limiting
- Max connections per user: 3
- Max messages per minute: 60
- Auto-disconnect bei Abuse

### Message Validation
- Content sanitization
- Size limits (max 5000 chars)
- Type validation

## Plugin System Security

### Sandboxing (TODO)

```python
# Geplant: Container-basierte Sandbox
class PluginSandbox:
    """
    Isoliert Plugin-Ausführung in separatem Container
    - Begrenzte Ressourcen (CPU, Memory)
    - Kein Netzwerk-Zugriff (optional)
    - Kein Dateisystem-Zugriff außer tmp
    - Timeout nach 30 Sekunden
    """
    pass
```

### Plugin Validation
- Code-Review erforderlich
- Statische Code-Analyse
- Permission-System für Plugins

## Dependency Security

### Vulnerability Scanning

```bash
# pip-audit für Python Dependencies
pip install pip-audit
pip-audit

# Safety check
pip install safety
safety check --json
```

### Dependency Updates
- Regelmäßige Updates (monatlich)
- Security Patches sofort
- Automated Dependabot PRs

```yaml
# .github/dependabot.yml
version: 2
updates:
  - package-ecosystem: "pip"
    directory: "/"
    schedule:
      interval: "weekly"
    open-pull-requests-limit: 10
```

## Logging & Monitoring

### Security Logging

```python
# Wichtige Security-Events loggen
enhanced_logger.warning(
    "Failed login attempt",
    user=username,
    ip=request.client.host,
    timestamp=datetime.now()
)

enhanced_logger.info(
    "Successful authentication",
    user_id=user.id,
    role=user.role,
    ip=request.client.host
)

enhanced_logger.error(
    "Unauthorized access attempt",
    user_id=user.id,
    resource=resource,
    required_permission=permission
)
```

### Audit Trail
- Alle Admin-Aktionen loggen
- User-Änderungen tracken
- Sensitive Operations protokollieren

### Monitoring Alerts
- Failed login attempts (> 5 in 5 min)
- Unusual API patterns
- High error rates
- Resource exhaustion

## Incident Response

### Security Incident Plan

1. **Detection**: Monitoring alerts oder Security Reports
2. **Assessment**: Schweregrad bestimmen
3. **Containment**: Betroffene Services isolieren
4. **Eradication**: Vulnerability fixen
5. **Recovery**: Services wiederherstellen
6. **Lessons Learned**: Post-Mortem

### Kontakt
- **Security Issues**: security@yourdomain.com
- **Emergency**: +49 XXX XXXXXXX

## Vulnerability Disclosure

### Responsible Disclosure Policy

1. **Report**: Email an security@yourdomain.com
2. **Acknowledgment**: Innerhalb 24h
3. **Triage**: Innerhalb 72h
4. **Fix**: Nach Schweregrad
   - Critical: 7 Tage
   - High: 30 Tage
   - Medium: 90 Tage
5. **Public Disclosure**: Nach Fix + 30 Tage

### Bug Bounty (TODO)
Geplant für Production-Release.

## Compliance

### DSGVO / GDPR
- [ ] Datenschutzerklärung
- [ ] Cookie-Consent
- [ ] Recht auf Löschung
- [ ] Datenportabilität
- [ ] Privacy by Design

### Logging Compliance
- Keine PII in Logs (außer Audit-Logs)
- Log Retention: 90 Tage
- Verschlüsselte Log-Speicherung

## Security Checklist

### Pre-Deployment
- [ ] Alle Secrets aus Code entfernt
- [ ] Environment Variables gesetzt
- [ ] TLS/SSL aktiviert
- [ ] CORS korrekt konfiguriert
- [ ] Rate Limiting aktiviert
- [ ] Dependency Scan durchgeführt
- [ ] Security Headers gesetzt

### Post-Deployment
- [ ] Monitoring aktiv
- [ ] Alerts konfiguriert
- [ ] Backup-Strategie aktiv
- [ ] Incident Response Plan bereit
- [ ] Security Audit durchgeführt

## Security Headers

```python
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware

# Redirect HTTP to HTTPS
app.add_middleware(HTTPSRedirectMiddleware)

# Security Headers
@app.middleware("http")
async def add_security_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Content-Security-Policy"] = "default-src 'self'"
    return response
```

## Common Vulnerabilities

### Verhinderte Angriffe
✅ SQL Injection (ORM)
✅ XSS (Input Sanitization)
✅ CSRF (JWT Token)
✅ Session Hijacking (Secure Cookies, HTTPOnly)
✅ Clickjacking (X-Frame-Options)
✅ MIME Sniffing (X-Content-Type-Options)

### TODO: Weitere Härtung
- [ ] Content Security Policy (CSP) implementieren
- [ ] Subresource Integrity (SRI)
- [ ] DDoS Protection (CloudFlare/AWS Shield)
- [ ] Web Application Firewall (WAF)

## Weitere Ressourcen

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [OWASP API Security Top 10](https://owasp.org/www-project-api-security/)
- [CWE Top 25](https://cwe.mitre.org/top25/)
- [FastAPI Security Best Practices](https://fastapi.tiangolo.com/tutorial/security/)

---
*Letzte Aktualisierung: 2025-12-02*

**Bei Sicherheitsvorfällen oder Fragen: security@yourdomain.com**
