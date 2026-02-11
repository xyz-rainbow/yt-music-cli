from src.api.auth import AuthManager
from typing import List, Dict, Any

class YTMusicClient:
    def __init__(self):
        self.auth = AuthManager()
        # Ensure we have the latest api instance
        if not self.auth.api:
            self.auth.login()
        self.api = self.auth.api

    def search_songs(self, query: str) -> List[Dict[str, Any]]:
        """Search for songs."""
        if not self.api:
            return []
        
        try:
            results = self.api.search(query, filter="songs")
            return results
        except Exception as e:
            print(f"Search error: {e}")
            return []

    def get_library_songs(self) -> List[Dict[str, Any]]:
        """Get user's library songs."""
        if not self.api:
             return []
        # basic implementation
        return self.api.get_library_songs()
