import logging
import ssl
import os
from typing import Any, Optional

# Fix SSL certificate verification on macOS
try:
    import certifi
    os.environ['SSL_CERT_FILE'] = certifi.where()
    os.environ['REQUESTS_CA_BUNDLE'] = certifi.where()
except ImportError:
    pass

from growthbook import GrowthBook

from config import settings

logger = logging.getLogger(__name__)


class FeatureFlagService:
    """GrowthBook feature flag service wrapper."""

    def __init__(self):
        self._enabled = bool(settings.growthbook_client_key)
        if not self._enabled:
            logger.warning("GrowthBook client key not configured - feature flags disabled")

    def _get_gb(self, user_id: int = None) -> GrowthBook:
        """Get GrowthBook instance with optional user context."""
        attributes = {}
        if user_id:
            attributes["id"] = str(user_id)

        return GrowthBook(
            api_host=settings.growthbook_api_host,
            client_key=settings.growthbook_client_key,
            attributes=attributes
        )

    def is_enabled(self, feature_key: str, user_id: int = None, default: bool = False) -> bool:
        """
        Check if a feature flag is enabled.

        Args:
            feature_key: The feature flag key from GrowthBook dashboard
            user_id: Optional user ID for per-user targeting
            default: Default value if GrowthBook is not configured

        Returns:
            True if feature is enabled, False otherwise
        """
        if not self._enabled:
            return default

        try:
            gb = self._get_gb(user_id)
            return gb.is_on(feature_key)
        except Exception as e:
            logger.error(f"Error checking feature flag '{feature_key}': {e}")
            return default

    def get_value(self, feature_key: str, default: Any, user_id: int = None) -> Any:
        """
        Get a feature flag value.

        Args:
            feature_key: The feature flag key from GrowthBook dashboard
            default: Default value if flag not found or GrowthBook not configured
            user_id: Optional user ID for per-user targeting

        Returns:
            The feature value or default
        """
        if not self._enabled:
            return default

        try:
            gb = self._get_gb(user_id)
            return gb.get_feature_value(feature_key, default)
        except Exception as e:
            logger.error(f"Error getting feature value '{feature_key}': {e}")
            return default


# Singleton instance
feature_flags = FeatureFlagService()
