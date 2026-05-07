import json
import os
import uuid
from datetime import datetime, timezone

import pika
import redis

RABBITMQ_URL = os.environ.get("RABBITMQ_URL", "amqp://guest:guest@rabbitmq:5672/")
REDIS_URL = os.environ.get("REDIS_URL", "redis://redis:6379/0")
EXCHANGE = "bookings"


def get_connection():
    params = pika.URLParameters(RABBITMQ_URL)
    params.heartbeat = 60
    return pika.BlockingConnection(params)


def get_redis():
    return redis.from_url(REDIS_URL, decode_responses=True)


def publish(channel, routing_key, payload, correlation_id):
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


def on_payment_authorised(ch, method, properties, body):
    try:
        msg = json.loads(body)
        correlation_id = msg.get("correlation_id") or (properties.correlation_id or str(uuid.uuid4()))
        booking_id = msg.get("booking_id")
        print(f"[ticket] received payment.authorised booking_id={booking_id} correlation_id={correlation_id}", flush=True)

        ticket_id = str(uuid.uuid4())
        r = get_redis()
        r.set(f"ticket:{ticket_id}", json.dumps({
            "ticket_id": ticket_id,
            "booking_id": booking_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }))

        payload = {
            "event_type": "ticket.issued",
            "correlation_id": correlation_id,
            "booking_id": booking_id,
            "ticket_id": ticket_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        publish(ch, "ticket.issued", payload, correlation_id)
        print(f"[ticket] published ticket.issued ticket_id={ticket_id} booking_id={booking_id}", flush=True)

        ch.basic_ack(delivery_tag=method.delivery_tag)
    except Exception as exc:
        print(f"[ticket] error processing message: {exc}", flush=True)
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)


def main():
    connection = get_connection()
    channel = connection.channel()

    channel.exchange_declare(exchange=EXCHANGE, exchange_type="topic", durable=True)
    result = channel.queue_declare(queue="", exclusive=True)
    queue_name = result.method.queue
    channel.queue_bind(exchange=EXCHANGE, queue=queue_name, routing_key="payment.authorised")

    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue=queue_name, on_message_callback=on_payment_authorised)

    print("[ticket] waiting for payment.authorised messages", flush=True)
    channel.start_consuming()


if __name__ == "__main__":
    main()
