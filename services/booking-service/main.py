import json
import os
import threading
import uuid
from datetime import datetime, timezone

import pika
import redis
from flask import Flask, jsonify, request

RABBITMQ_URL = os.environ.get("RABBITMQ_URL", "amqp://guest:guest@rabbitmq:5672/")
REDIS_URL = os.environ.get("REDIS_URL", "redis://redis:6379/0")
EXCHANGE = "bookings"

EVENT_CATALOG = [
    {
        "id": "evt-001",
        "name": "Dublin Tech Summit",
        "venue": "RDS Arena, Dublin",
        "date": "2026-06-14",
        "price": 49.00,
        "initial_available": 200,
    },
    {
        "id": "evt-002",
        "name": "Cork Jazz Festival",
        "venue": "Fitzgerald Park, Cork",
        "date": "2026-07-20",
        "price": 25.00,
        "initial_available": 500,
    },
    {
        "id": "evt-003",
        "name": "Galway Comedy Night",
        "venue": "Roisin Dubh, Galway",
        "date": "2026-08-03",
        "price": 18.00,
        "initial_available": 80,
    },
    {
        "id": "evt-004",
        "name": "Belfast Film Fest",
        "venue": "QFT, Belfast",
        "date": "2026-09-12",
        "price": 12.00,
        "initial_available": 150,
    },
    {
        "id": "evt-005",
        "name": "Limerick Startup Day",
        "venue": "Limerick Institute",
        "date": "2026-10-01",
        "price": 0.00,
        "initial_available": 300,
    },
]

EVENT_IDS = {e["id"] for e in EVENT_CATALOG}

app = Flask(__name__)


def redis_conn():
    return redis.from_url(REDIS_URL, decode_responses=True)


def seed_availability_if_missing(r):
    for ev in EVENT_CATALOG:
        key = f"event:{ev['id']}:available"
        r.set(key, ev["initial_available"], nx=True)


def utc_now_iso():
    return datetime.now(timezone.utc).isoformat()


def publish_event(routing_key, payload, correlation_id):
    params = pika.URLParameters(RABBITMQ_URL)
    params.heartbeat = 60
    connection = pika.BlockingConnection(params)
    try:
        channel = connection.channel()
        channel.exchange_declare(exchange=EXCHANGE, exchange_type="topic", durable=True)
        channel.basic_publish(
            exchange=EXCHANGE,
            routing_key=routing_key,
            body=json.dumps(payload),
            properties=pika.BasicProperties(
                content_type="application/json",
                delivery_mode=2,
                correlation_id=correlation_id,
            ),
        )
    finally:
        connection.close()


def load_booking(r, booking_id):
    raw = r.get(f"booking:{booking_id}")
    if not raw:
        return None
    return json.loads(raw)


def save_booking(r, booking):
    r.set(f"booking:{booking['id']}", json.dumps(booking))


def reserve_one_ticket(r, event_id):
    key = f"event:{event_id}:available"
    remaining = r.decr(key)
    if remaining < 0:
        r.incr(key)
        return False
    return True


def release_one_ticket(r, event_id):
    r.incr(f"event:{event_id}:available")


def on_amqp_message(ch, method, properties, body):
    r = redis_conn()
    try:
        msg = json.loads(body)
        routing_key = method.routing_key
        correlation_id = msg.get("correlation_id") or (properties.correlation_id or "")
        booking_id = msg.get("booking_id")
        if not booking_id:
            ch.basic_ack(delivery_tag=method.delivery_tag)
            return

        booking = load_booking(r, booking_id)
        if not booking:
            ch.basic_ack(delivery_tag=method.delivery_tag)
            return

        if routing_key == "payment.authorised":
            if booking["status"] != "awaiting_payment":
                ch.basic_ack(delivery_tag=method.delivery_tag)
                return
            booking["status"] = "awaiting_ticket"
            save_booking(r, booking)
            print(f"[booking] payment.authorised booking_id={booking_id}", flush=True)

        elif routing_key == "payment.failed":
            if booking["status"] != "awaiting_payment":
                ch.basic_ack(delivery_tag=method.delivery_tag)
                return
            booking["status"] = "failed"
            save_booking(r, booking)
            release_one_ticket(r, booking["event_id"])
            fail_payload = {
                "event_type": "booking.failed",
                "correlation_id": correlation_id or booking.get("correlation_id"),
                "booking_id": booking_id,
                "timestamp": utc_now_iso(),
                "reason": msg.get("reason", "payment_failed"),
            }
            publish_event(
                "booking.failed",
                fail_payload,
                correlation_id or booking.get("correlation_id"),
            )
            print(f"[booking] booking.failed booking_id={booking_id}", flush=True)

        elif routing_key == "ticket.issued":
            if booking["status"] == "confirmed":
                ch.basic_ack(delivery_tag=method.delivery_tag)
                return
            if booking["status"] != "awaiting_ticket":
                ch.basic_ack(delivery_tag=method.delivery_tag)
                return
            ticket_id = msg.get("ticket_id")
            booking["status"] = "confirmed"
            booking["ticket_id"] = ticket_id
            save_booking(r, booking)
            confirm_payload = {
                "event_type": "booking.confirmed",
                "correlation_id": correlation_id or booking.get("correlation_id"),
                "booking_id": booking_id,
                "timestamp": utc_now_iso(),
                "ticket_id": ticket_id,
                "event_id": booking.get("event_id"),
            }
            publish_event(
                "booking.confirmed",
                confirm_payload,
                correlation_id or booking.get("correlation_id"),
            )
            print(f"[booking] booking.confirmed booking_id={booking_id} ticket_id={ticket_id}", flush=True)

        ch.basic_ack(delivery_tag=method.delivery_tag)
    except Exception as exc:
        print(f"[booking] consumer error: {exc}", flush=True)
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)


def run_consumer():
    while True:
        try:
            params = pika.URLParameters(RABBITMQ_URL)
            params.heartbeat = 60
            connection = pika.BlockingConnection(params)
            channel = connection.channel()
            channel.exchange_declare(exchange=EXCHANGE, exchange_type="topic", durable=True)
            result = channel.queue_declare(queue="", exclusive=True)
            queue_name = result.method.queue
            for key in ("payment.authorised", "payment.failed", "ticket.issued"):
                channel.queue_bind(exchange=EXCHANGE, queue=queue_name, routing_key=key)
            channel.basic_qos(prefetch_count=10)
            channel.basic_consume(queue=queue_name, on_message_callback=on_amqp_message)
            print("[booking] consuming payment.* and ticket.issued", flush=True)
            channel.start_consuming()
        except Exception as exc:
            print(f"[booking] consumer reconnect after error: {exc}", flush=True)


@app.route("/healthz")
def healthz():
    return "OK", 200


@app.route("/events")
def list_events():
    r = redis_conn()
    seed_availability_if_missing(r)
    out = []
    for ev in EVENT_CATALOG:
        key = f"event:{ev['id']}:available"
        available = int(r.get(key) or 0)
        out.append(
            {
                "id": ev["id"],
                "name": ev["name"],
                "venue": ev["venue"],
                "date": ev["date"],
                "price": ev["price"],
                "available": available,
            }
        )
    return jsonify(out)


@app.route("/bookings", methods=["POST"])
def create_booking():
    r = redis_conn()
    seed_availability_if_missing(r)
    data = request.get_json(silent=True) or {}
    event_id = data.get("event_id")
    customer_id = data.get("customer_id") or "guest"

    if not event_id or event_id not in EVENT_IDS:
        return jsonify({"error": "invalid or missing event_id"}), 400

    if not reserve_one_ticket(r, event_id):
        return jsonify({"error": "sold_out", "event_id": event_id}), 409

    booking_id = str(uuid.uuid4())
    correlation_id = str(uuid.uuid4())
    created_at = utc_now_iso()
    booking = {
        "id": booking_id,
        "event_id": event_id,
        "customer_id": customer_id,
        "status": "held",
        "ticket_id": None,
        "correlation_id": correlation_id,
        "created_at": created_at,
    }
    save_booking(r, booking)

    requested = {
        "event_type": "booking.requested",
        "correlation_id": correlation_id,
        "booking_id": booking_id,
        "timestamp": created_at,
        "event_id": event_id,
        "customer_id": customer_id,
    }
    publish_event("booking.requested", requested, correlation_id)

    booking["status"] = "awaiting_payment"
    save_booking(r, booking)

    return jsonify({"booking_id": booking_id, "status": booking["status"]}), 201


@app.route("/bookings/<booking_id>")
def get_booking(booking_id):
    r = redis_conn()
    booking = load_booking(r, booking_id)
    if not booking:
        return jsonify({"error": "not_found"}), 404
    return jsonify(booking)


def main():
    r = redis_conn()
    seed_availability_if_missing(r)
    consumer_thread = threading.Thread(target=run_consumer, daemon=True)
    consumer_thread.start()
    app.run(host="0.0.0.0", port=5000, use_reloader=False, threaded=True)


if __name__ == "__main__":
    main()
