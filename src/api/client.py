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

    def get_home(self, limit=3):
        """Get home page sections and flatten them into a list of tracks."""
        try:
            home_data = self.api.get_home(limit=limit)
            tracks = []
            for section in home_data:
                # Each section has 'contents' which can be tracks, albums, or playlists
                for item in section.get("contents", []):
                    # We only want items that look like tracks (have videoId)
                    if "videoId" in item:
                        tracks.append(item)
                    # If it's an album or playlist, we could potentially expand it, 
                    # but for 'Search Home' button, let's keep it to direct tracks found on home
            return tracks
        except Exception:
            return []

    def like_song(self, video_id):
        """Rate a song as 'LIKE'."""
        return self.api.rate_song(video_id, rating="LIKE")

    def unlike_song(self, video_id):
        """Remove rating from a song ('INDIFFERENT')."""
        return self.api.rate_song(video_id, rating="INDIFFERENT")
