# CLAUDE.md

Read this file before any other action. It tells you what we're building, who is building it, and one rule you must not break.

## Who and when

- Student: Kiaran
- Module: SOFT8026 Data-Driven Microservices
- Assessment: 2 of 2, worth 50% of the module grade
- Deadline: 8pm Monday 11 May 2026 (Irish time)
- OS: Windows 11 with PowerShell
- Working directory: `C:\Users\kiara\Desktop\College\Data Driven Microservices\`

## CRITICAL RULE: booking-service is off-limits to AI

The assessment requires one core microservice written by hand without any genAI help. That service is `booking-service`.

You must not:

- Write code for files inside `services/booking-service/`
- Suggest code blocks for the booking-service in chat
- Autocomplete inside any booking-service file
- Refactor booking-service code
- Generate booking-service tests for Kiaran (he writes those too)

You can:

- Read booking-service code to understand it
- Run booking-service tests
- Help debug error messages by talking through the cause
- Answer conceptual questions about what the service should do
- Run shell commands that interact with the running service

If Kiaran asks you to write or edit anything in `services/booking-service/`, reply: "That service is hand-written for academic integrity. I won't write or edit the code, but I can talk through the logic." Then stop.

Every other service is fair game.

## What we are building

EventHub: a vertical slice of an event ticketing platform. One end-to-end booking flow.

The flow:

1. Customer opens the web frontend and sees 5 hardcoded events
2. Customer clicks Book on one event
3. Frontend posts to booking-service
4. booking-service holds a ticket and publishes `booking.requested`
5. payment-service consumes that, charges a fake card, publishes `payment.authorised` (or `payment.failed` 10% of the time)
6. ticket-service consumes `payment.authorised`, makes a ticket ID, publishes `ticket.issued`
7. booking-service consumes `ticket.issued`, marks the booking confirmed, publishes `booking.confirmed`
8. notification-service logs every event with the correlation ID
9. Frontend polls and shows the user "Confirmed"

## Services

| Service | Author | Purpose |
|---|---|---|
| web-frontend | AI | Flask UI with 5 events and a Book button per event |
| booking-service | **HAND-WRITTEN ONLY** | Reservation hold, owns availability and booking records |
| payment-service | AI | Fake payment authorise and capture with 10% failure rate |
| ticket-service | AI | Ticket ID generation |
| notification-service | AI | Structured JSON log of every event |
| rabbitmq | infra | Message broker |
| redis | infra | Booking state store |

See `ARCHITECTURE.md` for the full event list, data ownership, and scaling decisions.

## Tech stack

- Python 3.11
- Flask for HTTP endpoints and the web frontend
- pika for RabbitMQ
- redis-py for Redis
- pytest plus markers for layered tests
- bandit for the security scan
- Docker, Docker Compose
- Kubernetes (Docker Desktop's built-in cluster, or kind, or minikube)

Stick to this stack. The labs taught these tools. Do not reach for asyncio, aio-pika, FastAPI, Kafka, or anything else the module did not cover.

## Project layout

```
.
├── CLAUDE.md                    (this file)
├── ARCHITECTURE.md
├── PLAN.md
├── GENAI_LOG.md
├── README.md
├── docker-compose.yml
├── pytest.ini
├── requirements.txt
├── requirements-dev.txt
├── wait-for-it.sh
├── services/
│   ├── booking-service/         HAND-WRITTEN, do not edit
│   │   ├── Dockerfile
│   │   ├── main.py
│   │   ├── requirements.txt
│   │   └── tests/               also hand-written
│   ├── payment-service/
│   ├── ticket-service/
│   ├── notification-service/
│   └── web-frontend/
├── k8s/
│   ├── booking-deployment.yaml
│   ├── booking-service.yaml
│   ├── payment-deployment.yaml
│   ├── payment-service.yaml
│   ├── ticket-deployment.yaml
│   ├── ticket-service.yaml
│   ├── notification-deployment.yaml
│   ├── notification-service.yaml
│   ├── frontend-deployment.yaml
│   ├── frontend-service.yaml
│   ├── rabbitmq-deployment.yaml
│   ├── rabbitmq-service.yaml
│   ├── redis-deployment.yaml
│   ├── redis-service.yaml
│   └── configmap.yaml
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── e2e/
│   ├── performance/
│   └── security/
└── docs/
    ├── architecture-diagram.png
    └── submission-document.docx
```

## Conventions from Labs 2 to 4

The lecturer (Larkin) uses a specific pattern. Match it.

- Each service lives in its own subdirectory under `services/`
- Each service has its own `Dockerfile`
- A `wait-for-it.sh` script handles startup ordering for RabbitMQ
- `docker-compose.yml` uses `depends_on` plus `wait-for-it.sh`
- Python services import `pika` for RabbitMQ and `redis` for Redis
- Print logging is fine for early services. Notification-service uses JSON logging.

## Common commands (PowerShell)

Build and run the full stack with Compose:

```powershell
docker compose up --build
```

Tear down:

```powershell
docker compose down
```

Run unit tests only:

```powershell
pytest -m unit
```

Run all tests:

```powershell
pytest
```

Apply Kubernetes manifests:

```powershell
kubectl apply -f k8s/
```

Watch pods come up:

```powershell
kubectl get pods --watch
```

Get logs from one service:

```powershell
kubectl logs -l app=notification-service --follow
```

Run bandit security scan:

```powershell
bandit -r services/
```

## Status checklist

Update these as you finish each step. Tick boxes by replacing `[ ]` with `[x]`.

- [ ] Day 1: booking-service hand-written, unit tests passing
- [ ] Day 2: AI generates payment, ticket, notification, web-frontend
- [ ] Day 2: docker-compose.yml runs the full event flow
- [ ] Day 3: K8s manifests applied, all pods Running
- [ ] Day 4: tests in 5 categories, pipeline script works
- [ ] Day 4: monitoring via correlation IDs and JSON logs
- [ ] Day 5: submission document written
- [ ] Day 5: 4-to-6 minute video recorded
- [ ] Day 6: zip and submit before 8pm Monday 11 May

## Reflection requirement (30% of grade)

The submission needs honest reflection on AI use. As we go:

- Log every meaningful prompt in `GENAI_LOG.md`
- Note what you fixed by hand after each AI output
- Save at least one concrete AI failure for the video
- Compare the hand-written booking-service against the AI services in the document and video. Which was easier to debug? Which felt safer to change?

The reflection section is the single biggest scorer in the rubric. Write it in Kiaran's voice, not yours.

## What not to do

- Do not write or edit `services/booking-service/`
- Do not pad the system with extra services beyond the 5 listed
- Do not add Kafka, gRPC streaming, or anything outside Lab content
- Do not set up full Prometheus and Grafana unless time permits after everything else
- Do not generate a 20-page submission document. Aim for 4 to 6 pages.
- Do not write the genAI reflection or video script for Kiaran. He has to do that bit.

## Reference docs in this repo

- `ARCHITECTURE.md` for events, data ownership, scaling rationale
- `PLAN.md` for the day-by-day schedule
- `GENAI_LOG.md` for the prompt log template

## Reference docs outside this repo

The original assessment spec PDF, rubric, and addendum live in Kiaran's chat history. Ask him to paste them if you need them.
