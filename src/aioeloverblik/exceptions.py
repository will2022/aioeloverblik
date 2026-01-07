class EloverblikError(Exception):
    """Base exception for Eloverblik API errors."""

    def __init__(self, message: str, error_code: int = None, response_text: str = None):
        super().__init__(message)
        self.error_code = error_code
        self.response_text = response_text


class AuthenticationError(EloverblikError):
    """Raised when authentication fails (invalid token, expired, etc.)."""

    pass


class RateLimitError(EloverblikError):
    """Raised when API rate limit is exceeded (HTTP 429)."""

    pass


class ServerError(EloverblikError):
    """Raised when Eloverblik servers are experiencing issues (HTTP 500/503)."""

    pass
