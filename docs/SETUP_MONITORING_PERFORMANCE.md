# Setup Guide: Monitoring & Performance Enhancements

**Date:** 2025-12-06  
**Version:** 1.0  
**Related:** [IMPLEMENTATION_STATUS.md](IMPLEMENTATION_STATUS.md)

This guide helps you set up and configure the newly implemented monitoring and performance features.

---

## 🎯 Quick Start

### 1. Environment Variables

Add these to your `.env` file:

```bash
# Sentry Error Tracking (Optional)
SENTRY_DSN=https://your-sentry-dsn@sentry.io/project-id

# Redis (for caching and distributed features)
REDIS_HOST=localhost
REDIS_PORT=6379

# Performance Monitoring
SLOW_QUERY_THRESHOLD_MS=100  # Log queries slower than this
ENABLE_QUERY_LOGGING=true
ENABLE_POOL_MONITORING=true
```

### 2. Start the Application

```bash
# Start with all new features enabled
python main.py
```

The application now has:
- ✅ Prometheus metrics at `/metrics`
- ✅ Enhanced health checks at `/health/*`
- ✅ Response compression (automatic)
- ✅ Security headers (automatic)
- ✅ Sentry error tracking (if DSN configured)
- ✅ Database query monitoring (automatic)

---

## 📊 Prometheus Metrics

### Access Metrics

```bash
# View raw metrics
curl http://localhost:8000/metrics

# Or open in browser
open http://localhost:8000/metrics
```

### Available Metrics

**HTTP Metrics:**
- `http_requests_total` - Total HTTP requests
- `http_request_duration_seconds` - Request duration histogram
- `http_requests_in_progress` - Current requests being processed

**Application Metrics:**
- `websocket_connections_active` - Active WebSocket connections
- `database_connections_active` - Active database connections
- `database_query_duration_seconds` - Database query duration histogram

**Cache Metrics:**
- `cache_hits_total` - Cache hits
- `cache_misses_total` - Cache misses

**AI/RAG Metrics:**
- `ai_requests_total` - AI requests
- `ai_request_duration_seconds` - AI request duration
- `rag_queries_total` - RAG queries

**File Upload Metrics:**
- `file_uploads_total` - File uploads
- `file_upload_size_bytes` - File upload sizes

**Error Metrics:**
- `errors_total` - Total errors

### Track Custom Metrics

```python
from middleware import (
    track_database_query,
    track_ai_request,
    track_cache_operation,
    track_file_upload,
    track_websocket_connection,
)

# Track database query
track_database_query("SELECT", duration_seconds=0.025)

# Track AI request
track_ai_request("llama2", duration=1.5, success=True)

# Track cache operation
track_cache_operation("redis", hit=True)

# Track file upload
track_file_upload(success=True, file_type="pdf", size_bytes=1024000)

# Track WebSocket connection
track_websocket_connection(connected=True)  # On connect
track_websocket_connection(connected=False)  # On disconnect
```

### Prometheus Server Setup

**Using Docker Compose:**

```yaml
# docker-compose.yml
services:
  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'

volumes:
  prometheus_data:
```

**prometheus.yml:**

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'chat-system'
    static_configs:
      - targets: ['chat-system:8000']  # Or 'localhost:8000' for local
    metrics_path: '/metrics'
```

**Start Prometheus:**

```bash
docker-compose up -d prometheus
# Access at http://localhost:9090
```

---

## 🚨 Sentry Error Tracking

### Setup

1. **Create Sentry Account:** https://sentry.io
2. **Create New Project:** Select FastAPI/Python
3. **Get DSN:** Copy the DSN from project settings
4. **Configure:**

```bash
# .env
SENTRY_DSN=https://your-key@sentry.io/project-id
```

### Features

- **Automatic Error Capture:** Unhandled exceptions are automatically sent to Sentry
- **Performance Monitoring:** Transaction traces for slow endpoints
- **Breadcrumbs:** Trail of events leading to errors
- **User Context:** Identify which users experience errors
- **Release Tracking:** Track errors per version

### Manual Error Capture

```python
from core.sentry_config import (
    capture_exception,
    capture_message,
    add_breadcrumb,
    set_user_context,
)

# Add breadcrumb
add_breadcrumb("User logged in", category="auth", level="info")

# Set user context
set_user_context(user_id="123", username="john")

# Capture exception
try:
    risky_operation()
except Exception as e:
    capture_exception(e, component="payment", order_id="456")

# Capture message
capture_message("Low disk space", level="warning", disk_usage=95)
```

### Configuration

```python
# Sampling rates (0.0 to 1.0)
# Production: Low sampling to reduce costs
# Staging: Higher sampling for better debugging
# Development: No auto-init to reduce noise

# In core/sentry_config.py (already configured):
# Production: 20% traces, 10% profiles
# Staging: 50% traces, 20% profiles
```

---

## 🏥 Health Checks

### Endpoints

1. **Basic Health:** `GET /health`
   ```bash
   curl http://localhost:8000/health
   ```
   Response:
   ```json
   {
     "status": "healthy",
     "timestamp": 1701878400.0,
     "version": "2.0.0",
     "environment": "production"
   }
   ```

2. **Liveness Probe:** `GET /health/liveness`
   ```bash
   curl http://localhost:8000/health/liveness
   ```
   For Kubernetes to check if app is alive (not deadlocked)

3. **Readiness Probe:** `GET /health/readiness`
   ```bash
   curl http://localhost:8000/health/readiness
   ```
   For Kubernetes to check if app is ready for traffic

4. **Detailed Health:** `GET /health/detailed`
   ```bash
   curl http://localhost:8000/health/detailed
   ```
   Response:
   ```json
   {
     "status": "healthy",
     "timestamp": 1701878400.0,
     "app": {...},
     "components": {
       "database": {"status": "healthy"},
       "cache": {"status": "healthy"},
       "ai_service": {"status": "healthy"},
       "websocket": {"status": "healthy"},
       "disk": {"status": "healthy", "usage_percent": 45.2},
       "memory": {"status": "healthy", "usage_percent": 62.3}
     },
     "metrics": {
       "cpu_usage_percent": 25.5,
       "memory_usage_percent": 62.3,
       "disk_usage_percent": 45.2
     }
   }
   ```

### Kubernetes Integration

```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
spec:
  template:
    spec:
      containers:
      - name: chat-system
        livenessProbe:
          httpGet:
            path: /health/liveness
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
          timeoutSeconds: 5
          failureThreshold: 3
        
        readinessProbe:
          httpGet:
            path: /health/readiness
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 5
          timeoutSeconds: 3
          failureThreshold: 3
```

---

## 🗄️ Database Performance Monitoring

### Automatic Monitoring

The performance monitor is automatically set up and tracks:
- Query execution time
- Slow queries (>100ms by default)
- Connection pool usage
- Query operation types

### View Performance Statistics

```python
from database.performance_monitor import get_performance_monitor

monitor = get_performance_monitor()
if monitor:
    stats = monitor.get_statistics()
    print(stats)
    # Output:
    # {
    #   "total_queries": 1542,
    #   "slow_queries": 23,
    #   "slow_query_percentage": "1.49%",
    #   "slow_query_threshold_ms": 100.0
    # }
```

### Check Logs for Slow Queries

```bash
# Slow queries are logged as warnings
grep "Slow database query" logs/chat_system.log

# Example output:
# WARNING - Slow database query detected - operation=SELECT duration_ms=245.32 statement=SELECT * FROM messages WHERE...
```

### Custom Query Tracking

```python
from database.performance_monitor import track_query_performance

with track_query_performance("fetch_user_messages"):
    messages = session.query(Message).filter_by(user_id=user_id).all()
```

---

## 📇 Database Indexes

### Apply Performance Indexes

```bash
# Create all indexes
python -m database.migrations.add_performance_indexes create

# Output:
# Creating performance indexes...
# Created index: idx_messages_username_created on messages(username, created_at)
#   Purpose: Optimize queries filtering by username and sorting by date
# Created index: idx_messages_created_at on messages(created_at)
#   Purpose: Optimize queries sorting/filtering by creation date
# ...
# Created 14 indexes successfully
```

### Remove Indexes (if needed)

```bash
python -m database.migrations.add_performance_indexes drop
```

### Verify Indexes

**PostgreSQL:**
```sql
SELECT indexname, indexdef 
FROM pg_indexes 
WHERE tablename = 'messages';
```

**SQLite:**
```sql
SELECT name, sql 
FROM sqlite_master 
WHERE type = 'index' AND tbl_name = 'messages';
```

### Index Coverage

| Table | Indexes | Purpose |
|-------|---------|---------|
| messages | 3 | username+date, date, type |
| projects | 2 | status+date, owner |
| tickets | 4 | project+status, assigned, priority+status, due_date |
| files | 3 | project, ticket, type |
| users | 2 | username, role |

---

## 🗜️ Response Compression

### Automatic Compression

Compression is automatic! The middleware:
- Detects client support (Accept-Encoding header)
- Compresses responses > 500 bytes
- Uses Brotli (best) or Gzip (fallback)
- Only compresses if result is smaller
- Adds appropriate Content-Encoding header

### Test Compression

```bash
# Request with compression support
curl -H "Accept-Encoding: gzip, br" http://localhost:8000/api/messages -I

# Check response headers:
# Content-Encoding: br  (or gzip)
# Vary: Accept-Encoding
```

### Configuration

Adjust in `main.py`:
```python
app.add_middleware(
    CompressionMiddleware,
    minimum_size=500,      # Min size to compress (bytes)
    gzip_level=6,         # Gzip level 0-9 (6 is good balance)
    brotli_quality=4,     # Brotli quality 0-11 (4 is fast)
)
```

---

## 🔒 Security Headers

### Automatic Security Headers

All responses automatically include:
- **Content-Security-Policy:** Nonce-based CSP
- **X-Frame-Options:** DENY
- **X-Content-Type-Options:** nosniff
- **X-XSS-Protection:** 1; mode=block
- **Strict-Transport-Security:** (production only)
- **Referrer-Policy:** strict-origin-when-cross-origin
- **Permissions-Policy:** Disables unnecessary features

### Verify Headers

```bash
curl -I http://localhost:8000/

# Check for security headers in response
```

### CSP Nonce for Inline Scripts

If you need inline scripts/styles:

```python
from middleware.security_middleware import get_csp_nonce

@app.get("/page")
async def page(request: Request):
    nonce = get_csp_nonce(request)
    return templates.TemplateResponse("page.html", {
        "request": request,
        "csp_nonce": nonce
    })
```

```html
<!-- In template -->
<script nonce="{{ csp_nonce }}">
  // Inline script allowed with nonce
  console.log("Hello");
</script>
```

---

## 🔧 Monitoring Dashboard Setup

### Grafana Setup

1. **Start Grafana:**
   ```bash
   docker run -d -p 3000:3000 grafana/grafana
   ```

2. **Access:** http://localhost:3000 (admin/admin)

3. **Add Prometheus Data Source:**
   - Go to Configuration → Data Sources
   - Add Prometheus
   - URL: http://prometheus:9090

4. **Import Dashboard:**
   - Create new dashboard or import community dashboard
   - FastAPI dashboard ID: 16110

5. **Custom Panels:**
   - Request rate: `rate(http_requests_total[5m])`
   - Error rate: `rate(errors_total[5m])`
   - Request duration (p95): `histogram_quantile(0.95, http_request_duration_seconds_bucket)`
   - Active connections: `database_connections_active`

---

## 🧪 Testing

### Test All Features

```bash
# 1. Metrics
curl http://localhost:8000/metrics

# 2. Health checks
curl http://localhost:8000/health
curl http://localhost:8000/health/detailed

# 3. Compression
curl -H "Accept-Encoding: gzip" http://localhost:8000/api/messages -I

# 4. Security headers
curl -I http://localhost:8000/

# 5. Sentry (check logs for initialization)
grep "Sentry initialized" logs/chat_system.log

# 6. Database monitoring (check logs after some queries)
grep "Slow database query" logs/chat_system.log

# 7. Performance indexes
python -m database.migrations.add_performance_indexes create
```

---

## 📈 Production Checklist

Before deploying to production:

- [ ] Configure SENTRY_DSN in environment
- [ ] Set slow query threshold appropriately
- [ ] Set up Prometheus scraping
- [ ] Configure Grafana dashboards
- [ ] Set up alerts for critical metrics
- [ ] Apply database indexes
- [ ] Test health check endpoints
- [ ] Verify compression is working
- [ ] Check security headers
- [ ] Monitor error rates in Sentry
- [ ] Review initial slow queries

---

## 🔍 Troubleshooting

### Metrics Not Showing

```bash
# Check if middleware is loaded
curl http://localhost:8000/metrics | head -20

# Should see metrics like:
# http_requests_total{...}
```

### Sentry Not Working

```bash
# Check logs for initialization
grep -i "sentry" logs/chat_system.log

# Verify DSN is set
echo $SENTRY_DSN
```

### Health Checks Failing

```bash
# Check detailed health
curl http://localhost:8000/health/detailed | jq '.'

# Look for component with "unhealthy" status
```

### Slow Queries Not Logged

```bash
# Check if monitoring is initialized
python -c "from database.performance_monitor import get_performance_monitor; print(get_performance_monitor())"

# Should print: <DatabasePerformanceMonitor object>
```

---

## 📚 Additional Resources

- [IMPLEMENTATION_STATUS.md](IMPLEMENTATION_STATUS.md) - Full implementation details
- [MONITORING.md](06-operations/MONITORING.md) - Monitoring guide
- [PERFORMANCE.md](06-operations/PERFORMANCE.md) - Performance optimization
- [SECURITY_ENHANCEMENTS.md](06-operations/SECURITY_ENHANCEMENTS.md) - Security guide

---

**Last Updated:** 2025-12-06  
**Need Help?** Check the troubleshooting section or open an issue
