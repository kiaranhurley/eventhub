"""bandit on web-frontend only so random HIGHs elsewhere don't flake"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.security
def test_bandit_scan_on_web_frontend_no_high_severity():
    cmd = [
        sys.executable,
        "-m",
        "bandit",
        "-r",
        str(_ROOT / "services" / "web-frontend"),
        "-ll",
        "-f",
        "json",
        "-q",
    ]
    proc = subprocess.run(cmd, cwd=str(_ROOT), capture_output=True, text=True, timeout=120)
    raw = proc.stdout or proc.stderr or "{}"
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        pytest.fail(f"bandit did not emit JSON: exit={proc.returncode} stderr={proc.stderr!r}")

    highs = [i for i in data.get("results", []) if i.get("issue_severity") == "HIGH"]
    assert not highs, f"HIGH severity issues: {highs[:3]}"
