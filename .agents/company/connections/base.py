"""Tiny standard-library transport shared by HTTP Connections."""

import json
from dataclasses import dataclass, field
from urllib.request import Request, urlopen


@dataclass(frozen=True)
class ConnectionResult:
    ok: bool
    connection_id: str
    operation: str
    data: dict = field(default_factory=dict)
    error: str | None = None


def json_request(url, *, token, body, method="POST", headers=None, timeout=30):
    request = Request(url, data=json.dumps(body).encode(), method=method,
                      headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json",
                               **(headers or {})})
    with urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode())
