# CI/CD Setup and Implementation Guide

**Version:** 2.0.0  
**Last Updated:** 2025-12-06  
**Status:** Implemented ✅

## 📋 Table of Contents

- [Overview](#overview)
- [GitHub Actions Workflows](#github-actions-workflows)
- [Pre-commit Hooks](#pre-commit-hooks)
- [Testing Pipeline](#testing-pipeline)
- [Deployment Pipeline](#deployment-pipeline)
- [Monitoring and Alerts](#monitoring-and-alerts)
- [Best Practices](#best-practices)

## Overview

The Universal Chat System uses a comprehensive CI/CD pipeline to ensure code quality, automated testing, and reliable deployments. This guide covers the complete CI/CD setup including GitHub Actions workflows, pre-commit hooks, and deployment strategies.

### CI/CD Architecture

```
┌─────────────────┐
│   Developer     │
│  Local Changes  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Pre-commit     │ ← Lint, Format, Type Check
│     Hooks       │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   Git Push      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ GitHub Actions  │ ← CI Workflow
│   CI Pipeline   │
└────────┬────────┘
         │
         ├─── Lint & Format Check
         ├─── Type Checking (mypy)
         ├─── Security Scan
         ├─── Unit Tests
         ├─── Integration Tests
         ├─── Coverage Report
         │
         ▼
┌─────────────────┐
│   PR Review     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Merge to Main  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  CD Pipeline    │ ← Deploy
└────────┬────────┘
         │
         ├─── Build Docker Image
         ├─── Push to Registry
         ├─── Deploy to Staging
         ├─── Run E2E Tests
         ├─── Deploy to Production
         │
         ▼
┌─────────────────┐
│   Monitoring    │ ← Health Checks
└─────────────────┘
```

## GitHub Actions Workflows

### 1. Main CI Workflow

Location: `.github/workflows/ci.yml`

This is the primary CI workflow that runs on every push and pull request.

```yaml
name: CI

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main, develop ]

jobs:
  lint:
    name: Lint and Format Check
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.9'
      
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install black flake8 isort
      
      - name: Check formatting with black
        run: black --check --line-length 100 .
      
      - name: Check import sorting with isort
        run: isort --check-only --profile black .
      
      - name: Lint with flake8
        run: |
          flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
          flake8 . --count --max-complexity=10 --max-line-length=100 --statistics

  type-check:
    name: Type Checking
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.9'
      
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install mypy types-requests
          pip install -r requirements.txt
      
      - name: Type check with mypy
        run: mypy --ignore-missing-imports --no-strict-optional .

  security:
    name: Security Scan
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.9'
      
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install bandit safety
      
      - name: Security check with bandit
        run: bandit -r . -f json -o bandit-report.json || true
      
      - name: Check dependencies with safety
        run: safety check --json || true
      
      - name: Upload security reports
        uses: actions/upload-artifact@v3
        with:
          name: security-reports
          path: |
            bandit-report.json

  test:
    name: Tests
    runs-on: ubuntu-latest
    
    strategy:
      matrix:
        python-version: ['3.9', '3.10', '3.11']
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python ${{ matrix.python-version }}
        uses: actions/setup-python@v4
        with:
          python-version: ${{ matrix.python-version }}
      
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          pip install pytest pytest-cov pytest-asyncio
      
      - name: Run tests with coverage
        run: |
          pytest --cov=. --cov-report=xml --cov-report=html --cov-report=term
      
      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml
          flags: unittests
          name: codecov-umbrella
      
      - name: Upload coverage reports
        uses: actions/upload-artifact@v3
        with:
          name: coverage-reports
          path: htmlcov/

  build:
    name: Build Docker Image
    runs-on: ubuntu-latest
    needs: [lint, type-check, security, test]
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v2
      
      - name: Build Docker image
        run: docker build -t chat-system:${{ github.sha }} .
      
      - name: Test Docker image
        run: |
          docker run -d --name test-container -p 8000:8000 chat-system:${{ github.sha }}
          sleep 10
          curl -f http://localhost:8000/health || exit 1
          docker stop test-container
```

### 2. Deployment Workflow

Location: `.github/workflows/deploy.yml`

```yaml
name: Deploy

on:
  push:
    branches: [ main ]
    tags:
      - 'v*'

jobs:
  deploy-staging:
    name: Deploy to Staging
    runs-on: ubuntu-latest
    environment: staging
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v2
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: us-east-1
      
      - name: Login to Amazon ECR
        id: login-ecr
        uses: aws-actions/amazon-ecr-login@v1
      
      - name: Build and push Docker image
        env:
          ECR_REGISTRY: ${{ steps.login-ecr.outputs.registry }}
          ECR_REPOSITORY: chat-system
          IMAGE_TAG: ${{ github.sha }}
        run: |
          docker build -t $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG .
          docker push $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG
      
      - name: Deploy to ECS
        run: |
          aws ecs update-service \
            --cluster chat-system-staging \
            --service chat-system \
            --force-new-deployment
      
      - name: Wait for deployment
        run: |
          aws ecs wait services-stable \
            --cluster chat-system-staging \
            --services chat-system
      
      - name: Run smoke tests
        run: |
          curl -f https://staging.chat-system.com/health
          curl -f https://staging.chat-system.com/api/v1/health

  deploy-production:
    name: Deploy to Production
    runs-on: ubuntu-latest
    needs: deploy-staging
    environment: production
    if: startsWith(github.ref, 'refs/tags/v')
    
    steps:
      - uses: actions/checkout@v3
      
      # Similar steps as staging
      # ... (deployment steps)
      
      - name: Create GitHub Release
        uses: actions/create-release@v1
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        with:
          tag_name: ${{ github.ref }}
          release_name: Release ${{ github.ref }}
          draft: false
          prerelease: false
```

### 3. Dependency Update Workflow

Location: `.github/workflows/dependencies.yml`

```yaml
name: Update Dependencies

on:
  schedule:
    - cron: '0 0 * * 1'  # Every Monday at midnight
  workflow_dispatch:

jobs:
  update:
    name: Update Dependencies
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.9'
      
      - name: Install pip-tools
        run: pip install pip-tools
      
      - name: Update requirements
        run: |
          pip-compile --upgrade requirements.in
      
      - name: Create Pull Request
        uses: peter-evans/create-pull-request@v5
        with:
          token: ${{ secrets.GITHUB_TOKEN }}
          commit-message: 'chore: update dependencies'
          title: 'Update Python dependencies'
          body: |
            Automated dependency update
            
            - Review changes carefully
            - Ensure all tests pass
            - Check for breaking changes
          branch: dependency-updates
```

## Pre-commit Hooks

### Setup

Install pre-commit hooks to run checks before each commit:

```bash
# Install pre-commit
pip install pre-commit

# Install hooks
pre-commit install

# Run manually on all files
pre-commit run --all-files
```

### Configuration

Location: `.pre-commit-config.yaml`

```yaml
repos:
  # Code formatting
  - repo: https://github.com/psf/black
    rev: 23.11.0
    hooks:
      - id: black
        language_version: python3.9
        args: ['--line-length=100']

  # Import sorting
  - repo: https://github.com/PyCQA/isort
    rev: 5.12.0
    hooks:
      - id: isort
        args: ['--profile=black']

  # Linting
  - repo: https://github.com/PyCQA/flake8
    rev: 6.1.0
    hooks:
      - id: flake8
        args: ['--max-line-length=100', '--extend-ignore=E203,W503']

  # Type checking
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.7.0
    hooks:
      - id: mypy
        additional_dependencies: [types-requests]
        args: ['--ignore-missing-imports', '--no-strict-optional']

  # Security
  - repo: https://github.com/PyCQA/bandit
    rev: 1.7.5
    hooks:
      - id: bandit
        args: ['-c', 'pyproject.toml']

  # General checks
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
        args: ['--maxkb=1000']
      - id: check-merge-conflict
      - id: detect-private-key

  # Commit message linting
  - repo: https://github.com/commitizen-tools/commitizen
    rev: 3.12.0
    hooks:
      - id: commitizen
      - id: commitizen-branch
        stages: [push]
```

## Testing Pipeline

### Test Organization

```
tests/
├── unit/              # Unit tests
│   ├── test_auth.py
│   ├── test_models.py
│   └── test_services.py
├── integration/       # Integration tests
│   ├── test_api.py
│   ├── test_database.py
│   └── test_websocket.py
├── e2e/              # End-to-end tests
│   ├── test_chat_flow.py
│   └── test_rag_flow.py
└── conftest.py       # Pytest configuration
```

### pytest Configuration

Location: `pytest.ini`

```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
asyncio_mode = auto

# Coverage options
addopts =
    --verbose
    --strict-markers
    --cov=.
    --cov-report=term-missing
    --cov-report=html
    --cov-report=xml
    --cov-fail-under=75

markers =
    unit: Unit tests
    integration: Integration tests
    e2e: End-to-end tests
    slow: Slow tests
```

### Running Tests

```bash
# Run all tests
pytest

# Run specific test types
pytest -m unit
pytest -m integration
pytest -m e2e

# Run with coverage
pytest --cov=. --cov-report=html

# Run in parallel
pytest -n auto

# Run specific test file
pytest tests/unit/test_auth.py

# Run specific test
pytest tests/unit/test_auth.py::test_login

# Run with verbose output
pytest -vv

# Run and stop on first failure
pytest -x

# Run and show local variables on failure
pytest -l
```

## Deployment Pipeline

### Deployment Environments

1. **Development** (`develop` branch)
   - Automatic deployment on push
   - Internal testing environment
   - No manual approval required

2. **Staging** (`main` branch)
   - Automatic deployment on merge to main
   - Pre-production testing
   - Smoke tests run automatically
   - Manual approval for production

3. **Production** (version tags)
   - Manual trigger or tag creation
   - Requires approval
   - Blue-green deployment
   - Automatic rollback on failure

### Deployment Strategy

```yaml
# Blue-Green Deployment
deployment:
  type: blue-green
  
  blue:
    - Deploy to blue environment
    - Run health checks
    - Run smoke tests
  
  green:
    - Switch traffic to blue
    - Monitor for 10 minutes
    - Rollback if errors > threshold
  
  cleanup:
    - Keep green as fallback
    - Remove after 24 hours
```

### Rollback Procedure

```bash
# Automatic rollback on failure
if [ $ERROR_RATE > $THRESHOLD ]; then
    aws ecs update-service \
        --cluster chat-system-prod \
        --service chat-system \
        --task-definition chat-system:previous
fi

# Manual rollback
./scripts/rollback.sh --version v1.0.0
```

## Monitoring and Alerts

### Health Checks

```yaml
health_checks:
  - endpoint: /health
    interval: 30s
    timeout: 10s
    healthy_threshold: 3
    unhealthy_threshold: 2
  
  - endpoint: /api/v1/health
    interval: 60s
    timeout: 15s
```

### Alerts

```yaml
alerts:
  - name: High Error Rate
    condition: error_rate > 5%
    duration: 5m
    severity: critical
    notify: [slack, email, pagerduty]
  
  - name: High Latency
    condition: p99_latency > 1000ms
    duration: 10m
    severity: warning
    notify: [slack]
  
  - name: Low Test Coverage
    condition: coverage < 75%
    severity: warning
    notify: [slack]
```

## Best Practices

### 1. Commit Guidelines

Follow conventional commits:

```bash
# Format: <type>(<scope>): <subject>

# Examples:
feat(auth): add OAuth2 support
fix(api): handle null pointer in user endpoint
docs(readme): update installation instructions
test(integration): add websocket tests
chore(deps): update dependencies
```

### 2. Branch Strategy

```
main (production)
  └── develop (staging)
       ├── feature/new-feature
       ├── bugfix/fix-issue
       └── hotfix/critical-fix
```

### 3. Code Review Checklist

- [ ] All tests pass
- [ ] Code coverage meets threshold (75%)
- [ ] No security vulnerabilities
- [ ] Documentation updated
- [ ] Breaking changes documented
- [ ] Performance impact considered

### 4. Release Process

1. Create release branch from `main`
2. Update version numbers
3. Update CHANGELOG.md
4. Create pull request
5. After approval, merge to `main`
6. Create version tag
7. Automated deployment triggered

### 5. Security Best Practices

- All secrets stored in GitHub Secrets
- No credentials in code or logs
- Regular dependency updates
- Security scans on every PR
- Vulnerability reports reviewed weekly

## Troubleshooting

### CI Build Failures

**Problem**: Tests fail in CI but pass locally

**Solution**:
```bash
# Run tests with same Python version as CI
docker run -it python:3.9 bash
pip install -r requirements.txt
pytest
```

### Deployment Failures

**Problem**: Deployment times out

**Solution**:
```bash
# Check service status
aws ecs describe-services \
    --cluster chat-system-prod \
    --services chat-system

# Check logs
aws logs tail /ecs/chat-system --follow
```

### Pre-commit Hook Issues

**Problem**: Pre-commit hooks too slow

**Solution**:
```bash
# Skip hooks for quick commits (use sparingly)
git commit --no-verify -m "message"

# Run specific hook
pre-commit run black --all-files
```

## Maintenance

### Weekly Tasks
- [ ] Review failed builds
- [ ] Check coverage trends
- [ ] Review security alerts
- [ ] Update dependencies

### Monthly Tasks
- [ ] Review and optimize workflows
- [ ] Clean up old artifacts
- [ ] Update documentation
- [ ] Review access permissions

## Additional Resources

- **GitHub Actions Documentation**: https://docs.github.com/en/actions
- **Pre-commit Documentation**: https://pre-commit.com/
- **pytest Documentation**: https://docs.pytest.org/
- **Docker Documentation**: https://docs.docker.com/

## Support

Having issues with CI/CD?

- Check workflow logs in GitHub Actions tab
- Review [CONTRIBUTING.md](CONTRIBUTING.md)
- Open an issue with `ci/cd` label
- Ask in [GitHub Discussions](https://github.com/Thomas-Heisig/chat_system/discussions)

---

**Last Updated**: 2025-12-06  
**Maintained By**: DevOps Team  
**Status**: Active ✅
