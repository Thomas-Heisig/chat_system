# Security Enhancements Guide

This document outlines recommended security enhancements for the Universal Chat System.

## Overview

While the system implements many security best practices (JWT authentication, bcrypt password hashing, rate limiting), there are additional security measures that can be implemented for enhanced protection.

## File Upload Security

### Virus Scanning (Recommended)

File uploads should be scanned for malware before being stored or served to users.

#### ClamAV Integration

**Installation**:
```bash
# Install ClamAV
sudo apt-get install clamav clamav-daemon

# Install Python client
pip install clamd
```

**Configuration**:

Create `services/virus_scanner.py`:

```python
import clamd
import os
from pathlib import Path
from typing import Dict, Any, Optional
from config.settings import logger


class VirusScannerService:
    """
    Virus scanning service using ClamAV
    
    Features:
    - Async file scanning
    - Quarantine management
    - Scan result caching
    - Admin notifications
    """
    
    def __init__(self):
        self.enabled = os.getenv("VIRUS_SCAN_ENABLED", "false").lower() == "true"
        self.quarantine_dir = Path(os.getenv("QUARANTINE_DIR", "./quarantine"))
        self.quarantine_dir.mkdir(exist_ok=True)
        
        if self.enabled:
            try:
                self.scanner = clamd.ClamdUnixSocket()
                self.scanner.ping()
                logger.info("🛡️ Virus scanner initialized (ClamAV)")
            except Exception as e:
                logger.error(f"❌ Failed to connect to ClamAV: {e}")
                self.enabled = False
    
    async def scan_file(self, file_path: str) -> Dict[str, Any]:
        """
        Scan a file for viruses
        
        Args:
            file_path: Path to file to scan
            
        Returns:
            Scan result with status and details
        """
        if not self.enabled:
            return {
                "scanned": False,
                "clean": True,
                "note": "Virus scanning disabled"
            }
        
        try:
            result = self.scanner.scan(file_path)
            file_status = result.get(file_path, ('OK', None))
            
            is_clean = file_status[0] == 'OK'
            
            if not is_clean:
                # Quarantine infected file
                await self._quarantine_file(file_path, file_status[1])
                await self._notify_admin(file_path, file_status[1])
            
            return {
                "scanned": True,
                "clean": is_clean,
                "status": file_status[0],
                "virus_name": file_status[1] if not is_clean else None,
                "quarantined": not is_clean
            }
            
        except Exception as e:
            logger.error(f"❌ Virus scan failed: {e}")
            return {
                "scanned": False,
                "error": str(e)
            }
    
    async def _quarantine_file(self, file_path: str, virus_name: str):
        """Move infected file to quarantine"""
        try:
            file_name = Path(file_path).name
            quarantine_path = self.quarantine_dir / f"{virus_name}_{file_name}"
            
            os.rename(file_path, quarantine_path)
            logger.warning(f"🔒 File quarantined: {file_name} ({virus_name})")
            
        except Exception as e:
            logger.error(f"❌ Quarantine failed: {e}")
    
    async def _notify_admin(self, file_path: str, virus_name: str):
        """Notify administrators of infected file"""
        logger.critical(
            f"🚨 VIRUS DETECTED: {file_path} - {virus_name}",
            extra={
                "alert_type": "virus_detected",
                "file_path": file_path,
                "virus_name": virus_name
            }
        )
        # TODO: Send email/Slack notification to admins


# Singleton instance
_virus_scanner: Optional[VirusScannerService] = None


def get_virus_scanner() -> VirusScannerService:
    """Get or create virus scanner singleton"""
    global _virus_scanner
    if _virus_scanner is None:
        _virus_scanner = VirusScannerService()
    return _virus_scanner
```

**Usage in File Upload**:

```python
from services.virus_scanner import get_virus_scanner

@app.post("/upload")
async def upload_file(file: UploadFile):
    # Save file temporarily
    temp_path = await save_temp_file(file)
    
    # Scan for viruses
    scanner = get_virus_scanner()
    scan_result = await scanner.scan_file(temp_path)
    
    if not scan_result["clean"]:
        os.remove(temp_path)
        raise HTTPException(
            status_code=400,
            detail=f"File rejected: {scan_result.get('virus_name', 'malware detected')}"
        )
    
    # Continue with normal processing
    return await process_clean_file(temp_path)
```

#### Async Scanning with Celery

For better performance, scan files asynchronously:

```python
from celery import Celery

celery = Celery('tasks', broker='redis://localhost:6379')

@celery.task
def scan_uploaded_file(file_id: int, file_path: str):
    """Async virus scan task"""
    scanner = get_virus_scanner()
    result = scanner.scan_file(file_path)
    
    if not result["clean"]:
        # Mark file as infected in database
        mark_file_infected(file_id, result["virus_name"])
        # Delete or quarantine file
        quarantine_file(file_path)
        # Notify admin
        notify_admin_virus_detected(file_id, file_path)
    else:
        # Mark file as clean
        mark_file_clean(file_id)
```

#### Cloud-Based Scanning

Alternative: Use cloud-based scanning services:

**AWS S3 with Malware Protection**:
```python
import boto3

def scan_s3_object(bucket: str, key: str):
    """Scan S3 object using AWS Malware Protection"""
    s3 = boto3.client('s3')
    
    # Enable S3 Malware Protection on bucket
    # Scans happen automatically on upload
    
    # Check scan results via tags
    tags = s3.get_object_tagging(Bucket=bucket, Key=key)
    
    for tag in tags['TagSet']:
        if tag['Key'] == 'MalwareScanStatus':
            return tag['Value'] == 'CLEAN'
    
    return False
```

**VirusTotal API**:
```python
import requests

def scan_with_virustotal(file_path: str, api_key: str):
    """Scan file using VirusTotal API"""
    url = 'https://www.virustotal.com/api/v3/files'
    
    with open(file_path, 'rb') as f:
        files = {'file': f}
        headers = {'x-apikey': api_key}
        
        response = requests.post(url, files=files, headers=headers)
        
    if response.status_code == 200:
        analysis_id = response.json()['data']['id']
        # Poll for results
        return get_virustotal_results(analysis_id, api_key)
```

### File Type Validation

Validate file types beyond just extension:

```python
import magic

def validate_file_type(file_path: str, allowed_types: list) -> bool:
    """
    Validate file type using magic numbers
    
    Args:
        file_path: Path to file
        allowed_types: List of allowed MIME types
        
    Returns:
        True if file type is allowed
    """
    mime = magic.Magic(mime=True)
    file_type = mime.from_file(file_path)
    
    return file_type in allowed_types
```

### File Size Limits

Implement strict file size limits:

```python
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

@app.post("/upload")
async def upload_file(file: UploadFile):
    # Check file size
    file_size = 0
    chunk_size = 1024 * 1024  # 1MB chunks
    temp_path = None
    
    try:
        temp_path = get_temp_path()  # Get temp file path
        
        with open(temp_path, 'wb') as f:
            while chunk := await file.read(chunk_size):
                file_size += len(chunk)
                
                if file_size > MAX_FILE_SIZE:
                    raise HTTPException(413, "File too large")
                
                f.write(chunk)
        
        # Continue processing if within size limit
        return await process_file(temp_path)
        
    except HTTPException:
        # Clean up temp file on error
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)
        raise
```

## Database Query Performance Monitoring

### Slow Query Logging

Implement query performance monitoring (Issue #14):

```python
from sqlalchemy import event
from sqlalchemy.engine import Engine
import time

@event.listens_for(Engine, "before_cursor_execute")
def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    conn.info.setdefault('query_start_time', []).append(time.time())

@event.listens_for(Engine, "after_cursor_execute")
def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    total = time.time() - conn.info['query_start_time'].pop(-1)
    
    # Log slow queries
    if total > 0.1:  # 100ms threshold
        logger.warning(
            "slow_query",
            duration=total,
            query=statement[:200],  # First 200 chars
            params=str(parameters)[:100]
        )
```

### Query Analysis

Enable query analysis in PostgreSQL:

```sql
-- Enable pg_stat_statements
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;

-- View slow queries
SELECT 
    calls,
    total_exec_time,
    mean_exec_time,
    query
FROM pg_stat_statements
ORDER BY mean_exec_time DESC
LIMIT 10;
```

### Index Optimization

Add indexes for common queries:

```python
# In models.py
class Message(Base):
    __tablename__ = "messages"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    created_at = Column(DateTime, index=True)
    
    # Composite index for common queries
    __table_args__ = (
        Index('idx_user_created', 'user_id', 'created_at'),
    )
```

## Request Signing for Critical Endpoints

### HMAC-Based Request Signing

Implement request signing to prevent replay attacks and ensure request integrity:

```python
import hmac
import hashlib
import time
from typing import Optional
from fastapi import HTTPException, Header, Request
from config.settings import API_SECRET_KEY, logger

class RequestSigner:
    """
    HMAC-based request signing for API security
    
    Features:
    - Request integrity verification
    - Replay attack prevention
    - Timestamp validation
    - Signature verification
    """
    
    def __init__(self, secret_key: str, max_age_seconds: int = 300):
        self.secret_key = secret_key.encode()
        self.max_age_seconds = max_age_seconds
    
    def sign_request(
        self,
        method: str,
        path: str,
        body: bytes,
        timestamp: int
    ) -> str:
        """
        Generate HMAC signature for request
        
        Args:
            method: HTTP method (GET, POST, etc.)
            path: Request path
            body: Request body bytes
            timestamp: Unix timestamp
            
        Returns:
            Hex-encoded HMAC signature
        """
        # Create canonical request string
        canonical = f"{method}\n{path}\n{timestamp}\n{body.hex()}"
        
        # Generate HMAC-SHA256 signature
        signature = hmac.new(
            self.secret_key,
            canonical.encode(),
            hashlib.sha256
        ).hexdigest()
        
        return signature
    
    async def verify_request(
        self,
        request: Request,
        signature: str,
        timestamp: int,
        body: bytes
    ) -> bool:
        """
        Verify request signature
        
        Args:
            request: FastAPI request object
            signature: Provided signature
            timestamp: Provided timestamp
            body: Request body bytes
            
        Returns:
            True if signature is valid
            
        Raises:
            HTTPException: If signature is invalid or request expired
        """
        # Check timestamp freshness (prevent replay attacks)
        current_time = int(time.time())
        age = current_time - timestamp
        
        if age > self.max_age_seconds:
            logger.warning(
                "expired_request",
                age=age,
                max_age=self.max_age_seconds,
                path=request.url.path
            )
            raise HTTPException(
                status_code=401,
                detail="Request expired"
            )
        
        if age < -60:  # Allow 1 minute clock skew
            logger.warning(
                "future_request",
                age=age,
                path=request.url.path
            )
            raise HTTPException(
                status_code=401,
                detail="Invalid timestamp"
            )
        
        # Generate expected signature
        expected_signature = self.sign_request(
            method=request.method,
            path=str(request.url.path),
            body=body,
            timestamp=timestamp
        )
        
        # Compare signatures (constant-time to prevent timing attacks)
        if not hmac.compare_digest(signature, expected_signature):
            logger.warning(
                "invalid_signature",
                path=request.url.path,
                provided=signature[:20] + "...",
                expected=expected_signature[:20] + "..."
            )
            raise HTTPException(
                status_code=401,
                detail="Invalid signature"
            )
        
        return True

# Initialize signer
request_signer = RequestSigner(
    secret_key=os.getenv("API_SECRET_KEY", "change-me-in-production"),
    max_age_seconds=300  # 5 minutes
)
```

### Dependency for Signature Verification

```python
from fastapi import Depends, Header

async def verify_signature(
    request: Request,
    x_signature: str = Header(...),
    x_timestamp: int = Header(...),
) -> bool:
    """
    FastAPI dependency for request signature verification
    
    Usage:
        @app.post("/api/critical-action", dependencies=[Depends(verify_signature)])
        async def critical_action():
            pass
    """
    # Read request body
    body = await request.body()
    
    # Verify signature
    await request_signer.verify_request(
        request=request,
        signature=x_signature,
        timestamp=x_timestamp,
        body=body
    )
    
    return True
```

### Protecting Critical Endpoints

```python
from fastapi import APIRouter, Depends

router = APIRouter()

@router.post("/api/admin/users", dependencies=[Depends(verify_signature)])
async def create_admin_user(user_data: dict):
    """Create admin user (requires signed request)"""
    # This endpoint requires valid request signature
    return await user_service.create_admin(user_data)

@router.delete("/api/admin/users/{user_id}", dependencies=[Depends(verify_signature)])
async def delete_user(user_id: int):
    """Delete user (requires signed request)"""
    # This endpoint requires valid request signature
    return await user_service.delete(user_id)

@router.post("/api/payments/process", dependencies=[Depends(verify_signature)])
async def process_payment(payment_data: dict):
    """Process payment (requires signed request)"""
    # This endpoint requires valid request signature
    return await payment_service.process(payment_data)
```

### Client-Side Implementation

**Python Client:**

```python
import requests
import hmac
import hashlib
import time
import json

class SignedAPIClient:
    """Client for making signed API requests"""
    
    def __init__(self, base_url: str, api_key: str, secret_key: str):
        self.base_url = base_url
        self.api_key = api_key
        self.secret_key = secret_key.encode()
    
    def _sign_request(self, method: str, path: str, body: bytes, timestamp: int) -> str:
        """Generate request signature"""
        canonical = f"{method}\n{path}\n{timestamp}\n{body.hex()}"
        signature = hmac.new(
            self.secret_key,
            canonical.encode(),
            hashlib.sha256
        ).hexdigest()
        return signature
    
    def post(self, path: str, data: dict):
        """Make signed POST request"""
        timestamp = int(time.time())
        body = json.dumps(data).encode()
        
        signature = self._sign_request("POST", path, body, timestamp)
        
        response = requests.post(
            f"{self.base_url}{path}",
            json=data,
            headers={
                "X-API-Key": self.api_key,
                "X-Signature": signature,
                "X-Timestamp": str(timestamp),
                "Content-Type": "application/json"
            }
        )
        
        return response

# Usage
client = SignedAPIClient(
    base_url="https://api.example.com",
    api_key="your-api-key",
    secret_key="your-secret-key"
)

response = client.post("/api/admin/users", {
    "username": "newadmin",
    "email": "admin@example.com"
})
```

**JavaScript/Node.js Client:**

```javascript
const crypto = require('crypto');
const axios = require('axios');

class SignedAPIClient {
    constructor(baseURL, apiKey, secretKey) {
        this.baseURL = baseURL;
        this.apiKey = apiKey;
        this.secretKey = secretKey;
    }
    
    signRequest(method, path, body, timestamp) {
        // Create canonical request
        const bodyHex = Buffer.from(body).toString('hex');
        const canonical = `${method}\n${path}\n${timestamp}\n${bodyHex}`;
        
        // Generate HMAC signature
        const signature = crypto
            .createHmac('sha256', this.secretKey)
            .update(canonical)
            .digest('hex');
        
        return signature;
    }
    
    async post(path, data) {
        const timestamp = Math.floor(Date.now() / 1000);
        const body = JSON.stringify(data);
        
        const signature = this.signRequest('POST', path, body, timestamp);
        
        const response = await axios.post(
            `${this.baseURL}${path}`,
            data,
            {
                headers: {
                    'X-API-Key': this.apiKey,
                    'X-Signature': signature,
                    'X-Timestamp': timestamp.toString(),
                    'Content-Type': 'application/json'
                }
            }
        );
        
        return response.data;
    }
}

// Usage
const client = new SignedAPIClient(
    'https://api.example.com',
    'your-api-key',
    'your-secret-key'
);

client.post('/api/admin/users', {
    username: 'newadmin',
    email: 'admin@example.com'
}).then(response => {
    console.log('User created:', response);
});
```

### Replay Attack Prevention

The implementation prevents replay attacks through:

1. **Timestamp Validation:** Requests older than `max_age_seconds` (default 5 minutes) are rejected
2. **Signature Uniqueness:** Each signature includes timestamp, making it valid only for a short window
3. **Request Binding:** Signature includes method, path, and body, preventing request modification

### Configuration

Add to `.env`:

```bash
# Request Signing Configuration
API_SECRET_KEY=<generate-strong-secret-key>
REQUEST_MAX_AGE_SECONDS=300
ENABLE_REQUEST_SIGNING=true
```

Generate strong secret key:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

### Monitoring Signed Requests

Track signature verification metrics:

```python
from prometheus_client import Counter

signature_verifications = Counter(
    'api_signature_verifications_total',
    'Total signature verifications',
    ['status', 'endpoint']
)

# In verify_request method
signature_verifications.labels(
    status='success' if valid else 'failed',
    endpoint=request.url.path
).inc()
```

---

## Additional Security Measures

### Rate Limiting Enhancement

Implement advanced rate limiting:

```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.post("/api/chat")
@limiter.limit("10/minute")
async def chat_endpoint(request: Request):
    # Endpoint logic
    pass
```

### Input Sanitization

Sanitize user inputs:

```python
import bleach

def sanitize_html(text: str) -> str:
    """Remove dangerous HTML tags"""
    allowed_tags = ['b', 'i', 'u', 'a', 'p', 'br']
    allowed_attrs = {'a': ['href', 'title']}
    
    return bleach.clean(
        text,
        tags=allowed_tags,
        attributes=allowed_attrs,
        strip=True
    )
```

### SQL Injection Prevention

Always use parameterized queries (already implemented with SQLAlchemy):

```python
# ✅ GOOD - Parameterized
session.query(User).filter(User.username == username).first()

# ❌ BAD - String concatenation
session.execute(f"SELECT * FROM users WHERE username = '{username}'")
```

### CSRF Protection

Implement CSRF tokens for state-changing operations:

```python
from fastapi_csrf_protect import CsrfProtect

@app.post("/important-action")
async def important_action(csrf_protect: CsrfProtect = Depends()):
    await csrf_protect.validate_csrf()
    # Action logic
```

### Content Security Policy

Add CSP headers:

```python
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline'; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data: https:;"
    )
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    return response
```

## Security Checklist

- [ ] Implement virus scanning for file uploads
- [ ] Enable slow query logging
- [ ] Add database query performance monitoring
- [ ] Implement advanced rate limiting
- [ ] Add input sanitization for user content
- [ ] Enable CSRF protection
- [ ] Add Content Security Policy headers
- [ ] Implement file type validation
- [ ] Set up security monitoring and alerting
- [ ] Regular security audits and penetration testing
- [ ] Keep dependencies updated (automated with Dependabot)
- [ ] Implement secrets management (HashiCorp Vault, AWS Secrets Manager)

## References

- [ClamAV Documentation](https://docs.clamav.net/)
- [OWASP Security Cheat Sheets](https://cheatsheetseries.owasp.org/)
- [FastAPI Security Documentation](https://fastapi.tiangolo.com/tutorial/security/)
- [SQLAlchemy Security Best Practices](https://docs.sqlalchemy.org/en/14/faq/security.html)
