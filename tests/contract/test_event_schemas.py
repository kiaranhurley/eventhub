"""quick checks that sample events have the fields we rely on"""

from __future__ import annotations

import pytest


def _required_keys_booking_requested():
    return {"event_type", "correlation_id", "booking_id", "timestamp", "event_id", "customer_id"}


def _required_keys_payment_outcome():
    return {"correlation_id", "booking_id", "timestamp"}


@pytest.mark.contract
def test_booking_requested_shape():
    sample = {
        "event_type": "booking.requested",
        "correlation_id": "c1",
        "booking_id": "b1",
        "timestamp": "2026-05-13T12:00:00+00:00",
        "event_id": "evt-001",
        "customer_id": "guest",
    }
    assert _required_keys_booking_requested() <= sample.keys()
    assert sample["event_type"] == "booking.requested"


@pytest.mark.contract
def test_payment_authorised_shape():
    sample = {
        "event_type": "payment.authorised",
        "correlation_id": "c1",
        "booking_id": "b1",
        "timestamp": "2026-05-13T12:00:01+00:00",
    }
    assert _required_keys_payment_outcome() <= sample.keys()


@pytest.mark.contract
def test_ticket_issued_shape():
    sample = {
        "event_type": "ticket.issued",
        "correlation_id": "c1",
        "booking_id": "b1",
        "ticket_id": "t-uuid",
        "timestamp": "2026-05-13T12:00:02+00:00",
    }
    need = {"event_type", "correlation_id", "booking_id", "ticket_id", "timestamp"}
    assert need <= sample.keys()


@pytest.mark.contract
def test_booking_confirmed_shape():
    sample = {
        "event_type": "booking.confirmed",
        "correlation_id": "c1",
        "booking_id": "b1",
        "timestamp": "2026-05-13T12:00:03+00:00",
        "ticket_id": "t-uuid",
        "event_id": "evt-001",
    }
    need = {"event_type", "correlation_id", "booking_id", "ticket_id", "event_id", "timestamp"}
    assert need <= sample.keys()
