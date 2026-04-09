# Agnos DevOps Assignment

Production-ready DevOps setup with FastAPI, Docker, Kubernetes, GitHub Actions CI/CD, and Prometheus/Grafana monitoring.

---

## Architecture Overview

```
┌─────────────────────────────────────────────┐
│              GitHub Actions CI/CD            │
│  Lint → Test → Build → Scan → Deploy        │
└────────────────────┬────────────────────────┘
                     │
┌────────────────────▼────────────────────────┐
│           Kubernetes Cluster (minikube)      │
│                                             │
│  ┌─────────────────┐  ┌──────────────────┐  │
│  │   API Service   │  │  Worker Service  │  │
│  │  (2 replicas)   │  │  (1 replica)     │  │
│  │  FastAPI + HPA  │  │  APScheduler     │  │
│  └────────┬────────┘  └──────────────────┘  │
│           │                                 │
│  ┌────────▼────────────────────────────┐    │
│  │        Prometheus + Grafana         │    │
│  │   Scrapes /metrics every 15s        │    │
│  └─────────────────────────────────────┘    │
└─────────────────────────────────────────────┘
```

**Components:**
- **API Service** — FastAPI app exposing `GET /health` and `/metrics`. Runs with 2 replicas for HA, scales to 5 via HPA.
- **Worker Service** — Python background job that updates timestamps on today's records every 60 seconds.
- **ConfigMaps** — Separate configuration for DEV, UAT, PROD environments. Same image, different config.
- **Prometheus** — Scrapes `/metrics` from the API every 15 seconds.
- **Grafana** — Visualizes request rate, latency, error rate.

---

## Setup Instructions

### Prerequisites
- Docker Desktop
- minikube
- kubectl
- helm

### 1. Start minikube
```bash
minikube start --driver=docker
eval $(minikube docker-env)
```

### 2. Build images inside minikube
```bash
docker build -t agnos-api:latest ./api
docker build -t agnos-worker:latest ./worker
```

### 3. Create namespaces and deploy
```bash
kubectl create namespace dev
kubectl apply -f k8s/envs/dev/configmap.yaml
kubectl apply -f k8s/base/ -n dev
```

### 4. Enable metrics server (for HPA)
```bash
minikube addons enable metrics-server
```

### 5. Install monitoring stack
```bash
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update
helm install monitoring prometheus-community/kube-prometheus-stack \
  --namespace monitoring --create-namespace \
  --set grafana.adminPassword=admin123 \
  --set prometheus.prometheusSpec.serviceMonitorSelectorNilUsesHelmValues=false
```

---

## Usage Instructions

### Test the API
```bash
kubectl port-forward svc/agnos-api-service 8080:80 -n dev
curl http://localhost:8080/health
```

### View worker logs
```bash
kubectl logs -l app=agnos-worker -n dev -f
```

### Access Grafana
```bash
kubectl port-forward svc/monitoring-grafana 3000:80 -n monitoring
# Open http://localhost:3000 — admin / admin123
```

### Switch environments
```bash
# Apply UAT config and deploy to UAT namespace
kubectl create namespace uat
kubectl apply -f k8s/envs/uat/configmap.yaml
kubectl apply -f k8s/base/ -n uat
```

---

## Failure Scenario Handling

### a. API crashes during peak hours
The API runs with **2 minimum replicas** enforced by HPA. If one pod crashes, the Service automatically stops routing traffic to it (readiness probe fails) and routes all traffic to the healthy pod. Kubernetes restarts the crashed pod automatically. HPA scales up additional pods if CPU load is high. **Zero downtime.**

### b. Worker fails and infinitely retries
The worker Deployment has `restartPolicy: Always` (Kubernetes default). If the worker crashes, K8s restarts it. To prevent infinite crash loops from hammering resources, Kubernetes applies **exponential backoff** — it waits 10s, 20s, 40s, etc. between restarts (visible as `CrashLoopBackOff` status). Fix: check logs with `kubectl logs -l app=agnos-worker -n dev`, identify the error, push a fix through the CI/CD pipeline.

### c. Bad deployment is released
Roll back immediately using:
```bash
kubectl rollout undo deployment/agnos-api -n dev
kubectl rollout undo deployment/agnos-worker -n dev
```
Kubernetes keeps the previous ReplicaSet. The rollout is instantaneous. In CI/CD, this is prevented by the lint, test, and security scan stages — a bad build never reaches deploy.

### d. Kubernetes node goes down
In a multi-node cluster, pods are rescheduled to healthy nodes automatically. In our minikube setup (single node), this would cause downtime — acceptable for local dev. In production (EKS/GKE), you'd run **3+ nodes across availability zones** so no single node failure takes down the cluster.

---

## CI/CD Pipeline

Triggered on every push to `main`, `dev`, or `uat` branches.

| Stage | What it does |
|---|---|
| Lint & Test | flake8 code style check + pytest unit tests |
| Build | Builds Docker images tagged with git SHA |
| Security Scan | Trivy scans for HIGH/CRITICAL CVEs |
| Deploy | Applies K8s manifests (mocked for local) |

---

## Monitoring

| Metric | Source |
|---|---|
| Request rate | `http_requests_total` |
| Request latency | `http_request_duration_seconds` |
| Error rate | `http_requests_total{status="5xx"}` |
| Pod CPU/Memory | kube-state-metrics (auto-collected) |

Alerts configured for: high error rate, pod crash looping, stalled worker.