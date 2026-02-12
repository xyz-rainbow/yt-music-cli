import logging

from ytmusicapi import YTMusic

from src.api.auth import AuthManager

logger = logging.getLogger(__name__)


class YTMusicClient:
    def __init__(self, auth_manager: AuthManager):
        self.auth_manager = auth_manager
        self._public_api: YTMusic | None = None

    @property
    def api(self):
        return self.auth_manager.api

    @property
    def public_api(self) -> YTMusic:
        """Unauthenticated YTMusic instance used as fallback for search."""
        if self._public_api is None:
            self._public_api = YTMusic()
        return self._public_api

    def search_songs(self, query, limit=15):
        """Search for songs. Falls back to unauthenticated search on OAuth 400 errors."""
        try:
            results = self.api.search(query, limit=limit)
            return [r for r in results if r.get("resultType") in ["song", "video"]]
        except Exception as e:
            # Known ytmusicapi OAuth bug: TV/limited-input clients get 400 on search
            if "400" in str(e):
                logger.warning("OAuth search returned 400, falling back to public search")
                try:
                    results = self.public_api.search(query, limit=limit)
                    return [r for r in results if r.get("resultType") in ["song", "video"]]
                except Exception as fallback_err:
                    logger.error(f"Public search also failed: {fallback_err}")
                    raise fallback_err
            raise

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

