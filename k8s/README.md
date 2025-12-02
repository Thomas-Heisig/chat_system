# Kubernetes Deployment

Dieses Verzeichnis enthält Kubernetes-Manifests für das Deployment des Chat Systems.

## Deployment-Schritte

### 1. Namespace erstellen
```bash
kubectl apply -f manifests/namespace.yaml
```

### 2. Secrets erstellen
```bash
# WICHTIG: Nicht die secrets.yaml direkt anwenden!
# Stattdessen Secrets manuell erstellen:
kubectl create secret generic chat-system-secrets \
  --from-literal=APP_SECRET_KEY='your-secure-secret-key' \
  --from-literal=DATABASE_URL='postgresql://user:pass@postgres:5432/chat_system' \
  --from-literal=REDIS_URL='redis://redis:6379/0' \
  -n chat-system
```

### 3. ConfigMap erstellen
```bash
kubectl apply -f manifests/configmap.yaml
```

### 4. Datenbank und Redis deployen
```bash
kubectl apply -f manifests/database-deployment.yaml
kubectl apply -f manifests/redis-deployment.yaml
kubectl apply -f manifests/services.yaml
```

### 5. Application deployen
```bash
kubectl apply -f manifests/app-deployment.yaml
```

### 6. Ingress konfigurieren (optional)
```bash
# Domain in ingress.yaml anpassen!
kubectl apply -f manifests/ingress.yaml
```

## Überprüfen

```bash
# Pods anzeigen
kubectl get pods -n chat-system

# Logs anzeigen
kubectl logs -f deployment/chat-system-api -n chat-system

# Services anzeigen
kubectl get svc -n chat-system
```

## Scaling

```bash
# Horizontal skalieren
kubectl scale deployment chat-system-api --replicas=5 -n chat-system

# Autoscaling
kubectl autoscale deployment chat-system-api \
  --cpu-percent=70 \
  --min=2 \
  --max=10 \
  -n chat-system
```

## Troubleshooting

```bash
# Pod-Details
kubectl describe pod <pod-name> -n chat-system

# Events anzeigen
kubectl get events -n chat-system --sort-by='.lastTimestamp'

# Shell im Pod
kubectl exec -it deployment/chat-system-api -n chat-system -- /bin/bash
```
