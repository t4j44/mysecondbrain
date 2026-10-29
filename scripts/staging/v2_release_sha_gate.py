#!/usr/bin/env python3
"""Fail-closed public staging API revision gate. Does not authenticate or write data.

Usage:
  python scripts/staging/v2_release_sha_gate.py \
    --url https://second-brain-api-staging.onrender.com \
    --expected-sha <40-char-commit-sha>

For an assembled V2 candidate, this only checks API provenance and health.
It is NOT evidence of matching web/worker/database, user isolation, or provider acceptance.
"""

import argparse
import json
import re
import urllib.error
import urllib.parse
import urllib.request

SHA = re.compile(r"^[0-9a-f]{40}$")


class ReleaseGateError(Exception):
    """Human-safe release blocker (never include response bodies or credentials)."""


def verify_api_release(origin: str, expected_sha: str) -> dict:
    expected_sha = expected_sha.strip().lower()
    if not SHA.fullmatch(expected_sha):
        raise ReleaseGateError("Expected commit SHA must be exactly 40 hexadecimal characters.")

    parsed = urllib.parse.urlsplit(origin.strip())
    if (parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password
            or parsed.query or parsed.fragment or parsed.path not in ("", "/")):
        raise ReleaseGateError("Provide a bare HTTPS staging API origin without credentials or query parameters.")

    request = urllib.request.Request(origin.rstrip("/") + "/health",
                                     headers={"Accept": "application/json",
                                              "User-Agent": "SecondBrain-V2-ReleaseGate/1.0"})
    # Never follow a redirect to a different host or unapproved deployment.\n    class NoRedirect(urllib.request.HTTPRedirectHandler):\n        def redirect_request(self, request, fp, code, msg, headers, newurl):\n            return None\n\n    opener = urllib.request.build_opener(NoRedirect())
    try:
        with opener.open(request, timeout=15) as response:
            if response.status != 200:
                raise ReleaseGateError("Hosted API health endpoint did not return HTTP 200.")
            raw = response.read(16385)
            if len(raw) > 16384:
                raise ReleaseGateError("Health response exceeded size limit.")
            payload = json.loads(raw)
    except (urllib.error.URLError, TimeoutError, OSError, ValueError, json.JSONDecodeError) as exc:
        raise ReleaseGateError(f"Could not verify staging API health ({type(exc).__name__}).") from None

    if not isinstance(payload, dict) or payload.get("status") != "healthy":
        raise ReleaseGateError("Hosted API is not reporting a healthy state.")

    reported = payload.get("release_sha")
    if not isinstance(reported, str) or not SHA.fullmatch(reported.lower()):
        raise ReleaseGateError("Hosted API did not report a verifiable commit SHA.")
    if reported.lower() != expected_sha:
        raise ReleaseGateError("Hosted API commit differs from the approved V2 release commit.")

    return {"status": "PASS", "api_commit": expected_sha, "source": "/health",
            "scope": "API release provenance only; not full staging acceptance."}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", required=True, help="Bare HTTPS staging API origin")
    parser.add_argument("--expected-sha", required=True, help="Approved Git commit (40 hex)")
    args = parser.parse_args()
    try:
        print(json.dumps(verify_api_release(args.url, args.expected_sha), sort_keys=True))
        return 0
    except ReleaseGateError as error:
        print(f"NO-GO: {error}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
