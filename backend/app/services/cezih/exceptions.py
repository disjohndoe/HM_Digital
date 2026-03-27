from __future__ import annotations


class CezihError(Exception):
    """Base exception for all CEZIH-related errors."""

    def __init__(self, message: str, *, detail: str | None = None) -> None:
        self.message = message
        self.detail = detail
        super().__init__(self.message)


class CezihConnectionError(CezihError):
    """Network/VPN connectivity failure (cannot reach CEZIH servers)."""


class CezihAuthError(CezihError):
    """OAuth2 token acquisition or refresh failure."""


class CezihFhirError(CezihError):
    """FHIR API returned an OperationOutcome error or unexpected response."""

    def __init__(
        self,
        message: str,
        *,
        status_code: int = 0,
        operation_outcome: dict | None = None,
    ) -> None:
        self.status_code = status_code
        self.operation_outcome = operation_outcome
        super().__init__(message, detail=str(operation_outcome) if operation_outcome else None)


class CezihTimeoutError(CezihError):
    """Request to CEZIH timed out."""


class CezihSigningError(CezihError):
    """Remote signing service failure (Certilia cloud cert / certpubws)."""

    def __init__(
        self,
        message: str,
        *,
        signing_service_error: str | None = None,
    ) -> None:
        self.signing_service_error = signing_service_error
        super().__init__(message, detail=signing_service_error)
