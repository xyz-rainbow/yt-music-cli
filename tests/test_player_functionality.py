import sys
import os
import unittest
from unittest.mock import patch, MagicMock

# Ensure src is in path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Mock yt_dlp before importing Player if not installed
try:
    import yt_dlp
except ImportError:
    sys.modules["yt_dlp"] = MagicMock()

from src.player.functionality import Player

class TestPlayerFunctionality(unittest.TestCase):
    @patch('shutil.which')
    def test_init_no_player(self, mock_which):
        mock_which.return_value = None
        player = Player()
        self.assertIsNone(player.executable)

    @patch('shutil.which')
    def test_play_no_player_safe_return(self, mock_which):
        mock_which.return_value = None
        player = Player()
        # Should not raise exception
        try:
            player.play("http://example.com")
        except Exception as e:
            self.fail(f"play raised exception unexpectedly: {e}")

    @patch('shutil.which')
    @patch('src.player.functionality.Player._send_command')
    @patch('src.player.functionality.Player._ensure_process')
    def test_play_success_mpv(self, mock_ensure, mock_send, mock_which):
        mock_which.side_effect = lambda x: "/usr/bin/mpv" if x == "mpv" else None
        player = Player()
        self.assertEqual(player.executable, "mpv")

        player.play("http://example.com")

        mock_ensure.assert_called_once()
        # Check command sent
        mock_send.assert_any_call(["loadfile", "http://example.com", "replace"])
        mock_send.assert_any_call(["set_property", "pause", False])

    @patch('shutil.which')
    @patch('src.player.functionality.Player._send_command')
    def test_toggle_pause_mpv(self, mock_send, mock_which):
        mock_which.return_value = "/usr/bin/mpv"
        player = Player()

        player.toggle_pause()
        mock_send.assert_called_with(["cycle", "pause"])

if __name__ == '__main__':
    unittest.main()
