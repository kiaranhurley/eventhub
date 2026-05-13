"""real redis — skips if nothing listening"""

from __future__ import annotations

import os
import uuid

import pytest

redis = pytest.importorskip("redis")


def _client():
    url = os.environ.get("REDIS_TEST_URL", "redis://127.0.0.1:6379/15")
    return redis.from_url(url, decode_responses=True)


@pytest.mark.integration
def test_redis_incr_decr_roundtrip():
    r = _client()
    try:
        r.ping()
    except redis.exceptions.ConnectionError:
        pytest.skip("redis not up (check REDIS_TEST_URL)")

    key = f"pytest:eventhub:{uuid.uuid4()}:available"
    r.delete(key)
    r.set(key, 2)
    assert int(r.decr(key)) == 1
    assert int(r.decr(key)) == 0
    assert int(r.decr(key)) == -1
    r.incr(key)
    assert int(r.get(key)) == 0
    r.delete(key)


@pytest.mark.integration
def test_booking_style_key_roundtrip():
    r = _client()
    try:
        r.ping()
    except redis.exceptions.ConnectionError:
        pytest.skip("redis not up")

    bid = str(uuid.uuid4())
    key = f"pytest:booking:{bid}"
    r.delete(key)
    payload = '{"id":"%s","status":"held"}' % bid
    r.set(key, payload)
    assert r.get(key) == payload
    r.delete(key)
