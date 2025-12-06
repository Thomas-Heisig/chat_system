# Deployment Automation & CI/CD Configuration

## Overview

This document describes the deployment automation configuration for the Chat System, including CI/CD pipelines, container registry integration, and release automation. All features are optional and configurable.

## Configuration

### Environment Variables

```bash
# CI/CD Configuration
CI_CD_ENABLED=false  # Enable CI/CD automation
CONTAINER_REGISTRY=ghcr.io  # Container registry (ghcr.io, docker.io, gcr.io)
CONTAINER_REGISTRY_USER=your-username
CONTAINER_REGISTRY_TOKEN=your-token-or-pat

# Deployment Configuration
DEPLOYMENT_ENVIRONMENT=production  # development, staging, production
AUTO_DEPLOY_ENABLED=false  # Enable automatic deployments
DEPLOYMENT_APPROVAL_REQUIRED=true  # Require manual approval for production

# Release Automation
RELEASE_AUTOMATION_ENABLED=false
RELEASE_VERSION_STRATEGY=semver  # semver, calver, custom
```

### Settings in Code

```python
from config.settings import infrastructure_config

# Check CI/CD status
if infrastructure_config.ci_cd_enabled:
    registry = infrastructure_config.container_registry
    user = infrastructure_config.container_registry_user
```

## CI/CD Pipeline

### GitHub Actions Workflow

**File:** `.github/workflows/ci-cd.yml`

```yaml
name: CI/CD Pipeline

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]
  release:
    types: [ published ]

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}

jobs:
  # Build and Test
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
      
      - name: Run linters
        run: |
          flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
          black --check .
      
      - name: Run tests
        run: |
          pytest --cov=. --cov-report=xml
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          files: ./coverage.xml
  
  # Build Docker Image
  build-image:
    needs: build
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: write
    steps:
      - uses: actions/checkout@v3
      
      - name: Log in to Container Registry
        uses: docker/login-action@v2
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}
      
      - name: Extract metadata
        id: meta
        uses: docker/metadata-action@v4
        with:
          images: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}
          tags: |
            type=ref,event=branch
            type=ref,event=pr
            type=semver,pattern={{version}}
            type=semver,pattern={{major}}.{{minor}}
            type=sha
      
      - name: Build and push image
        uses: docker/build-push-action@v4
        with:
          context: .
          push: true
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
  
  # Deploy to Staging
  deploy-staging:
    needs: build-image
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/develop'
    environment:
      name: staging
      url: https://staging.chat-system.example.com
    steps:
      - name: Deploy to staging
        run: |
          echo "Deploying to staging..."
          # Add deployment commands here
  
  # Deploy to Production
  deploy-production:
    needs: build-image
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    environment:
      name: production
      url: https://chat-system.example.com
    steps:
      - name: Deploy to production
        run: |
          echo "Deploying to production..."
          # Add deployment commands here
```

### GitLab CI/CD

**File:** `.gitlab-ci.yml`

```yaml
stages:
  - test
  - build
  - deploy

variables:
  DOCKER_DRIVER: overlay2
  DOCKER_TLS_CERTDIR: "/certs"

# Test Stage
test:
  stage: test
  image: python:3.11
  before_script:
    - pip install -r requirements.txt
  script:
    - pytest --cov=. --cov-report=term
    - flake8 .
  coverage: '/TOTAL.+ ([0-9]{1,3}%)/'

# Build Docker Image
build:
  stage: build
  image: docker:latest
  services:
    - docker:dind
  script:
    - docker login -u $CI_REGISTRY_USER -p $CI_REGISTRY_PASSWORD $CI_REGISTRY
    - docker build -t $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA .
    - docker push $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA
  only:
    - main
    - develop

# Deploy to Staging
deploy_staging:
  stage: deploy
  script:
    - echo "Deploying to staging..."
    - kubectl set image deployment/chat-system chat-system=$CI_REGISTRY_IMAGE:$CI_COMMIT_SHA
  environment:
    name: staging
    url: https://staging.chat-system.example.com
  only:
    - develop

# Deploy to Production
deploy_production:
  stage: deploy
  script:
    - echo "Deploying to production..."
    - kubectl set image deployment/chat-system chat-system=$CI_REGISTRY_IMAGE:$CI_COMMIT_SHA
  environment:
    name: production
    url: https://chat-system.example.com
  when: manual
  only:
    - main
```

## Container Registry Integration

### GitHub Container Registry (GHCR)

**Setup:**
```bash
# Generate Personal Access Token (PAT)
# 1. Go to GitHub Settings > Developer settings > Personal access tokens
# 2. Create token with 'write:packages' scope
# 3. Save token securely

# Configuration
export CONTAINER_REGISTRY=ghcr.io
export CONTAINER_REGISTRY_USER=your-username
export CONTAINER_REGISTRY_TOKEN=your_pat_token

# Login
echo $CONTAINER_REGISTRY_TOKEN | docker login ghcr.io -u $CONTAINER_REGISTRY_USER --password-stdin
```

**Build and Push:**
```bash
# Build image
docker build -t ghcr.io/username/chat-system:latest .

# Push image
docker push ghcr.io/username/chat-system:latest

# Pull image
docker pull ghcr.io/username/chat-system:latest
```

### Docker Hub

**Setup:**
```bash
# Configuration
export CONTAINER_REGISTRY=docker.io
export CONTAINER_REGISTRY_USER=your-dockerhub-username
export CONTAINER_REGISTRY_TOKEN=your-access-token

# Login
docker login -u $CONTAINER_REGISTRY_USER -p $CONTAINER_REGISTRY_TOKEN
```

**Build and Push:**
```bash
docker build -t username/chat-system:latest .
docker push username/chat-system:latest
```

### Private Registry

**Setup:**
```bash
# Start private registry
docker run -d \
  -p 5000:5000 \
  --name registry \
  -v /mnt/registry:/var/lib/registry \
  registry:2

# Configuration
export CONTAINER_REGISTRY=localhost:5000
```

## Release Automation

### Semantic Versioning

**Configuration:**
```bash
RELEASE_AUTOMATION_ENABLED=true
RELEASE_VERSION_STRATEGY=semver
```

**Automated Versioning:**

```yaml
# .github/workflows/release.yml
name: Release

on:
  push:
    branches: [ main ]

jobs:
  release:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
        with:
          fetch-depth: 0
      
      - name: Semantic Release
        uses: cycjimmy/semantic-release-action@v3
        with:
          semantic_version: 19
          branches: |
            [
              'main',
              {name: 'develop', prerelease: true}
            ]
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

**Version Bump Script:**

```bash
#!/bin/bash
# scripts/bump_version.sh

CURRENT_VERSION=$(cat VERSION)
COMMIT_MSG=$(git log -1 --pretty=%B)

if [[ $COMMIT_MSG == *"BREAKING CHANGE"* ]]; then
  # Major version bump
  NEW_VERSION=$(echo $CURRENT_VERSION | awk -F. '{$1++; $2=0; $3=0} 1' OFS=.)
elif [[ $COMMIT_MSG == feat:* ]]; then
  # Minor version bump
  NEW_VERSION=$(echo $CURRENT_VERSION | awk -F. '{$2++; $3=0} 1' OFS=.)
else
  # Patch version bump
  NEW_VERSION=$(echo $CURRENT_VERSION | awk -F. '{$3++} 1' OFS=.)
fi

echo $NEW_VERSION > VERSION
git tag -a "v$NEW_VERSION" -m "Release $NEW_VERSION"
```

### Changelog Generation

**Automated with semantic-release:**

```json
// .releaserc.json
{
  "branches": ["main", "develop"],
  "plugins": [
    "@semantic-release/commit-analyzer",
    "@semantic-release/release-notes-generator",
    "@semantic-release/changelog",
    "@semantic-release/github",
    "@semantic-release/git"
  ]
}
```

**Manual with git-changelog:**

```bash
# Install
npm install -g conventional-changelog-cli

# Generate changelog
conventional-changelog -p angular -i CHANGELOG.md -s

# Commit
git add CHANGELOG.md
git commit -m "docs: update changelog"
```

## Deployment Strategies

### Blue-Green Deployment

```yaml
# k8s/deployment-blue-green.yml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: chat-system-blue
spec:
  replicas: 3
  selector:
    matchLabels:
      app: chat-system
      version: blue
  template:
    metadata:
      labels:
        app: chat-system
        version: blue
    spec:
      containers:
      - name: chat-system
        image: ghcr.io/username/chat-system:v1.0.0

---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: chat-system-green
spec:
  replicas: 3
  selector:
    matchLabels:
      app: chat-system
      version: green
  template:
    metadata:
      labels:
        app: chat-system
        version: green
    spec:
      containers:
      - name: chat-system
        image: ghcr.io/username/chat-system:v1.1.0
```

**Switch Traffic:**
```bash
# Switch to green
kubectl patch service chat-system -p '{"spec":{"selector":{"version":"green"}}}'

# Rollback to blue if needed
kubectl patch service chat-system -p '{"spec":{"selector":{"version":"blue"}}}'
```

### Canary Deployment

```yaml
# k8s/deployment-canary.yml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: chat-system-stable
spec:
  replicas: 9  # 90% of traffic
  selector:
    matchLabels:
      app: chat-system
      track: stable

---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: chat-system-canary
spec:
  replicas: 1  # 10% of traffic
  selector:
    matchLabels:
      app: chat-system
      track: canary
```

### Rolling Update

```bash
# Update image
kubectl set image deployment/chat-system \
  chat-system=ghcr.io/username/chat-system:v1.1.0

# Monitor rollout
kubectl rollout status deployment/chat-system

# Rollback if needed
kubectl rollout undo deployment/chat-system
```

## Fallback Behavior

When CI/CD is disabled:
- Manual deployment required
- Docker images can still be built locally
- No automatic versioning
- Manual changelog updates

## Best Practices

1. **Environment Parity:** Keep dev, staging, prod as similar as possible
2. **Automated Testing:** Run full test suite before deployment
3. **Gradual Rollout:** Use canary or blue-green deployments
4. **Monitoring:** Monitor metrics during and after deployment
5. **Rollback Plan:** Always have a quick rollback strategy
6. **Documentation:** Document deployment procedures
7. **Secrets Management:** Use secure secret storage (not in code)

## Troubleshooting

### Registry Authentication Failed

**Solutions:**
1. Verify token/password
2. Check token permissions
3. Re-login to registry
4. Check network connectivity

### Deployment Failed

**Solutions:**
1. Check deployment logs: `kubectl logs deployment/chat-system`
2. Verify image exists: `docker pull <image>`
3. Check resource limits
4. Verify configuration

### Version Conflict

**Solutions:**
1. Check current version: `cat VERSION`
2. Review git tags: `git tag -l`
3. Manually fix version if needed
4. Re-run release process

## Related Documentation

- [Kubernetes Deployment](k8s/README.md)
- [Docker Configuration](Dockerfile)
- [CI/CD Best Practices](docs/CI_CD_BEST_PRACTICES.md)

**Note:** All deployment automation is optional. Set `CI_CD_ENABLED=false` to use manual deployment processes.
