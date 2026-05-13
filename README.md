# EventHub: SOFT8026 Assessment 2

A vertical slice of an event ticketing platform built as a microservice and event-driven system.

**Submission:** branch `submission` tracks the hand-in bundle (including `docs/EventHub_Submission_Document.docx` and a Compose tweak: no `wait-for-it` bind-mount on web-frontend). Continue development on `main` unless you merge.

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

Or one script that builds, applies, runs the booking image check, and lists pods:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/k8s-apply-and-check.ps1
```

Images use `imagePullPolicy: Never`, so the kubelet must already have `eventhub-main-*` in **the same image store Kubernetes uses** (not only in `docker images` on the host).

Open `http://localhost:30080` once all pods are Running (web-frontend NodePort).

### Verify Kubernetes is healthy

```powershell
kubectl config current-context          # expect: docker-desktop
kubectl get nodes                       # expect: Ready
kubectl get pods                        # expect: all Running, READY matches replicas
kubectl get svc web-frontend            # expect: NodePort 30080 -> 8080
kubectl rollout status deployment/booking-service
curl.exe -s http://localhost:30080/healthz
curl.exe -s http://localhost:5000/healthz   # only if booking-service port-forward or Compose
```

To **smoke-test the UI on the cluster**, use the NodePort URL above. To **trace one booking**, pick a pod and stream logs (replace the pod name from `kubectl get pods`):

```powershell
kubectl logs -f deployment/booking-service --tail=50
```

Init containers use **`redis:7-alpine`** (same tag as the Redis Deployment) instead of `busybox`, because Docker Desktop often shows **`Init:ImagePullBackOff`** on extra Hub pulls while `redis` / `rabbitmq` images already loaded on the node work reliably.

### If pods show `ErrImageNeverPull` for `eventhub-main-*`

Run `kubectl get nodes`. If the node name looks like **`desktop-control-plane`**, Docker Desktop is using the **kind** provisioner. Per Docker’s docs, **kind only works with the containerd image store**, not the classic Docker Engine store—so `docker compose build` can succeed while Kubernetes still reports the image as missing.

Pick **one** of these fixes, then run `docker compose build` again and `kubectl apply -k k8s/`:

1. **Enable the containerd image store** (recommended): Docker Desktop → **Settings** → **General** → turn on **Use containerd for pulling and storing images** → **Apply & restart** → rebuild images. That aligns `docker build` / Compose with what the cluster can run.
2. **Or switch the cluster** to **kubeadm** (Docker Desktop → **Kubernetes** → edit cluster / provisioner). Kubeadm mode is documented as compatible with the **Docker** image store, so locally built tags are visible without that toggle. After the switch you should see the node name **`docker-desktop`** (not `desktop-control-plane`); **`imagePullPolicy: Never`** with `eventhub-main-*:latest` then works with `docker compose build` on the same machine.

Quick check after a rebuild:

```powershell
kubectl run imgcheck --image=eventhub-main-booking-service:latest --image-pull-policy=Never --restart=Never --command -- sleep 30
kubectl get pod imgcheck
kubectl delete pod imgcheck --ignore-not-found
```

If `imgcheck` stays **`ErrImageNeverPull`**, the cluster still cannot see your Compose-built image (fix the image store or provisioner above).

Declarative equivalent (same check, lives in repo): `kubectl apply -f k8s/test-local-image-pod.yaml` then `kubectl get pod test-eventhub-image` — expect **`Succeeded`** / **`Completed`**, not **`ErrImageNeverPull`**. Clean up with `kubectl delete -f k8s/test-local-image-pod.yaml`. **Do not** add that file to `kustomization.yaml` (keep it out of `kubectl apply -k k8s/`).

**Note:** Any external guide that says `kubectl apply -k ./kustomize-dir/` is wrong for this project — the overlay is **`k8s/`** (`kubectl apply -k k8s/`).

**Automation limit:** From the terminal we can run `docker compose build`, `kubectl apply`, resets (`docker desktop kubernetes reset-cluster`), and checks. **We cannot click Docker Desktop Settings** (for example switching the Kubernetes provisioner from **kind** to **kubeadm**, or toggling **Use containerd for pulling and storing images**). If `eventhub-imgcheck` / your pods still show **`ErrImageNeverPull`**, that GUI step is still required on your machine.

## Run tests

Hand-written booking unit tests live in **`services/booking-service/booking_service_tests/`** (not a nested `tests/` folder under the service, because pytest would treat that as the repo `tests` package and break collection).

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
