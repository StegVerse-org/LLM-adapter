"""Durable queue for Service Gateway forwards whose same-host receiver is not live.

Existing owner: LLMA-DECLARED-PATH-CONFORMANCE-368.

The Task Registry global invariants make destination liveness a non-predicate:
destination existence is sufficient for ingress and egress, no external machine
is awaited, and an unavailable receiver is answered by a durable queue or an
event-triggered ephemeral materialization. The transport-only gateway forwards
(evaluator, SV002 observation, InTr source package and device KV result, HIL
receiver projection) used to answer an unreachable receiver with 503. They now
queue the exact admitted bytes here and answer 202 QUEUED with a forward id.

The queue is drained, never awaited: once at service startup
(`python -m llm_adapter.gateway_forward_queue`, beside the custody worker) and
on the next event that reaches a live receiver of the same gateway. A receiver
that answers, with any HTTP status, has answered; that answer is kept and can be
read back from `GET /intr/forward-queue/{forward_id}`. Nothing here interprets
a receiver's answer, mints a receipt, or carries authority. Standard library
only.
"""
from __future__ import annotations

import base64
import hashlib
import json
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from threading import RLock
from typing import Any, Callable
from urllib import error as urlerror
from urllib import request as urlrequest

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

OWNING_EXISTING_GOAL = "LLMA-DECLARED-PATH-CONFORMANCE-368"
QUEUED_SCHEMA = "stegverse.gateway-forward-queued/v1"
STATUS_SCHEMA = "stegverse.gateway-forward-status/v1"
DB_ENV = "STEGVERSE_GATEWAY_FORWARD_DB"
DEFAULT_PATH = "/tmp/stegverse-gateway-forward.db"
MAX_RESPONSE_BYTES = 16 * 1024 * 1024
EVENT_DRAIN_LIMIT = 5

router = APIRouter()
_lock = RLock()


class ReceiverUnavailable(Exception):
    """The same-host receiver could not be reached; the forward is queued, not refused."""

    def __init__(self, cause: BaseException) -> None:
        super().__init__(f"{type(cause).__name__}")
        self.error_class = type(cause).__name__


def _path() -> str:
    return os.getenv(DB_ENV, "").strip() or DEFAULT_PATH


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _connect() -> sqlite3.Connection:
    path = _path()
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path, timeout=10)
    connection.row_factory = sqlite3.Row
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS gateway_forwards (
            forward_id TEXT PRIMARY KEY,
            gateway TEXT NOT NULL,
            target TEXT NOT NULL,
            headers_json TEXT,
            body BLOB,
            state TEXT NOT NULL,
            attempts INTEGER NOT NULL DEFAULT 0,
            last_error TEXT,
            response_status INTEGER,
            response_content_type TEXT,
            response_body BLOB,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """
    )
    return connection


def forward_id(gateway: str, target: str, body: bytes, headers: dict[str, str]) -> str:
    """Identity of one forward: the exact gateway, target, headers and bytes."""
    material = json.dumps(
        {"gateway": gateway, "target": target, "headers": dict(sorted(headers.items())),
         "body_sha256": hashlib.sha256(body).hexdigest()},
        sort_keys=True, separators=(",", ":"),
    ).encode("utf-8")
    return "fwd-" + hashlib.sha256(material).hexdigest()


def enqueue(gateway: str, target: str, body: bytes, headers: dict[str, str], *, error: str) -> str:
    """Queue one forward. Re-queueing the same forward is idempotent."""
    identity = forward_id(gateway, target, body, headers)
    now = _now()
    with _lock, _connect() as connection:
        connection.execute(
            """
            INSERT INTO gateway_forwards(forward_id, gateway, target, headers_json, body, state,
                                         attempts, last_error, created_at, updated_at)
            VALUES(?,?,?,?,?,'QUEUED',1,?,?,?)
            ON CONFLICT(forward_id) DO UPDATE SET
                attempts=gateway_forwards.attempts + 1,
                last_error=excluded.last_error,
                updated_at=excluded.updated_at
            WHERE gateway_forwards.state != 'FORWARDED'
            """,
            (identity, gateway, target, json.dumps(headers, sort_keys=True), body, error, now, now),
        )
    return identity


def queued_response(gateway: str, target: str, body: bytes, headers: dict[str, str],
                    unavailable: ReceiverUnavailable) -> JSONResponse:
    """Queue the forward and answer 202 QUEUED instead of refusing on liveness."""
    identity = enqueue(gateway, target, body, headers, error=unavailable.error_class)
    return JSONResponse(
        status_code=202,
        headers={"Cache-Control": "no-store"},
        content={
            "schema": QUEUED_SCHEMA,
            "state": "QUEUED",
            "forward_id": identity,
            "gateway": gateway,
            "status_path": f"/intr/forward-queue/{identity}",
            "receiver_state": "NOT_OBSERVED",
            "error_class": unavailable.error_class,
            "receiver_unavailable_disposition": "DURABLE_QUEUE",
            "destination_liveness_is_transition_predicate": False,
            "external_machine_awaited": False,
            "drained_by": ["service startup: python -m llm_adapter.gateway_forward_queue",
                           "next event reaching a live receiver of this gateway"],
            "gateway_receipt_authority": False,
            "owning_existing_goal": OWNING_EXISTING_GOAL,
            "authority_effect": "NONE_TRANSPORT_ONLY",
        },
    )


def _send(target: str, body: bytes, headers: dict[str, str]) -> tuple[int, bytes, str]:
    req = urlrequest.Request(target, data=body, method="POST")
    for name, value in headers.items():
        req.add_header(name, value)
    try:
        with urlrequest.urlopen(req, timeout=15) as response:
            raw = response.read(MAX_RESPONSE_BYTES + 1)
            if len(raw) > MAX_RESPONSE_BYTES:
                raise ValueError("queued forward response too large")
            return response.status, raw, response.headers.get_content_type()
    except urlerror.HTTPError as exc:
        return exc.code, exc.read(MAX_RESPONSE_BYTES + 1), exc.headers.get_content_type()


def process_pending(*, gateway: str | None = None, limit: int = 20,
                    send: Callable[[str, bytes, dict[str, str]], tuple[int, bytes, str]] | None = None
                    ) -> list[dict[str, Any]]:
    """Deliver queued forwards, oldest first. A failure leaves the forward queued as RETRY."""
    send = send or _send
    query = "SELECT * FROM gateway_forwards WHERE state IN ('QUEUED','RETRY')"
    params: list[Any] = []
    if gateway is not None:
        query += " AND gateway = ?"
        params.append(gateway)
    query += " ORDER BY created_at LIMIT ?"
    params.append(max(0, int(limit)))
    with _lock, _connect() as connection:
        rows = [dict(row) for row in connection.execute(query, params).fetchall()]
    results = []
    for row in rows:
        try:
            status, raw, content_type = send(row["target"], bytes(row["body"] or b""),
                                             json.loads(row["headers_json"] or "{}"))
        except Exception as exc:
            with _lock, _connect() as connection:
                connection.execute(
                    "UPDATE gateway_forwards SET state='RETRY', attempts=attempts+1, last_error=?, updated_at=? WHERE forward_id=?",
                    (type(exc).__name__, _now(), row["forward_id"]),
                )
            results.append({"forward_id": row["forward_id"], "state": "RETRY", "error_class": type(exc).__name__})
            continue
        with _lock, _connect() as connection:
            # The receiver answered. The request bytes and headers are no longer needed.
            connection.execute(
                """
                UPDATE gateway_forwards SET state='FORWARDED', attempts=attempts+1, last_error=NULL,
                    headers_json=NULL, body=NULL, response_status=?, response_content_type=?,
                    response_body=?, updated_at=? WHERE forward_id=?
                """,
                (status, content_type, raw, _now(), row["forward_id"]),
            )
        results.append({"forward_id": row["forward_id"], "state": "FORWARDED", "response_status": status})
    return results


def drain_after_live_event(gateway: str) -> None:
    """A receiver of this gateway just answered: deliver what was queued for it."""
    try:
        process_pending(gateway=gateway, limit=EVENT_DRAIN_LIMIT)
    except Exception:
        # Draining never changes the answer to the event that triggered it.
        pass


def status(identity: str) -> dict[str, Any] | None:
    with _lock, _connect() as connection:
        row = connection.execute(
            "SELECT forward_id, gateway, state, attempts, last_error, response_status, response_content_type, response_body, updated_at "
            "FROM gateway_forwards WHERE forward_id = ?", (identity,),
        ).fetchone()
    if row is None:
        return None
    raw = row["response_body"]
    return {
        "schema": STATUS_SCHEMA,
        "forward_id": row["forward_id"],
        "gateway": row["gateway"],
        "state": row["state"],
        "attempts": row["attempts"],
        "last_error": row["last_error"],
        "receiver_response": None if row["state"] != "FORWARDED" else {
            "status": row["response_status"],
            "content_type": row["response_content_type"],
            "body_base64": base64.b64encode(bytes(raw or b"")).decode("ascii"),
        },
        "updated_at": row["updated_at"],
        "gateway_receipt_authority": False,
        "authority_effect": "NONE_TRANSPORT_ONLY",
    }


@router.get("/intr/forward-queue/{identity}")
def forward_status(identity: str) -> JSONResponse:
    if not identity.startswith("fwd-") or len(identity) != 68:
        raise HTTPException(status_code=400, detail="forward_id_invalid")
    body = status(identity)
    if body is None:
        raise HTTPException(status_code=404, detail="forward_id_not_queued")
    return JSONResponse(content=body, headers={"Cache-Control": "no-store"})


def main() -> int:
    """Drain once and always exit 0: service startup never waits on a receiver."""
    try:
        results = process_pending(limit=100)
        report = {"worker": "gateway_forward_queue", "processed": len(results),
                  "forwarded": sum(1 for item in results if item["state"] == "FORWARDED"),
                  "retry": sum(1 for item in results if item["state"] == "RETRY"),
                  "gates_startup": False, "authority_effect": "NONE_TRANSPORT_ONLY"}
    except Exception as exc:
        report = {"worker": "gateway_forward_queue", "disposition": "NOT_DRAINED",
                  "failure_code": f"gateway_forward_queue_drain_failed:{type(exc).__name__}",
                  "failed_predicate": "gateway_forward_queue_drained",
                  "required_evidence_or_repair": f"correct the {DB_ENV} path named by the error",
                  "retry_entrypoint": "python -m llm_adapter.gateway_forward_queue",
                  "owning_existing_goal": OWNING_EXISTING_GOAL,
                  "next_attempt": "rerun the drain; queued forwards stay queued",
                  "gates_startup": False, "authority_effect": "NONE_TRANSPORT_ONLY"}
    print(json.dumps(report, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
