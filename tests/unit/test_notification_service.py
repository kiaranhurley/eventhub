"""notification handler — fake rabbit channel"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from unittest.mock import MagicMock

import pytest

_ROOT = Path(__file__).resolve().parents[2]


def _load():
    path = _ROOT / "services" / "notification-service" / "main.py"
    spec = importlib.util.spec_from_file_location("notification_service_main", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def notification():
    return _load()


@pytest.mark.unit
def test_on_any_event_logs_and_acks_valid_json(notification):
    ch = MagicMock()
    method = MagicMock()
    method.routing_key = "booking.confirmed"
    method.delivery_tag = 3
    props = MagicMock()
    props.correlation_id = "c99"
    payload = {"event_type": "booking.confirmed", "correlation_id": "c99", "booking_id": "b1"}
    body = json.dumps(payload).encode()

    notification.on_any_event(ch, method, props, body)

    ch.basic_ack.assert_called_once_with(delivery_tag=3)
    ch.basic_nack.assert_not_called()


@pytest.mark.unit
def test_on_any_event_nacks_invalid_json(notification):
    ch = MagicMock()
    method = MagicMock()
    method.routing_key = "broken"
    method.delivery_tag = 4
    props = MagicMock()
    props.correlation_id = None

    notification.on_any_event(ch, method, props, b"not-json{{{")
    ch.basic_nack.assert_called_once_with(delivery_tag=4, requeue=False)
