"""Unit tests for ticket-service handler (mocked Redis + channel)."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from unittest.mock import MagicMock

import pytest

_ROOT = Path(__file__).resolve().parents[2]


def _load():
    path = _ROOT / "services" / "ticket-service" / "main.py"
    spec = importlib.util.spec_from_file_location("ticket_service_main", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def ticket():
    return _load()


@pytest.mark.unit
def test_payment_authorised_stores_ticket_and_publishes_ticket_issued(ticket, monkeypatch):
    fake_r = MagicMock()
    monkeypatch.setattr(ticket, "get_redis", lambda: fake_r)

    ch = MagicMock()
    method = MagicMock()
    method.delivery_tag = 9
    props = MagicMock()
    props.correlation_id = "corr-t"
    body = json.dumps({"booking_id": "bid-9", "correlation_id": "corr-t"}).encode()

    ticket.on_payment_authorised(ch, method, props, body)

    fake_r.set.assert_called_once()
    set_args, _ = fake_r.set.call_args
    ticket_key = set_args[0]
    assert ticket_key.startswith("ticket:")
    ch.basic_publish.assert_called_once()
    assert ch.basic_publish.call_args.kwargs["routing_key"] == "ticket.issued"
    out = json.loads(ch.basic_publish.call_args.kwargs["body"])
    assert out["booking_id"] == "bid-9"
    assert out["event_type"] == "ticket.issued"
    assert "ticket_id" in out
    ch.basic_ack.assert_called_once_with(delivery_tag=9)
