import json
import os
import uuid
from datetime import datetime, timezone

import pika

RABBITMQ_URL = os.environ.get("RABBITMQ_URL", "amqp://guest:guest@rabbitmq:5672/")
EXCHANGE = "bookings"


def get_connection():
    params = pika.URLParameters(RABBITMQ_URL)
    params.heartbeat = 60
    return pika.BlockingConnection(params)


def on_any_event(ch, method, properties, body):
    try:
        payload = json.loads(body)
        log_line = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "service": "notification-service",
            "level": "INFO",
            "correlation_id": payload.get("correlation_id") or properties.correlation_id or "",
            "event_type": payload.get("event_type") or method.routing_key,
            "payload": payload,
        }
        print(json.dumps(log_line), flush=True)
        ch.basic_ack(delivery_tag=method.delivery_tag)
    except Exception as exc:
        log_line = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "service": "notification-service",
            "level": "ERROR",
            "correlation_id": "",
            "event_type": method.routing_key,
            "error": str(exc),
            "raw": body.decode("utf-8", errors="replace"),
        }
        print(json.dumps(log_line), flush=True)
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)


def main():
    connection = get_connection()
    channel = connection.channel()

    channel.exchange_declare(exchange=EXCHANGE, exchange_type="topic", durable=True)
    result = channel.queue_declare(queue="", exclusive=True)
    queue_name = result.method.queue
    channel.queue_bind(exchange=EXCHANGE, queue=queue_name, routing_key="#")

    channel.basic_qos(prefetch_count=10)
    channel.basic_consume(queue=queue_name, on_message_callback=on_any_event)

    print("[notification] waiting for all events on bookings exchange", flush=True)
    channel.start_consuming()


if __name__ == "__main__":
    main()
