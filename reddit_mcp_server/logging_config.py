import logging
import os


def setup_logging():
    level = os.environ.get("REDDIT_MCP_LOG_LEVEL", "INFO").upper()
    logging.basicConfig(
        level=getattr(logging, level, logging.INFO),
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    )
    return logging.getLogger("reddit_mcp")


# ponytail: defer setup_logging() until first attribute access.
# This prevents basicConfig from capturing sys.stderr at import time,
# which matters when cli_main.py replaces stderr with /dev/null in stdio MCP mode.


class _LazyLogger:
    """Proxy that defers setup_logging() until the logger is first used."""

    _logger = None

    def _get(self):
        if _LazyLogger._logger is None:
            _LazyLogger._logger = setup_logging()
        return _LazyLogger._logger

    def __getattr__(self, name):
        return getattr(self._get(), name)


logger = _LazyLogger()
