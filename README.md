# EventHub: SOFT8026 Assessment 2

A vertical slice of an event ticketing platform built as a microservice and event-driven system.

## Quick start

```powershell
docker compose up --build
```

Open `http://localhost:8080`. Click Book on any event. Watch the booking confirmation come back.

## On Kubernetes

```powershell
kubectl apply -f k8s/
kubectl get pods --watch
```

Open `http://localhost:30080` once all pods are Running.

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
