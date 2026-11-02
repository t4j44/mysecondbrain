#!/usr/bin/env python3
"""Read-only live staging check: anonymous callers cannot read V2 private tables.

This does NOT demonstrate signed-in isolation or backup recovery.
The key is a Supabase *public publishable key*, not a secret/service-role key.
"""
from __future__ import annotations

import json
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

BASE = "https://rpkjmdrralzxhdsgceal.supabase.co"
WORKFLOW = Path(__file__).resolve().parents[2] / ".github/workflows/beta-e2e.yml"
TABLES = {
    "assistant_preferences": "user_id",
    "messaging_connections": "id",
    "messaging_update_receipts": "update_id",
    "commitment_actions": "id",
    "notification_outbox": "id",
    "notification_delivery_attempts": "id",
    "messaging_callback_tokens": "id",
}


def publishable_key() -> str:
    source = WORKFLOW.read_text(encoding="utf-8")
    match = re.search(r"^\s*NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY:\s*(sb_publishable_[A-Za-z0-9_-]+)\s*$",
                      source, re.MULTILINE)
    if not match:
        raise RuntimeError("Public staging key is missing from the closed-beta workflow.")
    return match.group(1)


def request_status(path: str, key: str) -> tuple[int, bytes]:
    req = urllib.request.Request(
        BASE + path,
        headers={"apikey": key, "Accept": "application/json",
                 "User-Agent": "SecondBrain-Staging-Anonymous-RLS/1.0"},
    )

    class RejectRedirects(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, request, fp, code, msg, headers, newurl):
            return None

    opener = urllib.request.build_opener(RejectRedirects())
    try:
        with opener.open(req, timeout=18) as res:
            return res.status, res.read(8193)
    except urllib.error.HTTPError as error:
        # No response payloads or remote records are recorded in CI logs.
        return error.code, b""


def run() -> int:
    key = publishable_key()
    failures: list[str] = []
    for table in TABLES:
        try:
            status, body = request_status(f"/rest/v1/{table}?select={TABLES[table]}&limit=1", key)
            if status in (401, 403):
                print(f"PASS {table}: anonymous read denied (HTTP {status})")
            elif status == 200:
                if len(body) >= 8193:
                    raise ValueError("Oversized response")
                data = json.loads(body)
                if data != []:
                    raise ValueError("Anonymous database access returned rows or an unexpected shape")
                print(f"PASS {table}: anonymous query returned empty result under RLS")
            else:
                raise ValueError(f"Unexpected HTTP status {status}")
        except (ValueError, urllib.error.URLError, TimeoutError, OSError) as error:
            # Never include response bodies, keys, or unexpected remote content.
            print(f"FAIL {table}: {type(error).__name__}")
            failures.append(table)

    for label, path in (
        ("auth user without token", "/auth/v1/user"),
        ("account-active RPC anonymously", "/rest/v1/rpc/account_active"),
    ):
        try:
            status, _ = request_status(path, key)
            if status not in (401, 403, 404, 405):
                raise ValueError("Unexpected anonymous access response")
            print(f"PASS {label}: HTTP {status} (not an authenticated journey)")
        except (ValueError, urllib.error.URLError, TimeoutError, OSError) as error:
            print(f"FAIL {label}: {type(error).__name__}")
            failures.append(label)

    if failures:
        print("NO-GO: Anonymous RLS smoke failed. No account sign-in or customer data was used.")
        return 1
    print("PASS: seven V2 tables deny anonymous reads. This is NOT two-account tenant proof.")
    return 0


if __name__ == "__main__":
    sys.exit(run())
