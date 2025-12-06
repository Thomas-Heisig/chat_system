# Grafana Dashboards Configuration

## Overview

This document describes how to configure and use Grafana dashboards for monitoring the Chat System. All monitoring features have graceful fallback when Grafana is not available.

## Configuration

### Environment Variables

```bash
# Grafana Integration
GRAFANA_ENABLED=false  # Enable Grafana integration
GRAFANA_URL=http://localhost:3000  # Grafana server URL
GRAFANA_API_KEY=your-api-key-here  # API key for dashboard management
```

### Settings in Code

```python
from config.settings import monitoring_config

# Check if Grafana is enabled
if monitoring_config.grafana_enabled:
    # Grafana is available
    grafana_url = monitoring_config.grafana_url
    api_key = monitoring_config.grafana_api_key
```

## Fallback Behavior

When Grafana is disabled or unavailable:
- System continues to operate normally
- Metrics are still collected via Prometheus
- Dashboard operations return informative status messages
- No errors are raised - graceful degradation only

## Prometheus Integration

The system exports metrics compatible with Grafana:

```bash
# Prometheus metrics endpoint
http://localhost:8000/metrics
```

## Dashboard Templates

### 1. System Overview Dashboard

**Metrics:**
- HTTP request rate and latency
- Active WebSocket connections
- Database connection pool status
- Cache hit/miss rates
- Error rates

**Recommended Panels:**
```json
{
  "title": "HTTP Request Rate",
  "targets": [
    {
      "expr": "rate(http_requests_total[5m])"
    }
  ]
}
```

### 2. API Performance Dashboard

**Metrics:**
- Request duration by endpoint
- Request rate by method
- Error rate by status code
- Slow queries

**Key Queries:**
```promql
# Average response time by endpoint
avg(http_request_duration_seconds) by (path)

# Request rate by method
rate(http_requests_total[5m]) by (method)

# Error rate (5xx responses)
rate(http_requests_total{status=~"5.."}[5m])
```

### 3. Database Performance Dashboard

**Metrics:**
- Query execution time
- Connection pool utilization
- Slow queries count
- Database errors

**Key Queries:**
```promql
# Average query duration
avg(db_query_duration_seconds)

# Connection pool usage
db_connection_pool_active / db_connection_pool_size

# Slow queries per minute
rate(db_slow_queries_total[1m])
```

### 4. WebSocket Dashboard

**Metrics:**
- Active connections
- Message throughput
- Connection errors
- Average connection duration

### 5. AI/RAG Dashboard

**Metrics:**
- AI request rate
- Response generation time
- RAG query performance
- Cache effectiveness

## Setup Instructions

### 1. Install Grafana

```bash
# Using Docker
docker run -d \
  --name=grafana \
  -p 3000:3000 \
  -e "GF_SECURITY_ADMIN_PASSWORD=admin" \
  grafana/grafana-oss

# Or using docker-compose (add to docker-compose.yml):
services:
  grafana:
    image: grafana/grafana-oss:latest
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    volumes:
      - grafana-storage:/var/lib/grafana
```

### 2. Configure Prometheus Data Source

1. Open Grafana: http://localhost:3000
2. Login (admin/admin)
3. Go to Configuration > Data Sources
4. Add Prometheus data source
5. Set URL: http://localhost:8000/metrics (or Prometheus server URL)
6. Click "Save & Test"

### 3. Import Dashboards

#### Option A: Manual Import

1. Copy dashboard JSON from `grafana/dashboards/` directory
2. Go to Dashboards > Import
3. Paste JSON
4. Select Prometheus data source
5. Click Import

#### Option B: Automated Import

```python
from services.monitoring_service import GrafanaService

grafana = GrafanaService()
if grafana.is_available():
    # Import all dashboards
    result = await grafana.import_dashboards_from_dir("grafana/dashboards/")
```

### 4. Enable in Application

```bash
# Update .env file
GRAFANA_ENABLED=true
GRAFANA_URL=http://localhost:3000
GRAFANA_API_KEY=<your-api-key>

# Restart application
./restart.sh
```

## Dashboard Management

### Create Dashboard via API

```python
from services.monitoring_service import GrafanaService

grafana = GrafanaService()

dashboard_config = {
    "dashboard": {
        "title": "Custom Dashboard",
        "panels": [
            {
                "title": "Request Rate",
                "targets": [
                    {"expr": "rate(http_requests_total[5m])"}
                ]
            }
        ]
    }
}

result = await grafana.create_dashboard(dashboard_config)
```

### Update Dashboard

```python
result = await grafana.update_dashboard(dashboard_id, new_config)
```

### Delete Dashboard

```python
result = await grafana.delete_dashboard(dashboard_id)
```

## Alerting

### Configure Alerts in Grafana

1. Open dashboard panel
2. Click "Alert" tab
3. Configure alert condition:

```
WHEN avg() OF query(A, 5m, now) IS ABOVE 100
```

4. Set notification channels
5. Save alert

### Alert Examples

#### High Error Rate Alert

```
Alert Name: High Error Rate
Condition: rate(http_requests_total{status=~"5.."}[5m]) > 0.1
Notification: Slack, Email
```

#### Slow Database Queries

```
Alert Name: Slow Queries Detected
Condition: db_slow_queries_total > 10
Notification: PagerDuty
```

#### High Memory Usage

```
Alert Name: High Memory Usage
Condition: process_resident_memory_bytes > 1GB
Notification: Email
```

## Advanced Configuration

### Variables in Dashboards

Use variables for dynamic filtering:

```json
{
  "templating": {
    "list": [
      {
        "name": "instance",
        "type": "query",
        "query": "label_values(http_requests_total, instance)"
      }
    ]
  }
}
```

### Dashboard Annotations

Show deployment events:

```json
{
  "annotations": {
    "list": [
      {
        "name": "Deployments",
        "datasource": "Prometheus",
        "expr": "deployment_event"
      }
    ]
  }
}
```

## Troubleshooting

### Grafana Connection Failed

**Problem:** Cannot connect to Grafana

**Solution:**
1. Verify Grafana is running: `curl http://localhost:3000/api/health`
2. Check GRAFANA_URL in .env
3. Verify network connectivity
4. Check API key permissions

**Fallback:** System continues without Grafana, metrics still collected

### No Metrics in Dashboard

**Problem:** Dashboards show "No Data"

**Solution:**
1. Verify Prometheus is scraping metrics: http://localhost:8000/metrics
2. Check Prometheus data source configuration
3. Verify metric names in queries
4. Check time range selection

### API Key Errors

**Problem:** Authentication errors with Grafana API

**Solution:**
1. Generate new API key in Grafana: Configuration > API Keys
2. Ensure key has "Editor" or "Admin" role
3. Update GRAFANA_API_KEY in .env
4. Restart application

## Best Practices

1. **Start Simple:** Begin with system overview dashboard
2. **Focus on Key Metrics:** Don't overwhelm with too many panels
3. **Use Alerting:** Set up critical alerts early
4. **Regular Review:** Review dashboards weekly, update as needed
5. **Document Thresholds:** Document why alert thresholds are set
6. **Test Fallback:** Verify system works when Grafana is unavailable

## Maintenance

### Dashboard Backup

```bash
# Export all dashboards
curl -H "Authorization: Bearer $GRAFANA_API_KEY" \
  http://localhost:3000/api/search | \
  jq -r '.[] | .uid' | \
  while read uid; do
    curl -H "Authorization: Bearer $GRAFANA_API_KEY" \
      "http://localhost:3000/api/dashboards/uid/$uid" \
      > "backup_$uid.json"
  done
```

### Dashboard Updates

```bash
# Apply dashboard updates from git
python scripts/update_grafana_dashboards.py
```

## Related Documentation

- [Performance Monitoring](PERFORMANCE.md)
- [Prometheus Configuration](docs/MONITORING.md)
- [Alerting Guide](docs/ALERTING.md)

## Support

For issues with Grafana configuration:
1. Check logs: `docker logs grafana`
2. Review Grafana documentation: https://grafana.com/docs/
3. Check Prometheus metrics endpoint: `/metrics`

**Note:** All Grafana features are optional. The system operates fully when `GRAFANA_ENABLED=false`.
