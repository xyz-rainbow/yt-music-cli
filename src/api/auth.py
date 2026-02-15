import logging
from typing import Optional, Dict
from ytmusicapi import YTMusic

class AuthManager:
    def __init__(self):
        self._api: Optional[YTMusic] = None
        self.logger = logging.getLogger(__name__)

    @property
    def api(self) -> YTMusic:
        """Returns the authenticated YTMusic instance, initializing it if necessary."""
        if self._api is None:
            self.login_guest()
        return self._api

    def is_authenticated(self) -> bool:
        """Always True in Guest Mode (we are 'authenticated' as guest)."""
        return self._api is not None

    def login_guest(self) -> None:
        """Initialize valid public API for guest usage."""
        self._api = YTMusic() # No auth works for public search/radio

    def logout(self):
        self._api = None

    def get_user_info(self) -> Dict:
        return {"name": "Guest User", "accountName": "No Account"}
