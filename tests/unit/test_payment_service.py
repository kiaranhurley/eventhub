"""Unit tests for payment-service handler (mocked channel; no RabbitMQ)."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from unittest.mock import MagicMock

import pytest

_ROOT = Path(__file__).resolve().parents[2]


def _load():
    path = _ROOT / "services" / "payment-service" / "main.py"
    spec = importlib.util.spec_from_file_location("payment_service_main", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def payment():
    return _load()


@pytest.mark.unit
def test_booking_requested_publishes_authorised_when_random_favours_success(payment, monkeypatch):
    monkeypatch.setattr(payment.random, "random", lambda: 0.0)
    ch = MagicMock()
    method = MagicMock()
    method.delivery_tag = 1
    props = MagicMock()
    props.correlation_id = "corr-a"
    body = json.dumps({"booking_id": "bid-1", "correlation_id": "corr-a"}).encode()

    payment.on_booking_requested(ch, method, props, body)

    ch.basic_publish.assert_called_once()
    kwargs = ch.basic_publish.call_args.kwargs
    assert kwargs["routing_key"] == "payment.authorised"
    published = json.loads(kwargs["body"])
    assert published["booking_id"] == "bid-1"
    ch.basic_ack.assert_called_once_with(delivery_tag=1)


@pytest.mark.unit
def test_booking_requested_publishes_failed_when_random_favours_failure(payment, monkeypatch):
    monkeypatch.setattr(payment.random, "random", lambda: 0.99)
    ch = MagicMock()
    method = MagicMock()
    method.delivery_tag = 2
    props = MagicMock()
    props.correlation_id = None
    body = json.dumps({"booking_id": "bid-2"}).encode()

    payment.on_booking_requested(ch, method, props, body)

    ch.basic_publish.assert_called_once()
    kwargs = ch.basic_publish.call_args.kwargs
    assert kwargs["routing_key"] == "payment.failed"
    published = json.loads(kwargs["body"])
    assert published["event_type"] == "payment.failed"
    assert "reason" in published
    ch.basic_ack.assert_called_once_with(delivery_tag=2)
