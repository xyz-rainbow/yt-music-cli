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
    @patch('src.player.functionality.Player._send_command')
    @patch('subprocess.Popen')
    def test_play_success(self, mock_popen, mock_send_command, mock_which):
        mock_which.side_effect = lambda x: "/usr/bin/mpv" if x == "mpv" else None
        player = Player()
        self.assertEqual(player.executable, "mpv")

        player.play("http://example.com")

        # Verify process started (without URL)
        mock_popen.assert_called_once()
        args = mock_popen.call_args[0][0]
        self.assertEqual(args[0], "mpv")
        self.assertNotIn("http://example.com", args)

        # Verify loadfile command
        mock_send_command.assert_any_call(["loadfile", "http://example.com", "replace"])

    @patch('shutil.which')
    @patch('subprocess.Popen')
    def test_stop(self, mock_popen, mock_which):
        mock_which.return_value = "/usr/bin/mpv"
        player = Player()
        # Mocking _send_command to avoid IPC errors during play
        with patch.object(player, '_send_command'):
            player.play("http://example.com")

        mock_process = player.process
        player.stop()
        mock_process.terminate.assert_called_once()
        self.assertIsNone(player.process)

    @patch('shutil.which')
    @patch('subprocess.Popen')
    @patch('os.kill')
    @patch('src.player.functionality.signal')
    def test_pause_resume(self, mock_signal, mock_kill, mock_popen, mock_which):
        mock_which.return_value = "/usr/bin/mpv"
        player = Player()

        # Configure mock signal to have attributes
        mock_signal.SIGSTOP = 19
        mock_signal.SIGCONT = 18

        with patch.object(player, '_send_command'):
            player.play("http://example.com")

        # Mock process
        player.process.pid = 1234
        player.process.poll.return_value = None

        # Pause
        player.pause()
        mock_kill.assert_called_with(1234, 19)
        self.assertTrue(player._paused)

        # Resume
        player.pause()
        mock_kill.assert_called_with(1234, 18)
        self.assertFalse(player._paused)

    @patch('shutil.which')
    @patch('subprocess.Popen')
    def test_pause_missing_signals(self, mock_popen, mock_which):
        mock_which.return_value = "/usr/bin/mpv"
        player = Player()
        with patch.object(player, '_send_command'):
            player.play("http://example.com")

        player.process.pid = 1234
        player.process.poll.return_value = None

        # Create a mock signal module that has no SIGSTOP/SIGCONT attributes
        class MockSignalModule:
            pass

        with patch('src.player.functionality.signal', MockSignalModule()):
            player.pause()

            # Should log warning (we could verify logging but not strictly required)
            # State should not change
            self.assertFalse(player._paused)

if __name__ == '__main__':
    unittest.main()
