import sys
import os
import unittest
import subprocess
from unittest.mock import patch, MagicMock, call

# Ensure src is in path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.player.functionality import Player

class TestPlayerFunctionality(unittest.TestCase):
    @patch('shutil.which')
    def test_init_no_player(self, mock_which):
        mock_which.return_value = None
        player = Player()
        self.assertIsNone(player.executable)

    @patch('shutil.which')
    def test_play_no_player_raises_error(self, mock_which):
        mock_which.return_value = None
        player = Player()
        with self.assertRaises(RuntimeError):
            player.play("http://example.com")

    @patch('shutil.which')
    @patch('subprocess.Popen')
    @patch('src.player.functionality.Player._send_command')
    def test_play_mpv_success(self, mock_send_command, mock_popen, mock_which):
        mock_which.side_effect = lambda x: "/usr/bin/mpv" if x == "mpv" else None
        player = Player()
        self.assertEqual(player.executable, "mpv")

        player.play("http://example.com")

        # Check Popen called to start mpv (via _ensure_process)
        mock_popen.assert_called()
        args = mock_popen.call_args[0][0]
        self.assertEqual(args[0], "mpv")
        # Ensure URL is NOT in args for mpv (it uses IPC)
        self.assertNotIn("http://example.com", args)

        # Check IPC commands sent
        # We expect loadfile, unpause, and set ytdl-format
        # Note: play() calls _ensure_process() which might or might not call Popen depending on state.
        # Here we start fresh so Popen is called.

        calls = [
            call(["loadfile", "http://example.com", "replace"]),
            call(["set_property", "pause", False]),
            call(["set_property", "ytdl-format", "bestaudio"])
        ]
        mock_send_command.assert_has_calls(calls, any_order=False)

    @patch('shutil.which')
    @patch('subprocess.Popen')
    def test_play_ffplay_success(self, mock_popen, mock_which):
        # Return None for mpv, path for ffplay
        def which_side_effect(cmd):
            if cmd == "mpv": return None
            if cmd == "ffplay": return "/usr/bin/ffplay"
            return None
        mock_which.side_effect = which_side_effect

        player = Player()
        self.assertEqual(player.executable, "ffplay")

        player.play("http://example.com")

        mock_popen.assert_called()
        args = mock_popen.call_args[0][0]
        self.assertEqual(args[0], "ffplay")
        self.assertIn("http://example.com", args)
        # Verify -- is present
        self.assertIn("--", args)
        # Verify url is after --
        dash_index = args.index("--")
        url_index = args.index("http://example.com")
        self.assertGreater(url_index, dash_index)

    @patch('shutil.which')
    def test_play_invalid_protocol(self, mock_which):
        mock_which.return_value = "/usr/bin/mpv"
        player = Player()

        invalid_urls = [
            "file:///etc/passwd",
            "ftp://example.com",
            "javascript:alert(1)",
            "--help"
        ]

        for url in invalid_urls:
            with self.assertRaises(ValueError):
                player.play(url)

    @patch('shutil.which')
    @patch('subprocess.Popen')
    def test_stop(self, mock_popen, mock_which):
        mock_which.return_value = "/usr/bin/mpv"
        player = Player()
        player.play("http://example.com")

        # Mock the process object on the player
        mock_process = MagicMock()
        player.process = mock_process

        player.stop()

        mock_process.terminate.assert_called_once()
        mock_process.wait.assert_called_with(timeout=1)
        self.assertIsNone(player.process)

    @patch('shutil.which')
    @patch('subprocess.Popen')
    def test_stop_timeout(self, mock_popen, mock_which):
        """Verify that process.kill() is called if process.wait(timeout=1) raises TimeoutExpired."""
        mock_which.return_value = "/usr/bin/mpv"
        player = Player()

        # Setup a mock process
        mock_process = MagicMock()
        mock_process.wait.side_effect = subprocess.TimeoutExpired(cmd="mpv", timeout=1)
        player.process = mock_process

        player.stop()

        mock_process.terminate.assert_called_once()
        mock_process.wait.assert_called_with(timeout=1)
        mock_process.kill.assert_called_once()
        self.assertIsNone(player.process)

    @patch('shutil.which')
    @patch('src.player.functionality.Player._send_command')
    def test_toggle_pause_mpv(self, mock_send_command, mock_which):
        mock_which.return_value = "/usr/bin/mpv"
        player = Player()

        player.toggle_pause()
        mock_send_command.assert_called_with(["cycle", "pause"])

if __name__ == '__main__':
    unittest.main()
