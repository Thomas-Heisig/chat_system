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
    
    with open(temp_path, 'wb') as f:
        while chunk := await file.read(chunk_size):
            file_size += len(chunk)
            
            if file_size > MAX_FILE_SIZE:
                f.close()
                os.remove(temp_path)
                raise HTTPException(413, "File too large")
            
            f.write(chunk)
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
