"""Minimal ASGI client so HTTP-level tests need no extra dependency (no httpx)"""

import asyncio
import json
from typing import Any

BOUNDARY = "testboundary"


def _call(app, scope: dict, body: bytes) -> tuple[int, Any]:
    sent = False
    out: dict[str, Any] = {"status": 0, "body": b""}

    async def receive():
        nonlocal sent
        if not sent:
            sent = True
            return {"type": "http.request", "body": body, "more_body": False}
        return {"type": "http.disconnect"}

    async def send(message):
        if message["type"] == "http.response.start":
            out["status"] = message["status"]
        elif message["type"] == "http.response.body":
            out["body"] += message.get("body", b"")

    asyncio.run(app(scope, receive, send))
    try:
        return out["status"], json.loads(out["body"])
    except ValueError:
        return out["status"], out["body"].decode(errors="replace")


def _scope(method: str, path: str, query: str, headers: list[tuple[bytes, bytes]]) -> dict:
    return {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": method,
        "path": path,
        "raw_path": path.encode(),
        "query_string": query.encode(),
        "headers": headers,
        "scheme": "http",
        "server": ("test", 80),
        "client": ("test", 1),
        "root_path": "",
    }


def get(app, path: str, query: str = ""):
    return _call(app, _scope("GET", path, query, []), b"")


def upload(app, filename: str, content: bytes, fields: dict[str, str] | None = None):
    parts = []
    for key, value in (fields or {}).items():
        parts.append(f'--{BOUNDARY}\r\nContent-Disposition: form-data; name="{key}"\r\n\r\n{value}\r\n'.encode())
    parts.append(
        f'--{BOUNDARY}\r\nContent-Disposition: form-data; name="file"; filename="{filename}"\r\n'
        "Content-Type: application/octet-stream\r\n\r\n".encode()
        + content
        + b"\r\n"
    )
    body = b"".join(parts) + f"--{BOUNDARY}--\r\n".encode()
    headers = [
        (b"content-type", f"multipart/form-data; boundary={BOUNDARY}".encode()),
        (b"content-length", str(len(body)).encode()),
    ]
    return _call(app, _scope("POST", "/upload-bloodwork", "", headers), body)
