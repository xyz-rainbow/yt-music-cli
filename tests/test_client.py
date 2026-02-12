import unittest
import sys
import os
from unittest.mock import MagicMock

# Ensure src is in path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.api.client import YTMusicClient

class TestYTMusicClient(unittest.TestCase):
    def setUp(self):
        self.mock_auth_manager = MagicMock()
        self.mock_api = MagicMock()
        # Ensure the api property returns the mock API
        type(self.mock_auth_manager).api = unittest.mock.PropertyMock(return_value=self.mock_api)
        # Or simpler since auth_manager is a MagicMock, accessing .api returns a MagicMock by default
        # But we want it to return OUR mock_api
        self.mock_auth_manager.api = self.mock_api

        self.client = YTMusicClient(self.mock_auth_manager)

    def test_api_property(self):
        """Test that the api property delegates to auth_manager.api."""
        self.assertEqual(self.client.api, self.mock_api)

    def test_search_songs(self):
        """Test search_songs calls api.search with correct parameters."""
        query = "test query"
        limit = 20
        self.client.search_songs(query, limit=limit)

        self.mock_api.search.assert_called_once_with(query, filter="songs", limit=limit)

        # Test default limit
        self.client.search_songs(query)
        self.mock_api.search.assert_called_with(query, filter="songs", limit=10)

    def test_get_library_playlists(self):
        """Test get_library_playlists delegates to api.get_library_playlists."""
        self.client.get_library_playlists()
        self.mock_api.get_library_playlists.assert_called_once()

    def test_get_playlist_songs(self):
        """Test get_playlist_songs delegates to api.get_playlist."""
        playlist_id = "PL12345"
        self.client.get_playlist_songs(playlist_id)
        self.mock_api.get_playlist.assert_called_once_with(playlist_id)

    def test_get_liked_songs(self):
        """Test get_liked_songs delegates to api.get_liked_songs."""
        # Test default limit
        self.client.get_liked_songs()
        self.mock_api.get_liked_songs.assert_called_once_with(limit=50)

        self.mock_api.reset_mock()

        # Test custom limit
        limit = 100
        self.client.get_liked_songs(limit=limit)
        self.mock_api.get_liked_songs.assert_called_once_with(limit=limit)

if __name__ == '__main__':
    unittest.main()
