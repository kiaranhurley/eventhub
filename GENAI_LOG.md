# GENAI_LOG.md

Add a row every time you ask Claude Code, Copilot, ChatGPT, or any other AI for help on this assessment. Aim for 8 to 12 entries by Sunday night.

This log goes into the submission document. It is part of the 30% reflection grade.

**Scope note:** The **booking-service application code** (`main.py` behaviour, Redis model, Rabbit consumers, correlation IDs) is **hand-written by me** for this module. GenAI was used for **surrounding work** (other services earlier in the project, Docker/Compose packaging, debugging infra, Git operations), not to draft the core booking logic.

## The log

| Date | Task | Tool | Prompt summary | Manual changes | Output quality | What you learned |
|---|---|---|---|---|---|---|
| 2026-05-06 | Plan the assessment top to bottom | Claude (chat) | Asked for a 5-day plan covering the full assessment including the hand-written core service, AI-generated services, K8s, tests, monitoring, document, and video | None for planning row | Good. Surfaced rubric weighting and the reflection slice of the grade. | The Understanding and Reflection section is a large part of the grade; logging prompts as you go matters. |
| 2026-05-12 | Understand repo layout and behaviour | Cursor / Claude | Asked for a read-through of the EventHub project and what each part does | N/A (read-only explanation) | Good. Mapped services to ARCHITECTURE.md. | The vertical slice is smaller than a full product but the event flow is explicit end-to-end. |
| 2026-05-12 | Docker Desktop setup and Compose | Cursor / Claude | How to run the stack on Windows; `docker compose up --build` from the correct folder | Verified Docker Desktop running; used inner project path | Good. | The engine must be running before the CLI talks to a server; path to `docker-compose.yml` matters. |
| 2026-05-12 | Fix Redis `exec format error` in Compose | Cursor / Claude | Diagnose container start failure; image arch vs VM | Added `platform: linux/amd64` for `redis` and `rabbitmq`; `docker rmi` + `compose pull` to refresh layers | Mixed. Right diagnosis (wrong arch layer) but needed a clean pull to drop the bad cached image. | Pin platform on infra images when Desktop pulls the wrong variant; nuking the local image forces a correct re-pull. |
| 2026-05-12 | Docker build `COPY wait-for-it.sh` missing | Cursor / Claude | Compose build failed because wait-for-it was only mounted, not in build context | Copied `wait-for-it.sh` into each service directory that Dockerfile `COPY`s; trimmed web-frontend image where script unused; added `bash`/`netcat` where entrypoint runs wait-for-it | Good. | Build context is per-service folder; runtime volume mounts do not satisfy `COPY` at build time. |
| 2026-05-12 | K8s-safe booking-service image | Human + Cursor | (Human wrote service.) Asked to align Dockerfile so `/wait-for-it.sh` exists **inside** the image for Kubernetes, not only via Compose volume | Added `COPY wait-for-it.sh` + `chmod` in `services/booking-service/Dockerfile`; kept Compose volume optional | Good. | Same pattern as labs: image must be self-contained for K8s; Compose can still mount overrides for dev. |
| 2026-05-12 | Web UI stale ticket counts | Cursor / Claude | Frontend showed fixed availability; wire `index()` to booking-service `GET /events` | Removed hardcoded `EVENTS`; fetch live JSON with timeout and empty fallback | Good. | Single source of truth for inventory should be the service that owns Redis, not duplicated in the UI. |
| 2026-05-12 | Commit and push to GitHub | Cursor / Claude | Push updates to `github.com/kiaranhurley/eventhub` | Resolved nested-folder vs flat repo layout when syncing | Good. | Local folder layout may not match remote root; clone-merge or single inner repo avoids a mess. |
| 2026-05-12 | Kubernetes manifests from Compose | Cursor / Claude | Generate `k8s/` from `docker-compose.yml`: replicas (web 2, booking 2, others 1), NodePort 30080, ConfigMap for broker/Redis/booking URL, `/healthz` liveness | Added `kustomization.yaml` for apply order; initContainers (busybox) for startup deps; `command: ["python","main.py"]` to skip wait-for-it in-cluster; small threaded **HTTP /healthz on port 9100** in payment/ticket/notification so probes match ARCHITECTURE | Good. | Compose `depends_on` becomes initContainers + ClusterIP DNS; pure AMQP workers need an explicit health endpoint for kube probes. |

## Column guide

- **Date**: ISO format (YYYY-MM-DD), easy to sort
- **Task**: One short sentence on what you wanted done
- **Tool**: Claude Code, GitHub Copilot, ChatGPT, Codex, Claude (chat), etc.
- **Prompt summary**: 1 to 3 sentences. The verbatim prompt is not required.
- **Manual changes**: What you fixed, renamed, or added after the AI gave its output. Be specific.
- **Output quality**: Good, Mixed, or Poor, plus one sentence on why
- **What you learned**: One sentence. Concrete.

## What to log

Log meaningful prompts. Examples:

- "Generate the X service"
- "Write Kubernetes manifests for everything"
- "Suggest non-functional tests"
- "Why is RabbitMQ refusing the consumer's connection?"
- "Add bandit security scanning"
- "Convert this docker-compose.yml to K8s manifests"

Skip trivial prompts like "fix this typo". Aim for substance.

## Concrete failures (save these for the video)

The marking rubric and spec ask for at least one concrete example of where genAI failed or misled you. Keep a sub-list here. Pick the most interesting one for the video.

| Date | Tool | What went wrong | How you fixed it |
|---|---|---|---|
| 2026-05-12 | Cursor / Claude | Redis container exited with `exec format error`; first guess was not enough on its own until a bad **cached** `redis:7-alpine` layer stuck around | Set `platform: linux/amd64` in Compose for Redis/RabbitMQ, **`docker rmi redis:7-alpine`**, then `docker compose pull redis` and `up` again |

## Hand-written vs AI comparison (notes for the document)

As you go, jot down differences between writing booking-service yourself vs accepting AI output for the others. Use these notes when you write the comparison section in the document and the video.

- Which was easier to debug when it broke?
- Which felt safer to change?
- Which one did you understand line-by-line?
- If a bug appeared in production, which would you reach for first?

Notes:

- **Booking-service (mine):** I own the state machine, Redis keys, and Rabbit publish/consume paths; when something misbehaved I could reason from first principles. Infra bugs (Redis arch, image `COPY`) lived outside that code.
- **AI-assisted shell (Compose, Dockerfiles, other microservices):** Faster to scaffold, but failures were often **environmental** (build context, arch, entrypoint) until I read the error text and adjusted files by hand.
- **Kubernetes:** Manifests mirror Compose but needed extra pieces (ConfigMap env wiring, NodePort, probes). Consumer services only spoke AMQP until a minimal health HTTP was added for liveness—packaging work around the same Python you already had.
- **Debugging:** Booking logic bugs would be traced in Python and Redis; stack failures were Docker/registry/cache until platform and file copies were fixed.
