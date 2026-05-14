# EventHub

Event-driven ticketing (Flask UI, booking API, Redis, RabbitMQ, workers). **Written submission:** `docs/EventHub_Submission_Document.docx`.

## Run locally

```powershell
docker compose up --build
```

UI: http://localhost:8080 — Booking API: http://localhost:5000

## Kubernetes

```powershell
docker compose build
kubectl apply -k k8s/
```

UI when ready: http://localhost:30080 (NodePort). Manifests use `imagePullPolicy: Never` — images must exist in the cluster’s store (e.g. build with Compose on Docker Desktop **kubeadm** node, or enable the **containerd image store** if the node is **kind** / `desktop-control-plane`). Optional: `powershell -File scripts/k8s-apply-and-check.ps1`

## Tests

```powershell
pip install -r requirements-dev.txt
pytest -m unit
pytest
```

Booking unit tests: `services/booking-service/booking_service_tests/` (separate from top-level `tests/` so pytest does not confuse package names).
