"""Minimal persistent HTTP client for TypeSafe-compatible System One endpoints.

Research-only. No retries are performed: completion/failure rate is benchmark evidence.
"""
from __future__ import annotations

import http.client
import json
import time
from dataclasses import dataclass
from typing import Any, Mapping
from urllib.parse import urlparse


@dataclass(frozen=True)
class HttpResult:
    payload: Mapping[str, Any]
    latency_ms: float
    status: int
    headers: Mapping[str, str]


class SystemOneHttpError(RuntimeError):
    def __init__(self, status: int, body: str):
        super().__init__(f"System One HTTP {status}: {body[:500]}")
        self.status = status
        self.body = body[:500]


class SystemOneHttpClient:
    def __init__(
        self,
        base_url: str,
        *,
        endpoint: str = "/v1/systemone",
        auth_mode: str = "none",
        api_key: str | None = None,
        timeout_s: float = 60.0,
    ) -> None:
        parsed = urlparse(base_url)
        if parsed.scheme not in {"http", "https"} or not parsed.hostname:
            raise ValueError("base_url must be http(s)://host[:port]")
        if auth_mode not in {"none", "bearer", "x-api-key"}:
            raise ValueError("auth_mode must be none, bearer or x-api-key")
        self._parsed = parsed
        base_path = parsed.path.rstrip("/")
        self.path = f"{base_path}{endpoint}" or endpoint
        self.auth_mode = auth_mode
        self.api_key = api_key
        self.timeout_s = timeout_s
        self._conn: http.client.HTTPConnection | http.client.HTTPSConnection | None = None

    def _connect(self) -> http.client.HTTPConnection | http.client.HTTPSConnection:
        if self._conn is None:
            cls = http.client.HTTPSConnection if self._parsed.scheme == "https" else http.client.HTTPConnection
            self._conn = cls(self._parsed.hostname, self._parsed.port, timeout=self.timeout_s)
        return self._conn

    def close(self) -> None:
        if self._conn is not None:
            self._conn.close()
            self._conn = None

    def request(
        self,
        state: Any,
        questions: Mapping[str, Mapping[str, Any]],
        *,
        model: str | None = None,
        permutations: int | None = None,
    ) -> HttpResult:
        payload: dict[str, Any] = {"state": state, "questions": questions}
        if model:
            payload["model"] = model
        if permutations is not None:
            if permutations < 1:
                raise ValueError("permutations must be >= 1")
            payload["permutations"] = permutations
        body = json.dumps(payload, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
        headers = {"content-type": "application/json", "accept": "application/json"}
        if self.api_key:
            if self.auth_mode == "bearer":
                headers["authorization"] = f"Bearer {self.api_key}"
            elif self.auth_mode == "x-api-key":
                headers["x-api-key"] = self.api_key

        started = time.perf_counter()
        try:
            conn = self._connect()
            conn.request("POST", self.path, body=body, headers=headers)
            response = conn.getresponse()
            raw = response.read()
        except (ConnectionError, OSError, http.client.HTTPException):
            self.close()
            raise
        latency_ms = (time.perf_counter() - started) * 1000.0
        response_headers = {k.lower(): v for k, v in response.getheaders()}
        text = raw.decode("utf-8", errors="replace")
        if response.status < 200 or response.status >= 300:
            raise SystemOneHttpError(response.status, text)
        parsed = json.loads(text)
        if not isinstance(parsed, Mapping):
            raise ValueError("System One response must be a JSON object")
        return HttpResult(parsed, latency_ms, response.status, response_headers)

    def __enter__(self) -> "SystemOneHttpClient":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()
