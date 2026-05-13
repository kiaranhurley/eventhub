"""End-to-end booking API against a running booking-service (Compose or local)."""

from __future__ import annotations

import os
import time
import uuid

import pytest
import requests

BOOKING_URL = os.environ.get("BOOKING_SERVICE_TEST_URL", "http://127.0.0.1:5000")


def _reachable():
    try:
        r = requests.get(f"{BOOKING_URL}/healthz", timeout=1.5)
        return r.status_code == 200
    except requests.RequestException:
        return False


@pytest.mark.e2e
def test_full_booking_flow_creates_booking_and_returns_json():
    if not _reachable():
        pytest.skip(f"booking-service not reachable at {BOOKING_URL} (start Compose or port-forward)")

    event_id = "evt-005"
    customer = f"e2e-{uuid.uuid4().hex[:8]}"
    create = requests.post(
        f"{BOOKING_URL}/bookings",
        json={"event_id": event_id, "customer_id": customer},
        timeout=10,
    )
    assert create.status_code == 201, create.text
    booking_id = create.json()["booking_id"]

    deadline = time.monotonic() + 25.0
    status = None
    while time.monotonic() < deadline:
        g = requests.get(f"{BOOKING_URL}/bookings/{booking_id}", timeout=5)
        assert g.status_code == 200, g.text
        body = g.json()
        status = body.get("status")
        if status == "confirmed":
            assert body.get("ticket_id")
            return
        time.sleep(0.5)

    pytest.fail(f"booking {booking_id} did not reach confirmed in time, last status={status!r}")
