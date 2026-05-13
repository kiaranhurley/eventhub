# PLAN.md

Day-by-day plan from now to the 11 May deadline.

## The week at a glance

| Day | Date | Goal |
|---|---|---|
| 1 | Wed 6 May | Hand-write booking-service |
| 2 | Thu 7 May | AI generates 4 services, Compose stack runs end-to-end |
| 3 | Fri 8 May | Kubernetes manifests, full stack on K8s |
| 4 | Sat 9 May | Tests in 5 categories, monitoring via correlation IDs |
| 5 | Sun 10 May | Submission document, demo video |
| 6 | Mon 11 May | Polish, zip, submit before 8pm |

## Day 1 (Wed 6 May): hand-written core

This is the part Kiaran cannot offload. Claude Code must not help write any code in this section.

What Kiaran does:

- Set up the project tree under `services/`
- Create `services/booking-service/` with a `Dockerfile`, `main.py`, `requirements.txt`
- Write the booking-service in Flask + pika + redis-py
- Implement `POST /bookings`, `GET /bookings/{id}`, `GET /events`, `GET /healthz`
- Add a consumer thread for `payment.authorised`, `payment.failed`, `ticket.issued`
- Write 4 to 5 pytest unit tests in `services/booking-service/booking_service_tests/` (not `tests/` under the service — clashes with repo `tests` in pytest). Mock pika and redis.
- Commit every step through git. The marker may look at the history.

What Claude Code does:

- Stays out of `services/booking-service/` entirely
- Helps with the broader project tree if asked (folders for other services)
- Answers conceptual questions about pika, Flask, Redis, RabbitMQ exchanges

End-of-day check: `pytest services/booking-service/booking_service_tests/` passes locally.

## Day 2 (Thu 7 May): AI generates the rest

What Kiaran does:

- Prompts Claude Code or Copilot for each service one at a time
- Reviews each generated service before accepting
- Logs every prompt in `GENAI_LOG.md`
- Wires everything together in `docker-compose.yml`
- Tests the full event flow with `docker compose up`

Starter prompts for Claude Code:

- "Generate `services/payment-service/` with a Python script that consumes `booking.requested` from a RabbitMQ topic exchange called `bookings`. Sleep 200ms. Publish `payment.authorised` 90% of the time and `payment.failed` 10% of the time. Carry the correlation ID across. Include a Dockerfile and requirements.txt."
- "Generate `services/ticket-service/` that consumes `payment.authorised`, generates a UUID4 ticket ID, stores it in Redis under `ticket:{id}`, and publishes `ticket.issued`. Carry the correlation ID. Include a Dockerfile."
- "Generate `services/notification-service/` that consumes every routing key on the `bookings` exchange and writes one JSON log line per message. Each log line has timestamp, service, level, correlation_id, event_type, and the full payload. Include a Dockerfile."
- "Generate `services/web-frontend/` as a Flask app on port 8080. One page lists 5 hardcoded events. Each event has a Book button that POSTs to `http://booking-service:5000/bookings`. After submit, poll `GET /bookings/{id}` every second and update the page. Include a Dockerfile."
- "Generate `docker-compose.yml` for all 5 services plus rabbitmq:3-management and redis:7. Use depends_on with the wait-for-it.sh pattern for RabbitMQ readiness. Expose web-frontend on host port 8080."

End-of-day check: `docker compose up --build` runs the full booking flow. Notification logs show all 5 events with the same correlation ID.

## Day 3 (Fri 8 May): Kubernetes

What Kiaran does:

- Asks Claude Code to convert the working `docker-compose.yml` into K8s manifests
- Reviews each manifest and corrects the replica counts to match `ARCHITECTURE.md`
- Applies the manifests to a local cluster (Docker Desktop, kind, or minikube)
- Confirms all pods reach Running

Manifests to produce inside `k8s/`:

- Deployment plus Service per microservice (5 sets)
- Deployment plus Service for rabbitmq
- Deployment plus Service for redis
- A ConfigMap with environment variables (RabbitMQ URL, Redis URL)
- A Service of type NodePort or LoadBalancer for web-frontend on host port 30080

Replica counts (set these explicitly, do not let the AI guess):

| Service | Replicas |
|---|---|
| web-frontend | 2 |
| booking-service | 2 |
| payment-service | 1 |
| ticket-service | 1 |
| notification-service | 1 |
| rabbitmq | 1 |
| redis | 1 |

End-of-day check: `kubectl get pods` shows everything Running. Open the frontend on `http://localhost:30080`, click Book, see the confirmation come back. `kubectl logs -l app=notification-service` shows all 5 events.

## Day 4 (Sat 9 May): tests and monitoring

### Tests pipeline

What Kiaran does:

- Asks Claude Code to generate `pytest.ini` with markers: unit, contract, integration, e2e, performance, security
- Asks for `tests/` skeleton matching the markers
- Reviews and tweaks
- Runs each layer to confirm it works

Test files to produce (Claude Code generates everything except booking-service unit tests, which already exist from Day 1):

- `tests/unit/test_payment_service.py`
- `tests/unit/test_ticket_service.py`
- `tests/unit/test_notification_service.py`
- `tests/contract/test_event_schemas.py`
- `tests/integration/test_redis_booking.py`
- `tests/e2e/test_full_booking_flow.py`
- `tests/performance/test_latency.py` asserting end-to-end booking finishes in under 2 seconds
- `tests/security/test_bandit_scan.py` running bandit and asserting no high-severity findings

A simple bash or PowerShell script in the repo root chains the layers:

```powershell
# run-tests.ps1
pytest -m unit
pytest -m contract
pytest -m integration
pytest -m e2e
pytest -m performance
bandit -r services/
```

### Monitoring

Pick the lightweight option (Option A in the original plan).

- Confirm correlation IDs flow across all 5 services. notification-service log lines all carry the same ID for one booking.
- Add a `/healthz` endpoint to each AI-generated service. Add liveness probes to the K8s manifests pointing at `/healthz`.
- Test by killing a pod and watching K8s restart it.

End-of-day check: `pytest -m "unit or integration"` passes. A booking traced through `kubectl logs` shows the same correlation ID 6 times (one per event). Killing a pod with `kubectl delete pod <name>` triggers a restart.

## Day 5 (Sun 10 May): document and video

### Document (Word or PDF, 4 to 6 pages)

Sections:

1. **Microservices list.** One line per service. Mark booking-service as hand-written.
2. **Event-driven architecture write-up.** 1 page in Kiaran's own words. Include the diagram from `docs/architecture-diagram.png`.
3. **Tests list and how to run them.** Table of test files plus the exact commands.
4. **Monitoring overview.** 3 paragraphs in Kiaran's own words covering correlation IDs, structured logs, and health probes.
5. **GenAI prompt log.** Paste the table from `GENAI_LOG.md`.

Claude Code can help format the document, generate the architecture diagram (or a Mermaid source), and proofread. It must not write the architecture or monitoring sections. Those have to be in Kiaran's voice for the marker to score them well.

### Video (4 to 6 minutes total)

Run sheet:

- 0:00 to 0:30 — Intro. State the system, the slice, what was hand-written.
- 0:30 to 1:30 — `kubectl get pods` and `kubectl get svc`. Point at each one and say what it does.
- 1:30 to 3:00 — Live event flow. Open the frontend, click Book, switch to a second terminal showing notification-service logs streaming. Walk through the 6 log lines as they appear.
- 3:00 to 5:00 — GenAI reflection. Where it helped (one specific example, e.g. RabbitMQ consumer setup). Where it failed (one concrete example from the log). What got fixed by hand. Hand-written vs AI: which was easier to debug.
- 5:00 to 5:30 — Outro. What you understand that the AI cannot replace (the bounded context decisions, why booking is the core, when to use events vs HTTP).

Record in one take if possible. Use OBS Studio or Windows Game Bar (Win+G). Trim with Clipchamp.

End-of-day check: document is 4 to 6 pages, video is between 4:00 and 6:00, both files render correctly.

## Day 6 (Mon 11 May): polish and submit

Final checklist:

- [ ] All pods come up clean from a fresh `kubectl apply -f k8s/`
- [ ] `pytest -m "unit or integration"` passes
- [ ] Document reads in Kiaran's voice on the architecture and monitoring sections
- [ ] Video plays without audio glitches and is under 6 minutes
- [ ] Zip everything: `code/`, `submission-document.pdf`, `demo.mp4`
- [ ] Upload before 8pm

Time buffer: aim to upload by 6pm. Last-minute Wi-Fi issues are real.

## Marks weighting and where to put effort

The rubric scores out of 100:

- **Understanding and Reflection (30%)** — biggest section. Real reflection beats slick code. Write the reflection yourself.
- **Microservice Implementation (25%)** — booking-service is what the marker scrutinises hardest. The other 4 just need to work.
- **Event-Driven Architecture (15%)** — the diagram and the live event flow demo cover this.
- **Deployment, Testing, Monitoring (15%)** — basic working pipelines hit this fully. Do not over-build.
- **Video Demonstration (15%)** — clarity beats polish. Speak slowly. Show, do not tell.

If time runs short, drop in this order: performance tests, security tests, Option B monitoring, frontend polish, second replica counts. Never drop the hand-written booking-service or the kubectl demo.

## Things that can go wrong

- K8s on Windows can take 10 minutes to start the first time. Begin Friday early.
- RabbitMQ exchange and binding setup trips up genAI. Confirm the event flow on Compose first, then port it to K8s.
- Bandit will flag false positives. Note this in the reflection. Do not fix every warning.
- Recording a video at 1am Sunday is a bad idea. Aim to finish recording by 6pm Sunday.
- Reconstructing the prompt log from memory on Sunday reads false. Keep it up to date day by day.

## What to ask Claude Code for, in order

This list helps Kiaran know what to prompt for next. Tick items off as you go.

- [ ] Project tree skeleton (NOT the booking-service code, just folders)
- [ ] payment-service (full)
- [ ] ticket-service (full)
- [ ] notification-service (full)
- [ ] web-frontend (full)
- [ ] docker-compose.yml
- [ ] K8s manifests for all 7 components
- [ ] ConfigMap and NodePort
- [ ] pytest.ini and tests/ skeleton (excluding booking-service tests)
- [ ] Performance and security test files
- [ ] run-tests.ps1 script
- [ ] Architecture diagram source (Mermaid or Draw.io)
- [ ] Document outline (Kiaran fills in the prose)
- [ ] Video run sheet polish (Kiaran writes the actual narration)
