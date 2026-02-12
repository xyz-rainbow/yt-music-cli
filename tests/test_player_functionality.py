import sys
import os
import unittest
from unittest.mock import patch, MagicMock

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
    def test_play_success(self, mock_popen, mock_which):
        mock_which.side_effect = lambda x: "/usr/bin/mpv" if x == "mpv" else None
        player = Player()
        self.assertEqual(player.executable, "mpv")

        player.play("http://example.com")
        mock_popen.assert_called_once()
        args = mock_popen.call_args[0][0]
        self.assertEqual(args[0], "mpv")
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

        mock_process = player.process
        player.stop()
        mock_process.terminate.assert_called_once()
        self.assertIsNone(player.process)

    @patch('shutil.which')
    @patch('subprocess.Popen')
    @patch('os.kill')
    @patch('signal.SIGSTOP', create=True)
    @patch('signal.SIGCONT', create=True)
    def test_pause_resume(self, mock_sigcont, mock_sigstop, mock_kill, mock_popen, mock_which):
        mock_which.return_value = "/usr/bin/mpv"
        player = Player()
        player.play("http://example.com")

        # Mock process
        player.process.pid = 1234
        player.process.poll.return_value = None

        # Pause
        player.pause()
        mock_kill.assert_called_with(1234, mock_sigstop)
        self.assertTrue(player._paused)

        # Resume
        player.pause()
        mock_kill.assert_called_with(1234, mock_sigcont)
        self.assertFalse(player._paused)

if __name__ == '__main__':
    unittest.main()
