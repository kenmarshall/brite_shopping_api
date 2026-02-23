from app.db import db
from app.services.logger_service import logger


def get_hidden_store_ids() -> set[str]:
    """Return the set of store_ids that are marked as hidden in store_settings."""
    try:
        docs = db.store_settings.find({"visible": False}, {"store_id": 1})
        return {doc["store_id"] for doc in docs}
    except Exception as e:
        logger.warning(f"Failed to load store visibility settings: {e}")
        return set()
