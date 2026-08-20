from __future__ import annotations


class G2BError(Exception):
    """A safe public failure that carries only a stable error code."""

    status = "FAILED"

    def __init__(self, code: str):
        super().__init__(code)
        self.code = code


class RefusedError(G2BError):
    status = "REFUSED"


class ConflictError(G2BError):
    status = "CONFLICT"


class TimeoutError(G2BError):
    status = "TIMEOUT"
