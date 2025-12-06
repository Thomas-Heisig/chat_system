# Troubleshooting Guide

This guide helps you diagnose and resolve common issues with the Universal Chat System.

## Table of Contents

- [Installation Issues](#installation-issues)
- [Database Issues](#database-issues)
- [Authentication Issues](#authentication-issues)
- [WebSocket Connection Issues](#websocket-connection-issues)
- [AI Integration Issues](#ai-integration-issues)
- [RAG System Issues](#rag-system-issues)
- [Plugin System Issues](#plugin-system-issues)
- [Performance Issues](#performance-issues)
- [Docker Issues](#docker-issues)
- [Logging and Debugging](#logging-and-debugging)

---

## Installation Issues

### Issue: `pip install` fails with dependency conflicts

**Symptoms:**
```
ERROR: Cannot install package-a and package-b because these package versions have conflicting dependencies.
```

**Solutions:**
1. Update pip to the latest version:
   ```bash
   pip install --upgrade pip
   ```

2. Use a clean virtual environment:
   ```bash
   rm -rf venv
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. Install dependencies one by one to identify the problematic package:
   ```bash
   pip install -r requirements.txt --no-deps
   pip install <package-name>
   ```

### Issue: Python version incompatibility

**Symptoms:**
```
ERROR: This package requires Python >=3.9
```

**Solution:**
1. Check your Python version:
   ```bash
   python --version
   ```

2. Install Python 3.9+ from [python.org](https://www.python.org/downloads/)

3. Use the correct Python version in your virtual environment:
   ```bash
   python3.9 -m venv venv
   ```

---

## Database Issues

### Issue: Database connection fails

**Symptoms:**
```
sqlalchemy.exc.OperationalError: could not connect to server
```

**Solutions:**

**For PostgreSQL:**
1. Verify PostgreSQL is running:
   ```bash
   sudo systemctl status postgresql  # Linux
   brew services list  # macOS
   ```

2. Check connection string in `.env`:
   ```bash
   DATABASE_URL=postgresql://user:password@localhost:5432/chatdb
   ```

3. Test connection manually:
   ```bash
   psql -h localhost -U user -d chatdb
   ```

4. Check firewall rules allow connections to port 5432

**For MongoDB:**
1. Verify MongoDB is running:
   ```bash
   sudo systemctl status mongod  # Linux
   brew services list  # macOS
   ```

2. Check connection string:
   ```bash
   DATABASE_URL=mongodb://localhost:27017/chatdb
   ```

3. Test connection:
   ```bash
   mongo mongodb://localhost:27017/chatdb
   ```

### Issue: Database migrations fail

**Symptoms:**
```
alembic.util.exc.CommandError: Can't locate revision identified by 'xxxxx'
```

**Solutions:**
1. Reset Alembic:
   ```bash
   # Backup your database first!
   alembic stamp head
   ```

2. Create fresh database:
   ```bash
   # SQLite
   rm chat.db
   python main.py  # Auto-creates database
   
   # PostgreSQL
   dropdb chatdb
   createdb chatdb
   alembic upgrade head
   ```

3. Check Alembic configuration in `alembic.ini` and `alembic/env.py`

### Issue: "Table already exists" error

**Symptoms:**
```
sqlalchemy.exc.OperationalError: table "users" already exists
```

**Solution:**
1. Drop all tables and recreate:
   ```python
   from database.models import Base
   from database.connection import engine
   
   Base.metadata.drop_all(engine)
   Base.metadata.create_all(engine)
   ```

2. Or use Alembic to manage schema:
   ```bash
   alembic downgrade base
   alembic upgrade head
   ```

---

## Authentication Issues

### Issue: Unable to login with default credentials

**Symptoms:**
- Login fails with `admin` / `admin123`
- "Invalid credentials" error

**Solutions:**
1. Check if admin user was created:
   ```python
   # Run in Python console
   from database.repositories.user_repository import UserRepository
   repo = UserRepository()
   users = repo.get_all()
   print([u.username for u in users])
   ```

2. Manually create admin user:
   ```python
   from services.auth_service import AuthService
   auth = AuthService()
   auth.register_user("admin", "your-new-password", role="admin")
   ```

3. Reset admin password:
   ```python
   from database.repositories.user_repository import UserRepository
   from utils.password_utils import hash_password
   
   repo = UserRepository()
   user = repo.get_by_username("admin")
   user.password = hash_password("new-password")
   repo.update(user)
   ```

### Issue: JWT token expired

**Symptoms:**
```
{"detail": "Token has expired"}
```

**Solution:**
1. Login again to get a new token

2. Increase token expiration time in `.env`:
   ```bash
   JWT_ACCESS_TOKEN_EXPIRE_MINUTES=60  # Default is 30
   ```

### Issue: "Invalid token" error

**Symptoms:**
```
{"detail": "Could not validate credentials"}
```

**Solutions:**
1. Check `JWT_SECRET_KEY` is set and consistent:
   ```bash
   echo $JWT_SECRET_KEY
   ```

2. Generate a new secret key:
   ```python
   import secrets
   print(secrets.token_urlsafe(32))
   ```

3. Clear browser cookies and login again

---

## WebSocket Connection Issues

### Issue: WebSocket connection fails

**Symptoms:**
```
WebSocket connection failed: Error during WebSocket handshake
```

**Solutions:**
1. Check WebSocket URL format:
   ```javascript
   // Correct
   ws://localhost:8000/ws
   wss://yourdomain.com/ws  // For HTTPS
   
   // Incorrect
   http://localhost:8000/ws
   ```

2. Verify CORS settings in `.env`:
   ```bash
   CORS_ORIGINS=["http://localhost:3000", "http://localhost:8000"]
   ```

3. Check reverse proxy configuration (if using nginx/Apache):
   ```nginx
   # nginx
   location /ws {
       proxy_pass http://localhost:8000;
       proxy_http_version 1.1;
       proxy_set_header Upgrade $http_upgrade;
       proxy_set_header Connection "upgrade";
   }
   ```

### Issue: WebSocket disconnects frequently

**Symptoms:**
- Connection drops after a few seconds/minutes
- Constant reconnection attempts

**Solutions:**
1. Implement heartbeat/ping-pong:
   ```javascript
   // Already implemented in static/js/chat.js
   setInterval(() => {
       if (socket.readyState === WebSocket.OPEN) {
           socket.send(JSON.stringify({ type: 'ping' }));
       }
   }, 30000);
   ```

2. Check proxy timeout settings:
   ```nginx
   # nginx
   proxy_read_timeout 3600s;
   proxy_send_timeout 3600s;
   ```

3. Monitor network stability and firewall rules

---

## AI Integration Issues

### Issue: Ollama connection fails

**Symptoms:**
```
Error: Could not connect to Ollama at http://localhost:11434
```

**Solutions:**
1. Verify Ollama is running:
   ```bash
   curl http://localhost:11434/api/tags
   ```

2. Start Ollama:
   ```bash
   ollama serve
   ```

3. Check Ollama URL in `.env`:
   ```bash
   OLLAMA_URL=http://localhost:11434
   ```

4. If using Docker, ensure container can reach host:
   ```bash
   # Use host.docker.internal on Docker Desktop
   OLLAMA_URL=http://host.docker.internal:11434
   ```

### Issue: AI model not found

**Symptoms:**
```
Error: Model 'llama2' not found
```

**Solution:**
1. List available models:
   ```bash
   ollama list
   ```

2. Pull the model:
   ```bash
   ollama pull llama2
   ```

3. Update model name in `.env`:
   ```bash
   OLLAMA_MODEL=llama2
   ```

### Issue: AI responses are slow

**Symptoms:**
- Requests timeout
- Very long response times (>60s)

**Solutions:**
1. Use a smaller/faster model:
   ```bash
   OLLAMA_MODEL=llama2:7b  # Instead of 70b
   ```

2. Increase timeout in code:
   ```python
   # In services/ai_service.py
   timeout = 120  # Increase from 60
   ```

3. Enable GPU acceleration (if available):
   ```bash
   # Check if GPU is detected
   ollama ps
   ```

---

## RAG System Issues

### Issue: Documents not being indexed

**Symptoms:**
- Upload succeeds but documents don't appear in searches
- No results from RAG queries

**Solutions:**
1. Check RAG is enabled in `.env`:
   ```bash
   RAG_ENABLED=true
   ```

2. Verify vector database is running:
   ```bash
   # For ChromaDB (built-in)
   ls -la ./chroma_db
   
   # For Qdrant
   curl http://localhost:6333/health
   
   # For Pinecone
   # Check API key is valid
   ```

3. Check document processing logs:
   ```bash
   tail -f logs/chat_system.log | grep "document"
   ```

4. Manually test document upload:
   ```bash
   curl -X POST http://localhost:8000/api/rag/documents \
     -H "Authorization: Bearer $TOKEN" \
     -F "file=@test.pdf"
   ```

### Issue: Vector database connection fails

**Symptoms:**
```
Error: Could not connect to vector database
```

**Solutions:**

**For ChromaDB:**
1. Check directory permissions:
   ```bash
   ls -ld ./chroma_db
   chmod 755 ./chroma_db
   ```

**For Qdrant:**
1. Verify Qdrant is running:
   ```bash
   curl http://localhost:6333/health
   ```

2. Start Qdrant:
   ```bash
   docker run -p 6333:6333 qdrant/qdrant
   ```

**For Pinecone:**
1. Verify API key:
   ```bash
   echo $PINECONE_API_KEY
   ```

2. Check index exists in Pinecone dashboard

### Issue: Search results not relevant

**Symptoms:**
- Queries return unrelated documents
- Low similarity scores

**Solutions:**
1. Check embedding model consistency:
   ```python
   # Ensure same model used for indexing and querying
   EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
   ```

2. Adjust similarity threshold:
   ```python
   # In RAG query
   results = rag_service.query(query, top_k=5, min_similarity=0.7)
   ```

3. Re-index documents with better chunking:
   ```python
   # Adjust chunk size and overlap
   chunk_size = 1000  # Tokens
   chunk_overlap = 200
   ```

---

## Plugin System Issues

### Issue: Plugin installation fails

**Symptoms:**
```
Error: Plugin installation not yet implemented
```

**Solution:**
This is expected - plugin installation is currently a stub. Plugins need to be manually placed in the `plugins/` directory with proper structure:

```
plugins/
└── my-plugin/
    ├── plugin.json
    └── main.py
```

Example `plugin.json`:
```json
{
  "id": "my-plugin-id",
  "name": "My Plugin",
  "version": "1.0.0",
  "description": "Plugin description",
  "author": "Author Name",
  "permissions": ["filesystem_read", "api_access"],
  "entry_point": "main.py"
}
```

### Issue: Docker not available for plugin sandbox

**Symptoms:**
```
Error: Docker SDK not installed
```

**Solutions:**
1. Install Docker SDK:
   ```bash
   pip install docker
   ```

2. Verify Docker is running:
   ```bash
   docker ps
   ```

3. On Linux, add user to docker group:
   ```bash
   sudo usermod -aG docker $USER
   newgrp docker
   ```

### Issue: Plugin execution fails

**Symptoms:**
```
Error: Plugin execution not implemented
```

**Solution:**
Plugin execution is disabled by default for security. To enable (for development only):
```bash
export ENABLE_PLUGIN_EXECUTION=true
```

**WARNING:** Only enable in trusted development environments.

---

## Performance Issues

### Issue: Slow application startup

**Symptoms:**
- Application takes >30 seconds to start
- High CPU during startup

**Solutions:**
1. Disable unnecessary services in `.env`:
   ```bash
   RAG_ENABLED=false  # If not using RAG
   AI_ENABLED=false   # If not using AI
   ```

2. Use production ASGI server:
   ```bash
   uvicorn main:app --workers 4
   ```

3. Optimize database connection pool:
   ```python
   # In database/connection.py
   engine = create_engine(
       DATABASE_URL,
       pool_size=10,
       max_overflow=20
   )
   ```

### Issue: High memory usage

**Symptoms:**
- Application uses >2GB RAM
- OOM (Out of Memory) errors

**Solutions:**
1. Reduce AI model size:
   ```bash
   OLLAMA_MODEL=llama2:7b  # Smaller model
   ```

2. Limit WebSocket connections:
   ```python
   # In websocket/manager.py
   MAX_CONNECTIONS = 100
   ```

3. Use connection pooling for database:
   ```python
   pool_size=5  # Reduce from 10
   max_overflow=10  # Reduce from 20
   ```

### Issue: Slow API responses

**Symptoms:**
- API requests take >2 seconds
- Timeout errors

**Solutions:**
1. Add database indexes:
   ```python
   # In database/models/
   class Message(Base):
       __tablename__ = "messages"
       # Add indexes
       __table_args__ = (
           Index('idx_created_at', 'created_at'),
           Index('idx_username', 'username'),
       )
   ```

2. Enable response caching:
   ```python
   from fastapi_cache import FastAPICache
   from fastapi_cache.backends.redis import RedisBackend
   ```

3. Use pagination for large results:
   ```python
   # Limit results
   @app.get("/api/messages")
   async def get_messages(skip: int = 0, limit: int = 50):
       return messages[skip:skip + limit]
   ```

---

## Docker Issues

### Issue: Docker Compose fails to start

**Symptoms:**
```
ERROR: Service 'app' failed to build
```

**Solutions:**
1. Check Docker Compose version:
   ```bash
   docker-compose --version  # Should be 1.27+
   ```

2. Rebuild images:
   ```bash
   docker-compose build --no-cache
   docker-compose up -d
   ```

3. Check for port conflicts:
   ```bash
   # Check if port 8000 is in use
   lsof -i :8000
   netstat -an | grep 8000
   ```

### Issue: Cannot connect to services in Docker

**Symptoms:**
- App can't reach database
- Network errors between containers

**Solutions:**
1. Use Docker network names:
   ```bash
   # In docker-compose.yml
   DATABASE_URL=postgresql://user:pass@postgres:5432/chatdb
   OLLAMA_URL=http://ollama:11434
   ```

2. Verify network exists:
   ```bash
   docker network ls
   docker network inspect chat_system_default
   ```

3. Check container logs:
   ```bash
   docker-compose logs app
   docker-compose logs postgres
   ```

---

## Logging and Debugging

### Enable Debug Logging

1. Set log level in `.env`:
   ```bash
   LOG_LEVEL=DEBUG
   APP_DEBUG=true
   ```

2. Check logs:
   ```bash
   tail -f logs/chat_system.log
   ```

3. Use structured logging:
   ```python
   from config.settings import logger
   logger.debug("Debug message", extra={"user": "admin"})
   logger.info("Info message")
   logger.warning("Warning message")
   logger.error("Error message", exc_info=True)
   ```

### Common Log Patterns

**Database Issues:**
```bash
grep -i "database" logs/chat_system.log
grep -i "sqlalchemy" logs/chat_system.log
```

**Authentication Issues:**
```bash
grep -i "auth" logs/chat_system.log
grep -i "token" logs/chat_system.log
```

**WebSocket Issues:**
```bash
grep -i "websocket" logs/chat_system.log
grep -i "connection" logs/chat_system.log
```

### Debug Tools

1. **Python Debugger (pdb):**
   ```python
   import pdb; pdb.set_trace()
   ```

2. **FastAPI Debug Mode:**
   ```bash
   uvicorn main:app --reload --log-level debug
   ```

3. **Database Query Logging:**
   ```python
   # In database/connection.py
   engine = create_engine(DATABASE_URL, echo=True)
   ```

---

## Getting Additional Help

If you're still experiencing issues:

1. **Check Documentation:**
   - [Setup Guide](../SETUP.md)
   - [Architecture](../ARCHITECTURE.md)
   - [API Documentation](API.md)

2. **Search Issues:**
   - GitHub Issues: https://github.com/Thomas-Heisig/chat_system/issues
   - Check if someone has reported similar issue

3. **Create New Issue:**
   - Include error messages
   - Include relevant logs
   - Include system information (OS, Python version, Docker version)
   - Include steps to reproduce

4. **Community Support:**
   - GitHub Discussions
   - Stack Overflow (tag: `chat-system`)

---

## Preventive Measures

1. **Regular Backups:**
   ```bash
   # Backup database
   pg_dump chatdb > backup_$(date +%Y%m%d).sql
   ```

2. **Monitor Logs:**
   ```bash
   # Watch for errors
   tail -f logs/chat_system.log | grep -i error
   ```

3. **Health Checks:**
   ```bash
   # Check system health
   curl http://localhost:8000/health
   curl http://localhost:8000/status
   ```

4. **Update Dependencies:**
   ```bash
   pip list --outdated
   pip install --upgrade -r requirements.txt
   ```

5. **Test Before Deploying:**
   ```bash
   pytest tests/
   ```

---

**Last Updated:** 2025-12-06
