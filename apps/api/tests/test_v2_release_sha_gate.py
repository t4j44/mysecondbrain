import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / "scripts" / "staging" / "v2_release_sha_gate.py"
spec = importlib.util.spec_from_file_location("v2_release_sha_gate", SOURCE)
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)

EXPECTED = "a" * 40


class FakeResponse:
    status = 200

    def __init__(self, payload):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self, n):
        return json.dumps(self.payload).encode("utf-8")[:n]


def mock_health(monkeypatch, payload):
    class FakeOpener:
        def open(self, request, timeout):
            assert request.full_url == "https://staging.example.test/health"
            assert timeout == 15
            return FakeResponse(payload)
    monkeypatch.setattr(gate.urllib.request, "build_opener", lambda *args: FakeOpener())


def test_sha_gate_accepts_only_matching_reported_release(monkeypatch):
    mock_health(monkeypatch, {"status": "healthy", "release_sha": EXPECTED})
    result = gate.verify_api_release("https://staging.example.test", EXPECTED)
    assert result["status"] == "PASS"
    assert result["api_commit"] == EXPECTED
    assert "API release provenance only" in result["scope"]


@pytest.mark.parametrize("payload", [
    {"status": "healthy", "release_sha": None},
    {"status": "healthy", "release_sha": "b" * 40},
    {"status": "not_ready", "release_sha": EXPECTED},
])
def test_sha_gate_blocks_missing_mismatched_or_unhealthy(monkeypatch, payload):
    mock_health(monkeypatch, payload)
    with pytest.raises(gate.ReleaseGateError):
        gate.verify_api_release("https://staging.example.test", EXPECTED)


@pytest.mark.parametrize("origin", [
    "http://staging.example.test", "https://user:password@staging.example.test",
    "https://staging.example.test/health", "https://staging.example.test?token=secret",
])
def test_sha_gate_rejects_unsafe_origin_without_network(monkeypatch, origin):
    def forbidden(*args):
        raise AssertionError("network must not be called")
    monkeypatch.setattr(gate.urllib.request, "build_opener", forbidden)
    with pytest.raises(gate.ReleaseGateError):
        gate.verify_api_release(origin, EXPECTED)


def test_sha_gate_requires_full_commit_sha():
    with pytest.raises(gate.ReleaseGateError):
        gate.verify_api_release("https://staging.example.test", "abc123")
