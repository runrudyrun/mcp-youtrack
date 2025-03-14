"""Environment configuration for the MCP YouTrack server.

This module handles all environment variable configuration with sensible defaults
and type conversion.
"""

import os
from typing import Optional

from pydantic import BaseModel, Field


class YouTrackConfig(BaseModel):
    """Configuration for the YouTrack connection settings.

    This class provides configuration for connecting to a YouTrack instance.
    """
    
    url: str = Field(..., description="Base URL of the YouTrack instance")
    token: str = Field(..., description="Permanent token for YouTrack API access")
    timeout: Optional[float] = Field(30.0, description="Request timeout in seconds")


class Config:
    """Configuration for the MCP YouTrack server.

    This class handles all environment variable configuration with sensible defaults
    and type conversion. It provides typed methods for accessing each configuration value.

    Required environment variables:
        YOUTRACK_URL: Base URL of the YouTrack instance
        YOUTRACK_TOKEN: Permanent token for YouTrack API access

    Optional environment variables (with defaults):
        YOUTRACK_TIMEOUT: Request timeout in seconds (default: 30.0)
    """

    def __init__(self):
        """Initialize the configuration from environment variables."""
        pass

    @property
    def youtrack_url(self) -> Optional[str]:
        """Get the YouTrack instance URL."""
        return os.getenv("YOUTRACK_URL")

    @property
    def youtrack_token(self) -> Optional[str]:
        """Get the YouTrack API token."""
        return os.getenv("YOUTRACK_TOKEN")

    @property
    def youtrack_timeout(self) -> float:
        """Get the YouTrack API request timeout in seconds.

        Default: 30.0
        """
        return float(os.getenv("YOUTRACK_TIMEOUT", "30.0"))

    def get_youtrack_config(self) -> Optional[YouTrackConfig]:
        """Get the complete YouTrack configuration.
        
        Returns None if required configuration is missing.
        """
        url = self.youtrack_url
        token = self.youtrack_token
        
        if not url or not token:
            return None
            
        return YouTrackConfig(
            url=url,
            token=token,
            timeout=self.youtrack_timeout
        )


# Global instance for easy access
config = Config()
