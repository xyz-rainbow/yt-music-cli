from src.api.auth import AuthManager

class YTMusicClient:
    def __init__(self, auth_manager: AuthManager):
        self.auth_manager = auth_manager

    @property
    def api(self):
        return self.auth_manager.api

    def search_songs(self, query, limit=10):
        return self.api.search(query, filter="songs", limit=limit)

    def get_library_playlists(self):
        return self.api.get_library_playlists()

    def get_playlist_songs(self, playlist_id):
        """Get tracks from a specific playlist."""
        return self.api.get_playlist(playlist_id)

    def get_liked_songs(self, limit=50):
        """Get the 'Liked Music' playlist content."""
        return self.api.get_liked_songs(limit=limit)
