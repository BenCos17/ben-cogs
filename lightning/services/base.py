"""Base service class for lightning APIs."""
from abc import ABC, abstractmethod
import aiohttp


class LightningService(ABC):
    """Base class for lightning tracking services."""

    def __init__(self):
        self.session = None

    async def get_session(self):
        """Get or create aiohttp session."""
        if not self.session:
            self.session = aiohttp.ClientSession()
        return self.session

    @abstractmethod
    async def fetch(self, lat: float, lon: float, **kwargs) -> dict:
        """Fetch lightning data from the service."""
        pass

    @abstractmethod
    def format_display_name(self) -> str:
        """Return the display name of this service."""
        pass
