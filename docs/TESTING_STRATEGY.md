# Testing Strategy & Configuration

## Overview

This document describes the testing strategy for the Chat System, including configuration for performance tests, security tests, and contract tests. All testing features are optional and configurable.

## Configuration

### Environment Variables

```bash
# Testing Configuration
PERFORMANCE_TESTS_ENABLED=false  # Enable performance testing
SECURITY_TESTS_ENABLED=false     # Enable security testing
CONTRACT_TESTS_ENABLED=false     # Enable contract testing

# Test Environment
TEST_DATABASE_URL=test_chat.db
TEST_LOG_LEVEL=WARNING
TEST_TIMEOUT=30
```

## Performance Testing

### Configuration

```bash
# Enable performance tests
PERFORMANCE_TESTS_ENABLED=true

# Optional: Configure load testing tool
LOAD_TESTING_TOOL=locust  # locust, k6, artillery
LOAD_TEST_DURATION=300     # 5 minutes
LOAD_TEST_USERS=100        # Concurrent users
LOAD_TEST_SPAWN_RATE=10    # Users per second
```

### Setup with Locust

**Installation:**
```bash
pip install locust
```

**Configuration File:** `tests/performance/locustfile.py`

```python
from locust import HttpUser, task, between

class ChatUser(HttpUser):
    """Simulated chat user for load testing"""
    
    wait_time = between(1, 3)
    
    def on_start(self):
        """Login or setup before testing"""
        self.client.post("/api/auth/login", json={
            "username": "testuser",
            "password": "testpass"
        })
    
    @task(3)
    def send_message(self):
        """Send chat message (most common action)"""
        self.client.post("/api/messages", json={
            "content": "Test message",
            "room_id": "general"
        })
    
    @task(1)
    def get_messages(self):
        """Retrieve messages"""
        self.client.get("/api/messages?limit=50")
    
    @task(1)
    def get_users(self):
        """Get online users"""
        self.client.get("/api/users/online")
```

**Running Tests:**
```bash
# Start load test
locust -f tests/performance/locustfile.py \
  --host http://localhost:8000 \
  --users 100 \
  --spawn-rate 10 \
  --run-time 5m

# Web UI
locust -f tests/performance/locustfile.py
# Open http://localhost:8089
```

### Setup with k6

**Installation:**
```bash
# macOS
brew install k6

# Linux
sudo apt-get install k6
```

**Configuration File:** `tests/performance/k6_script.js`

```javascript
import http from 'k6/http';
import { check, sleep } from 'k6';

export let options = {
  stages: [
    { duration: '2m', target: 100 }, // Ramp up to 100 users
    { duration: '5m', target: 100 }, // Stay at 100 users
    { duration: '2m', target: 0 },   // Ramp down to 0 users
  ],
  thresholds: {
    http_req_duration: ['p(95)<500'], // 95% of requests < 500ms
    http_req_failed: ['rate<0.01'],   // < 1% errors
  },
};

export default function () {
  // Send message
  let response = http.post('http://localhost:8000/api/messages', 
    JSON.stringify({
      content: 'Test message',
      room_id: 'general'
    }),
    { headers: { 'Content-Type': 'application/json' } }
  );
  
  check(response, {
    'status is 200': (r) => r.status === 200,
    'response time < 500ms': (r) => r.timings.duration < 500,
  });
  
  sleep(1);
}
```

**Running Tests:**
```bash
k6 run tests/performance/k6_script.js
```

### Performance Metrics

Monitor these metrics during load testing:

1. **Response Time:**
   - p50 (median): < 100ms
   - p95: < 500ms
   - p99: < 1000ms

2. **Throughput:**
   - Target: 1000 requests/second
   - Success rate: > 99%

3. **Resource Usage:**
   - CPU: < 80%
   - Memory: < 2GB
   - Database connections: < 80% pool

4. **Error Rates:**
   - HTTP 5xx: < 0.1%
   - Timeouts: < 0.5%

### Fallback Behavior

When `PERFORMANCE_TESTS_ENABLED=false`:
- Performance tests are skipped
- No additional dependencies required
- Regular unit/integration tests run normally

## Security Testing

### Configuration

```bash
# Enable security tests
SECURITY_TESTS_ENABLED=true

# Optional: Configure security scanning
SECURITY_SCAN_TOOL=zap  # zap, bandit, safety
SECURITY_SCAN_DEPTH=medium  # low, medium, high
```

### Setup with OWASP ZAP

**Installation:**
```bash
# Using Docker
docker pull owasp/zap2docker-stable

# Or download from: https://www.zaproxy.org/download/
```

**Running Security Scan:**
```bash
# Baseline scan (quick)
docker run -t owasp/zap2docker-stable \
  zap-baseline.py \
  -t http://localhost:8000 \
  -r security_report.html

# Full scan (thorough)
docker run -t owasp/zap2docker-stable \
  zap-full-scan.py \
  -t http://localhost:8000 \
  -r security_report.html
```

**Automated CI Integration:**
```yaml
# .github/workflows/security-tests.yml
name: Security Tests

on: [push, pull_request]

jobs:
  security-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Start application
        run: |
          docker-compose up -d
          sleep 10
      
      - name: Run ZAP scan
        run: |
          docker run -t owasp/zap2docker-stable \
            zap-baseline.py \
            -t http://localhost:8000 \
            -r security_report.html
      
      - name: Upload report
        uses: actions/upload-artifact@v2
        with:
          name: security-report
          path: security_report.html
```

### Python Security Scanning

**Bandit (Static Analysis):**
```bash
# Install
pip install bandit

# Run scan
bandit -r . -f json -o bandit_report.json

# Exclude test files
bandit -r . -x tests/ -f json -o bandit_report.json
```

**Safety (Dependency Scanning):**
```bash
# Install
pip install safety

# Check dependencies
safety check --json

# Check requirements file
safety check -r requirements.txt
```

### Security Test Checklist

- [ ] SQL Injection prevention
- [ ] XSS (Cross-Site Scripting) prevention
- [ ] CSRF (Cross-Site Request Forgery) protection
- [ ] Authentication bypass attempts
- [ ] Authorization checks
- [ ] Sensitive data exposure
- [ ] Rate limiting effectiveness
- [ ] Session management
- [ ] Input validation
- [ ] Dependency vulnerabilities

### Fallback Behavior

When `SECURITY_TESTS_ENABLED=false`:
- Security tests are skipped
- Manual security review recommended
- CodeQL still runs (if configured in CI)

## Contract Testing

### Configuration

```bash
# Enable contract tests
CONTRACT_TESTS_ENABLED=true

# Optional: Configure contract testing tool
CONTRACT_TEST_TOOL=pact  # pact, spring-cloud-contract
CONTRACT_BROKER_URL=http://localhost:9292
```

### Setup with Pact

**Installation:**
```bash
pip install pact-python
```

**Consumer Test Example:**

```python
# tests/contract/test_message_api_consumer.py
import pytest
from pact import Consumer, Provider

pact = Consumer('ChatClient').has_pact_with(
    Provider('ChatAPI'),
    pact_dir='./pacts'
)

def test_get_messages():
    """Test contract for getting messages"""
    expected_response = {
        "messages": [
            {
                "id": 1,
                "content": "Hello",
                "username": "user1",
                "timestamp": "2024-01-01T00:00:00Z"
            }
        ]
    }
    
    pact.given('messages exist').upon_receiving(
        'a request for messages'
    ).with_request(
        method='GET',
        path='/api/messages'
    ).will_respond_with(
        status=200,
        body=expected_response
    )
    
    with pact:
        # Make actual request
        response = requests.get(f'{pact.uri}/api/messages')
        assert response.json() == expected_response
```

**Provider Verification:**

```python
# tests/contract/test_message_api_provider.py
from pact import Verifier

def test_provider_contract():
    """Verify provider meets consumer contracts"""
    verifier = Verifier(
        provider='ChatAPI',
        provider_base_url='http://localhost:8000'
    )
    
    # Setup provider state
    verifier.set_state('messages exist', setup=seed_messages)
    
    # Verify contracts
    output, logs = verifier.verify_pacts('./pacts/*.json')
    assert output == 0
```

### Contract Testing Best Practices

1. **Define Clear Contracts:** Document expected API behavior
2. **Version Contracts:** Track changes over time
3. **CI Integration:** Run on every PR
4. **Share Contracts:** Use Pact Broker for team collaboration
5. **Keep Updated:** Update contracts when API changes

### Fallback Behavior

When `CONTRACT_TESTS_ENABLED=false`:
- Contract tests are skipped
- API documentation still generated
- Integration tests still run

## Test Execution Strategy

### Local Development

```bash
# Run all tests
pytest

# Run specific test types
pytest tests/unit/           # Unit tests only
pytest tests/integration/    # Integration tests only
pytest tests/performance/    # Performance tests (if enabled)

# Run with coverage
pytest --cov=. --cov-report=html
```

### CI/CD Pipeline

```yaml
# .github/workflows/tests.yml
name: Tests

on: [push, pull_request]

jobs:
  unit-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Run unit tests
        run: pytest tests/unit/
  
  integration-tests:
    runs-on: ubuntu-latest
    needs: unit-tests
    steps:
      - uses: actions/checkout@v2
      - name: Start services
        run: docker-compose up -d
      - name: Run integration tests
        run: pytest tests/integration/
  
  performance-tests:
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    needs: integration-tests
    steps:
      - uses: actions/checkout@v2
      - name: Run performance tests
        run: |
          export PERFORMANCE_TESTS_ENABLED=true
          locust -f tests/performance/locustfile.py --headless
```

## Reporting

### Test Coverage Reports

```bash
# Generate coverage report
pytest --cov=. --cov-report=html

# View report
open htmlcov/index.html
```

### Performance Test Reports

Locust generates HTML reports automatically.
Access at: http://localhost:8089

### Security Test Reports

ZAP generates HTML/JSON reports.
View with: `open security_report.html`

## Related Documentation

- [Testing Guide](TESTING_GUIDE.md)
- [Performance Monitoring](PERFORMANCE.md)
- [Security Enhancements](SECURITY_ENHANCEMENTS.md)

## Support

For testing issues:
1. Check test logs
2. Verify configuration in .env
3. Review test framework documentation
4. Ensure dependencies are installed

**Note:** All testing features are optional and configurable. The system runs normally with all tests disabled.
