# EventHub: SOFT8026 Assessment 2

A vertical slice of an event ticketing platform built as a microservice and event-driven system.

## Quick start

```powershell
docker compose up --build
```

Open `http://localhost:8080`. Click Book on any event. Watch the booking confirmation come back.

## On Kubernetes

Build images locally first (same tags the cluster expects), then apply:

```powershell
docker compose build
kubectl apply -k k8s/
kubectl get pods --watch
```

Images use `imagePullPolicy: Never` so the Kubernetes node must already have `eventhub-main-*` images (Docker Desktop’s cluster shares the local daemon). Open `http://localhost:30080` once all pods are Running (web-frontend NodePort).

Init containers use **`redis:7-alpine`** (same tag as the Redis Deployment) instead of `busybox`, because Docker Desktop often shows **`Init:ImagePullBackOff`** on extra Hub pulls while `redis` / `rabbitmq` images already loaded on the node work reliably.

## Run tests

```powershell
pytest -m unit
pytest
```

## Repo guide

- `CLAUDE.md` — context for Claude Code, including a critical rule about which service is hand-written
- `ARCHITECTURE.md` — system design, events, scaling decisions
- `PLAN.md` — day-by-day plan to the deadline
- `GENAI_LOG.md` — prompt log for the submission

## Submission

Due 8pm Monday 11 May 2026. Zip contains source code, a 4 to 6 page document, and a 4 to 6 minute video.
