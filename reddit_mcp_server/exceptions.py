class RedditMCPError(Exception):
    pass

class AuthenticationError(RedditMCPError):
    pass

class RateLimitError(RedditMCPError):
    def __init__(self, retry_after: float = 30.0):
        self.retry_after = retry_after
        super().__init__(f"Rate limited. Retry after {retry_after}s")

class SessionExpiredError(AuthenticationError):
    pass

class ToolError(RedditMCPError):
    pass
