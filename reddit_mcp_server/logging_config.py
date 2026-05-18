import logging
import os

def setup_logging():
    level = os.environ.get("REDDIT_MCP_LOG_LEVEL", "INFO").upper()
    logging.basicConfig(level=getattr(logging, level, logging.INFO), format="%(asctime)s [%(name)s] %(levelname)s: %(message)s")
    return logging.getLogger("reddit_mcp")

logger = setup_logging()
