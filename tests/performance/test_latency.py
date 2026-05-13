"""rough speed check on POST /bookings"""

from __future__ import annotations

import os
import time

import pytest
import requests

BOOKING_URL = os.environ.get("BOOKING_SERVICE_TEST_URL", "http://127.0.0.1:5000")


@pytest.mark.performance
def test_create_booking_latency_under_two_seconds():
    try:
        requests.get(f"{BOOKING_URL}/healthz", timeout=1.5)
    except requests.RequestException:
        pytest.skip(f"no booking at {BOOKING_URL}")

    t0 = time.monotonic()
    r = requests.post(
        f"{BOOKING_URL}/bookings",
        json={"event_id": "evt-005", "customer_id": "perf-guest"},
        timeout=10,
    )
    elapsed = time.monotonic() - t0
    assert r.status_code in (201, 409)
    assert elapsed < 2.0, f"POST /bookings took {elapsed:.2f}s"
