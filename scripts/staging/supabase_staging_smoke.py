#!/usr/bin/env python3
"""
Supabase staging smoke — real Auth tokens only.

Verifies against a running API + non-production Supabase staging project:

  1. User A password login (Supabase Auth)
  2. User A Venture / Project / Task / Person CRUD
  3. User B cannot list / read / update / delete User A objects

No fake JWTs. No invented secrets. Skips (exit 2) when required env is missing.
Never run against production.

Required env (placeholders must be replaced privately):

  SUPABASE_URL or NEXT_PUBLIC_SUPABASE_URL
  NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY or NEXT_PUBLIC_SUPABASE_ANON_KEY
  NEXT_PUBLIC_API_BASE_URL (or STAGING_API_BASE_URL) — must include /api/v1
  E2E_EMAIL / E2E_PASSWORD
  E2E_EMAIL_B / E2E_PASSWORD_B

Optional: load apps/web/.env.local and apps/web/e2e/.env.local if present.
"""

from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

ROOT = Path(__file__).resolve().parents[2]


def _load_env_file(path: Path) -> None:
    if not path.is_file():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and (os.environ.get(key) in (None, "")):
            os.environ[key] = value


def _require(name: str) -> str:
    value = (os.environ.get(name) or "").strip()
    if not value:
        raise SystemExit(f"BLOCKED: missing required env {name} (secrets were not invented).")
    return value


def _looks_like_production(*values: str) -> bool:
    markers = ("prod", "production", "live")
    for value in values:
        lowered = value.lower()
        if any(marker in lowered for marker in markers):
            return True
    return False


def _http(
    method: str,
    url: str,
    *,
    headers: Optional[Dict[str, str]] = None,
    body: Optional[Dict[str, Any]] = None,
    timeout: float = 60.0,
) -> Tuple[int, Any, Dict[str, str]]:
    data = None
    req_headers = {"Accept": "application/json", **(headers or {})}
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        req_headers["Content-Type"] = "application/json"
    request = urllib.request.Request(url, data=data, headers=req_headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read().decode("utf-8") if response.length != 0 else ""
            parsed: Any = None
            if raw:
                try:
                    parsed = json.loads(raw)
                except json.JSONDecodeError:
                    parsed = raw
            return response.status, parsed, dict(response.headers)
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8")
        parsed = None
        if raw:
            try:
                parsed = json.loads(raw)
            except json.JSONDecodeError:
                parsed = raw
        return exc.code, parsed, dict(exc.headers)


def _supabase_password_login(supabase_url: str, anon_key: str, email: str, password: str) -> str:
    token_url = f"{supabase_url.rstrip('/')}/auth/v1/token?grant_type=password"
    status, payload, _ = _http(
        "POST",
        token_url,
        headers={"apikey": anon_key, "Authorization": f"Bearer {anon_key}"},
        body={"email": email, "password": password},
    )
    if status != 200 or not isinstance(payload, dict) or not payload.get("access_token"):
        raise SystemExit(
            f"FAIL: Supabase Auth login failed for {email!r} "
            f"(HTTP {status}). Confirm staging Auth user exists and email is confirmed."
        )
    return str(payload["access_token"])


def _api(
    method: str,
    base: str,
    path: str,
    token: str,
    body: Optional[Dict[str, Any]] = None,
) -> Tuple[int, Any]:
    status, payload, _ = _http(
        method,
        f"{base.rstrip('/')}{path}",
        headers={"Authorization": f"Bearer {token}"},
        body=body,
    )
    return status, payload


def _ids_from_list(payload: Any) -> List[str]:
    if not isinstance(payload, dict):
        return []
    items = payload.get("items") or payload.get("data") or []
    if not isinstance(items, list):
        return []
    out: List[str] = []
    for item in items:
        if isinstance(item, dict) and item.get("id") is not None:
            out.append(str(item["id"]))
    return out


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"FAIL: {message}")


def _deny_cross_tenant(
    label: str,
    base: str,
    collection: str,
    resource_id: str,
    token_b: str,
    update_body: Dict[str, Any],
) -> None:
    list_status, list_payload = _api("GET", base, f"/{collection}", token_b)
    _assert(list_status == 200, f"User B {label} list expected 200, got {list_status}")
    _assert(
        resource_id not in _ids_from_list(list_payload),
        f"User B listed User A {label} {resource_id}",
    )

    get_status, _ = _api("GET", base, f"/{collection}/{resource_id}", token_b)
    _assert(
        get_status in {403, 404},
        f"User B read User A {label}: expected 403/404, got {get_status}",
    )

    patch_status, _ = _api(
        "PATCH", base, f"/{collection}/{resource_id}", token_b, body=update_body
    )
    _assert(
        patch_status in {403, 404},
        f"User B update User A {label}: expected 403/404, got {patch_status}",
    )

    delete_status, _ = _api("DELETE", base, f"/{collection}/{resource_id}", token_b)
    _assert(
        delete_status in {403, 404},
        f"User B delete User A {label}: expected 403/404, got {delete_status}",
    )


def main() -> int:
    _load_env_file(ROOT / "apps" / "web" / ".env.local")
    _load_env_file(ROOT / "apps" / "web" / "e2e" / ".env.local")
    _load_env_file(ROOT / "apps" / "api" / ".env")

    app_env = (os.environ.get("APP_ENV") or os.environ.get("ENVIRONMENT") or "").strip().lower()
    next_env = (os.environ.get("NEXT_PUBLIC_APP_ENV") or "").strip().lower()
    if app_env == "production" or next_env == "production":
        raise SystemExit("REFUSED: APP_ENV/ENVIRONMENT/NEXT_PUBLIC_APP_ENV is production.")

    supabase_url = (
        os.environ.get("SUPABASE_URL") or os.environ.get("NEXT_PUBLIC_SUPABASE_URL") or ""
    ).strip()
    anon_key = (
        os.environ.get("NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY")
        or os.environ.get("NEXT_PUBLIC_SUPABASE_ANON_KEY")
        or ""
    ).strip()
    api_base = (
        os.environ.get("STAGING_API_BASE_URL") or os.environ.get("NEXT_PUBLIC_API_BASE_URL") or ""
    ).strip()

    missing = [
        name
        for name, value in (
            ("SUPABASE_URL|NEXT_PUBLIC_SUPABASE_URL", supabase_url),
            (
                "NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY|NEXT_PUBLIC_SUPABASE_ANON_KEY",
                anon_key,
            ),
            ("STAGING_API_BASE_URL|NEXT_PUBLIC_API_BASE_URL", api_base),
            ("E2E_EMAIL", os.environ.get("E2E_EMAIL")),
            ("E2E_PASSWORD", os.environ.get("E2E_PASSWORD")),
            ("E2E_EMAIL_B", os.environ.get("E2E_EMAIL_B")),
            ("E2E_PASSWORD_B", os.environ.get("E2E_PASSWORD_B")),
        )
        if not (value or "").strip()
    ]
    if missing:
        print("SUPABASE STAGING SMOKE = BLOCKED")
        print("Missing env (not invented): " + ", ".join(missing))
        return 2

    if _looks_like_production(supabase_url, api_base, app_env, next_env):
        raise SystemExit(
            "REFUSED: URL/env appears production-related. Use a dedicated staging project."
        )

    email_a = _require("E2E_EMAIL")
    password_a = _require("E2E_PASSWORD")
    email_b = _require("E2E_EMAIL_B")
    password_b = _require("E2E_PASSWORD_B")

    stamp = int(time.time())
    print("== staging smoke: Auth ==")
    token_a = _supabase_password_login(supabase_url, anon_key, email_a, password_a)
    token_b = _supabase_password_login(supabase_url, anon_key, email_b, password_b)
    print("PASS: User A and User B obtained real Supabase access tokens")

    created: List[Tuple[str, str]] = []

    try:
        print("== staging smoke: User A Venture CRUD ==")
        status, venture = _api(
            "POST",
            api_base,
            "/ventures",
            token_a,
            body={"name": f"Staging Smoke Venture {stamp}", "description": "staging-smoke"},
        )
        _assert(status == 201 and isinstance(venture, dict), f"create venture HTTP {status}")
        venture_id = str(venture["id"])
        created.append(("ventures", venture_id))

        status, got = _api("GET", api_base, f"/ventures/{venture_id}", token_a)
        _assert(status == 200 and isinstance(got, dict) and str(got["id"]) == venture_id, "read venture")

        status, updated = _api(
            "PATCH",
            api_base,
            f"/ventures/{venture_id}",
            token_a,
            body={"description": "staging-smoke-updated"},
        )
        _assert(status == 200 and isinstance(updated, dict), f"update venture HTTP {status}")

        status, listed = _api("GET", api_base, "/ventures", token_a)
        _assert(status == 200 and venture_id in _ids_from_list(listed), "list ventures includes create")
        print(f"PASS: Venture CRUD ({venture_id})")

        print("== staging smoke: User A Project CRUD ==")
        status, project = _api(
            "POST",
            api_base,
            "/projects",
            token_a,
            body={
                "name": f"Staging Smoke Project {stamp}",
                "venture_id": venture_id,
                "description": "staging-smoke",
            },
        )
        _assert(status == 201 and isinstance(project, dict), f"create project HTTP {status}")
        project_id = str(project["id"])
        created.append(("projects", project_id))

        status, _ = _api("GET", api_base, f"/projects/{project_id}", token_a)
        _assert(status == 200, "read project")
        status, _ = _api(
            "PATCH",
            api_base,
            f"/projects/{project_id}",
            token_a,
            body={"description": "staging-smoke-updated"},
        )
        _assert(status == 200, "update project")
        status, listed = _api("GET", api_base, "/projects", token_a)
        _assert(status == 200 and project_id in _ids_from_list(listed), "list projects")
        print(f"PASS: Project CRUD ({project_id})")

        print("== staging smoke: User A Task CRUD ==")
        status, task = _api(
            "POST",
            api_base,
            "/tasks",
            token_a,
            body={
                "title": f"Staging Smoke Task {stamp}",
                "venture_id": venture_id,
                "project_id": project_id,
                "description": "staging-smoke",
            },
        )
        _assert(status == 201 and isinstance(task, dict), f"create task HTTP {status}")
        task_id = str(task["id"])
        created.append(("tasks", task_id))

        status, _ = _api("GET", api_base, f"/tasks/{task_id}", token_a)
        _assert(status == 200, "read task")
        status, _ = _api(
            "PATCH",
            api_base,
            f"/tasks/{task_id}",
            token_a,
            body={"description": "staging-smoke-updated"},
        )
        _assert(status == 200, "update task")
        status, listed = _api("GET", api_base, "/tasks", token_a)
        _assert(status == 200 and task_id in _ids_from_list(listed), "list tasks")
        print(f"PASS: Task CRUD ({task_id})")

        print("== staging smoke: User A Person CRUD ==")
        status, person = _api(
            "POST",
            api_base,
            "/people",
            token_a,
            body={"name": f"Staging Smoke Person {stamp}", "relationship_type": "contact"},
        )
        _assert(status == 201 and isinstance(person, dict), f"create person HTTP {status}")
        person_id = str(person["id"])
        created.append(("people", person_id))

        status, _ = _api("GET", api_base, f"/people/{person_id}", token_a)
        _assert(status == 200, "read person")
        status, _ = _api(
            "PATCH",
            api_base,
            f"/people/{person_id}",
            token_a,
            body={"notes": "staging-smoke-updated"},
        )
        _assert(status == 200, "update person")
        status, listed = _api("GET", api_base, "/people", token_a)
        _assert(status == 200 and person_id in _ids_from_list(listed), "list people")
        print(f"PASS: Person CRUD ({person_id})")

        print("== staging smoke: User B isolation ==")
        _deny_cross_tenant(
            "venture",
            api_base,
            "ventures",
            venture_id,
            token_b,
            {"description": "stolen"},
        )
        _deny_cross_tenant(
            "project",
            api_base,
            "projects",
            project_id,
            token_b,
            {"description": "stolen"},
        )
        _deny_cross_tenant(
            "task",
            api_base,
            "tasks",
            task_id,
            token_b,
            {"description": "stolen"},
        )
        _deny_cross_tenant(
            "person",
            api_base,
            "people",
            person_id,
            token_b,
            {"notes": "stolen"},
        )
        print("PASS: User B cannot list/read/update/delete User A objects")

        # Owner delete (cleanup as part of CRUD D)
        for collection, resource_id in list(reversed(created)):
            status, _ = _api("DELETE", api_base, f"/{collection}/{resource_id}", token_a)
            _assert(status in {200, 204}, f"User A delete {collection}/{resource_id} HTTP {status}")
            created.remove((collection, resource_id))
        print("PASS: User A delete cleanup")

    finally:
        for collection, resource_id in reversed(created):
            try:
                _api("DELETE", api_base, f"/{collection}/{resource_id}", token_a)
            except Exception:
                pass

    print("SUPABASE STAGING SMOKE = PASS")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        raise SystemExit(130)
