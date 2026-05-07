import json
import os
import random
import time
import uuid
from datetime import datetime, timezone

import pika

RABBITMQ_URL = os.environ.get("RABBITMQ_URL", "amqp://guest:guest@rabbitmq:5672/")
EXCHANGE = "bookings"


def get_connection():
    params = pika.URLParameters(RABBITMQ_URL)
    params.heartbeat = 60
    return pika.BlockingConnection(params)


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


def on_booking_requested(ch, method, properties, body):
    try:
        msg = json.loads(body)
        correlation_id = msg.get("correlation_id") or (properties.correlation_id or str(uuid.uuid4()))
        booking_id = msg.get("booking_id")
        print(f"[payment] received booking.requested booking_id={booking_id} correlation_id={correlation_id}", flush=True)

        time.sleep(0.2)

        base = {
            "correlation_id": correlation_id,
            "booking_id": booking_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        if random.random() < 0.9:
            payload = {**base, "event_type": "payment.authorised"}
            publish(ch, "payment.authorised", payload, correlation_id)
            print(f"[payment] published payment.authorised booking_id={booking_id}", flush=True)
        else:
            payload = {**base, "event_type": "payment.failed", "reason": "card_declined"}
            publish(ch, "payment.failed", payload, correlation_id)
            print(f"[payment] published payment.failed booking_id={booking_id}", flush=True)

        ch.basic_ack(delivery_tag=method.delivery_tag)
    except Exception as exc:
        print(f"[payment] error processing message: {exc}", flush=True)
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)


def main():
    connection = get_connection()
    channel = connection.channel()

    channel.exchange_declare(exchange=EXCHANGE, exchange_type="topic", durable=True)
    result = channel.queue_declare(queue="", exclusive=True)
    queue_name = result.method.queue
    channel.queue_bind(exchange=EXCHANGE, queue=queue_name, routing_key="booking.requested")

    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue=queue_name, on_message_callback=on_booking_requested)

    print("[payment] waiting for booking.requested messages", flush=True)
    channel.start_consuming()


if __name__ == "__main__":
    main()
