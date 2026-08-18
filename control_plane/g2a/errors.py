from __future__ import annotations


class G2AError(Exception):
    """Safe, structured G2-A failure that never carries sensitive detail."""

    def __init__(self, code: str, status: str):
        self.code = code
        self.status = status
        super().__init__(code)


class RefusedError(G2AError):
    def __init__(self, code: str):
        super().__init__(code, "REFUSED")


class NotFoundError(G2AError):
    def __init__(self, code: str):
        super().__init__(code, "NOT_FOUND")


class OperationTimeout(G2AError):
    def __init__(self, code: str = "operation_timeout"):
        super().__init__(code, "TIMEOUT")
