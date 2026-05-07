# ARCHITECTURE.md

Design decisions for the EventHub vertical slice.

## System

EventHub is a scaled-down event ticketing platform. The slice covers browse, book, pay, issue, confirm. No cancellation UI, no auth, no real payment processor.

## Bounded contexts and services

Each context maps to one microservice. Each service owns its own data. No service reads or writes another service's data directly.

### booking-service (hand-written core)

Responsibilities:

- Receive booking requests over HTTP
- Reserve a ticket against an event's availability counter
- Track the booking lifecycle: held, awaiting_payment, awaiting_ticket, confirmed, failed
- Publish events as the lifecycle progresses
- Serve the hardcoded event catalog to the frontend

Data owned (in Redis):

- `booking:{uuid}` keys with JSON values containing id, event_id, customer_id, status, ticket_id, correlation_id, created_at
- `event:{id}:available` integer counters for ticket availability

HTTP endpoints:

- `POST /bookings` body `{event_id, customer_id}` returns `{booking_id, status}`
- `GET /bookings/{id}` returns the current booking record
- `GET /events` returns the 5 hardcoded events
- `GET /healthz` returns 200 OK for K8s probes

Publishes:

- `booking.requested` after a hold goes in
- `booking.confirmed` after seeing `ticket.issued`
- `booking.failed` after seeing `payment.failed`

Consumes:

- `payment.authorised`
- `payment.failed`
- `ticket.issued`

### payment-service (AI-generated)

Fakes a payment processor. Sleeps 200ms, then 90% chance of authorising.

- Consumes: `booking.requested`
- Publishes: `payment.authorised` or `payment.failed`

### ticket-service (AI-generated)

Generates a UUID4 as a ticket ID. Stores it in Redis under `ticket:{id}`.

- Consumes: `payment.authorised`
- Publishes: `ticket.issued`

### notification-service (AI-generated)

Subscribes to all events on the bookings exchange. Writes one JSON log line per event with the correlation ID present.

- Consumes: every event
- Publishes: nothing

### web-frontend (AI-generated)

Flask app on port 8080. One page lists 5 events with a Book button per event. After submitting, it polls booking status every second and updates the page.

- Calls: `booking-service` over HTTP

## Events

Every event flows through one RabbitMQ topic exchange named `bookings`. Routing keys match event names.

| Event | Publisher | Consumers | Purpose |
|---|---|---|---|
| booking.requested | booking-service | payment-service, notification-service | Hold placed, payment needed |
| payment.authorised | payment-service | ticket-service, notification-service | Money captured |
| payment.failed | payment-service | booking-service, notification-service | Card declined |
| ticket.issued | ticket-service | booking-service, notification-service | Ticket ready |
| booking.confirmed | booking-service | notification-service | Customer-facing success |
| booking.failed | booking-service | notification-service | Customer-facing failure |

Every event payload is JSON with at minimum: `event_type`, `correlation_id`, `booking_id`, `timestamp`. Specific events add their own fields, like `ticket_id` on `ticket.issued`.

## Correlation IDs

booking-service mints a UUID4 per incoming HTTP request. Every published event carries it in two places: the JSON payload, and the AMQP `correlation_id` header.

Consumers copy the ID onto every event they publish in response. Notification-service writes it on every log line.

The marker can trace a single booking across all 5 services using one ID. Show this in the video.

## Scaling decisions

Stateless services scale horizontally. Stateful infrastructure does not, at least not in a demo.

| Component | Replicas | Reason |
|---|---|---|
| web-frontend | 2 | Stateless, scales horizontally |
| booking-service | 2 | Stateless logic. Redis holds the state. |
| payment-service | 1 | Demo throughput, no need for more |
| ticket-service | 1 | Same as above |
| notification-service | 1 | One log writer is simpler to reason about |
| rabbitmq | 1 | Clustering RabbitMQ adds operational cost we do not need for a demo |
| redis | 1 | Same reasoning. Sentinel and Cluster mode are out of scope. |

In the submission document, write 1 paragraph in Kiaran's own words on why the front and back stateless services scale to multiple replicas, but the broker and Redis stay at 1. The addendum from Larkin asks for this kind of thinking.

## Monitoring

Lightweight by design. Two layers:

1. **Correlation ID tracing.** One ID flows across all 5 services per booking. notification-service writes it on every log line. `kubectl logs -l app=notification-service` shows the trace.
2. **Health endpoints.** Each service exposes `/healthz` returning 200 OK. K8s liveness probes use this to restart unhealthy pods.

Skip Prometheus and Grafana unless time permits after everything else. The rubric's monitoring section is 15%, not 30%. A clean correlation ID story scores well.

## Test strategy

Pyramid shape. More fast tests at the bottom, fewer slow ones at the top.

| Layer | Tool | Marker | What it checks |
|---|---|---|---|
| Unit | pytest with mocks | `unit` | Booking logic, event payload shape |
| Contract | pytest | `contract` | Event JSON schemas across services |
| Integration | pytest + live Redis | `integration` | booking-service reads and writes Redis correctly |
| End-to-end | pytest + Compose | `e2e` | Full booking flow through all services |
| Performance | pytest | `performance` | Booking latency under 2 seconds |
| Security | bandit | `security` | Static scan for known issues |

Run unit and contract on every commit. Run integration and e2e nightly or before submission. Run performance and security on demand.

Drop performance and security first if time runs short.

## What we are NOT building

- Real payment processing (no Stripe, no Square)
- Real QR code rendering (a UUID string is the "ticket")
- User accounts and auth
- Cancellation UI (event flow exists but no button)
- Full event catalog (5 hardcoded events is fine)
- Saga compensation (booking.failed is logged, but no rollback work runs)
- HTTPS or TLS between services
- Multi-tenancy

If Kiaran asks for any of the above, ask him to confirm there's time. There almost certainly isn't.
