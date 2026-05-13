"""booking tests — fake redis + fake publish, no rabbit"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from unittest.mock import MagicMock

import pytest

_ROOT = Path(__file__).resolve().parents[3]


def _load_booking_main():
    path = _ROOT / "services" / "booking-service" / "main.py"
    spec = importlib.util.spec_from_file_location("booking_service_main", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def booking():
    return _load_booking_main()


@pytest.mark.unit
def test_healthz_ok(booking):
    client = booking.app.test_client()
    resp = client.get("/healthz")
    assert resp.status_code == 200
    assert resp.data == b"OK"


@pytest.mark.unit
def test_list_events_includes_catalog_and_redis_counts(booking, monkeypatch):
    fake = MagicMock()
    fake.get.side_effect = lambda k: {"event:evt-001:available": "3", "event:evt-002:available": "0"}.get(k, "1")

    monkeypatch.setattr(booking, "redis_conn", lambda: fake)

    client = booking.app.test_client()
    resp = client.get("/events")
    assert resp.status_code == 200
    data = resp.get_json()
    ids = {e["id"] for e in data}
    assert ids == booking.EVENT_IDS
    evt1 = next(e for e in data if e["id"] == "evt-001")
    assert evt1["available"] == 3


@pytest.mark.unit
def test_create_booking_rejects_unknown_event(booking, monkeypatch):
    fake = MagicMock()
    fake.decr.return_value = 10
    monkeypatch.setattr(booking, "redis_conn", lambda: fake)
    monkeypatch.setattr(booking, "publish_event", MagicMock())

    client = booking.app.test_client()
    resp = client.post("/bookings", json={"event_id": "evt-999", "customer_id": "u1"})
    assert resp.status_code == 400
    booking.publish_event.assert_not_called()


@pytest.mark.unit
def test_create_booking_conflict_when_sold_out(booking, monkeypatch):
    fake = MagicMock()
    fake.decr.return_value = -1
    fake.incr.return_value = 1
    monkeypatch.setattr(booking, "redis_conn", lambda: fake)
    monkeypatch.setattr(booking, "publish_event", MagicMock())

    client = booking.app.test_client()
    resp = client.post("/bookings", json={"event_id": "evt-001", "customer_id": "u1"})
    assert resp.status_code == 409
    assert resp.get_json()["error"] == "sold_out"
    fake.incr.assert_called_once_with("event:evt-001:available")
    booking.publish_event.assert_not_called()


@pytest.mark.unit
def test_create_booking_publishes_requested_and_sets_awaiting_payment(booking, monkeypatch):
    fake = MagicMock()
    fake.decr.return_value = 5
    monkeypatch.setattr(booking, "redis_conn", lambda: fake)
    monkeypatch.setattr(booking, "publish_event", MagicMock())

    client = booking.app.test_client()
    resp = client.post("/bookings", json={"event_id": "evt-001", "customer_id": "alice"})
    assert resp.status_code == 201
    body = resp.get_json()
    assert body["status"] == "awaiting_payment"
    assert "booking_id" in body

    booking.publish_event.assert_called_once()
    args, _kwargs = booking.publish_event.call_args
    rk, payload, cid = args
    assert rk == "booking.requested"
    assert payload["event_id"] == "evt-001"
    assert payload["customer_id"] == "alice"
    assert payload["correlation_id"] == cid


@pytest.mark.unit
def test_on_amqp_payment_authorised_transitions_booking(booking, monkeypatch):
    store = {
        "b1": {
            "id": "b1",
            "event_id": "evt-001",
            "customer_id": "guest",
            "status": "awaiting_payment",
            "ticket_id": None,
            "correlation_id": "corr-1",
            "created_at": booking.utc_now_iso(),
        }
    }

    def load_booking(r, booking_id):
        raw = store.get(booking_id)
        return json.loads(json.dumps(raw)) if raw else None

    def save_booking(r, booking_row):
        store[booking_row["id"]] = booking_row

    monkeypatch.setattr(booking, "load_booking", load_booking)
    monkeypatch.setattr(booking, "save_booking", save_booking)
    monkeypatch.setattr(booking, "publish_event", MagicMock())
    monkeypatch.setattr(booking, "redis_conn", lambda: MagicMock())

    ch = MagicMock()
    method = MagicMock()
    method.routing_key = "payment.authorised"
    method.delivery_tag = 42
    props = MagicMock()
    props.correlation_id = "corr-1"
    body = json.dumps({"booking_id": "b1", "correlation_id": "corr-1"})

    booking.on_amqp_message(ch, method, props, body.encode("utf-8"))

    assert store["b1"]["status"] == "awaiting_ticket"
    ch.basic_ack.assert_called_once_with(delivery_tag=42)
