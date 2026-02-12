import time
import unittest
import sys
import os
from unittest.mock import MagicMock, patch

# Ensure src is in path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.player.functionality import Player

class TestPlayerBlocking(unittest.TestCase):
    @patch('shutil.which')
    @patch('subprocess.Popen')
    def test_play_blocks(self, mock_popen, mock_which):
        # Mock shutil.which to return a fake executable so Player assumes it's available
        mock_which.return_value = "/usr/bin/mpv"

        # Setup mock process
        mock_process = MagicMock()
        # wait sleeps for 0.5s to simulate blocking
        mock_process.wait.side_effect = lambda timeout=None: time.sleep(0.5)
        # terminate/kill just return
        mock_process.terminate.return_value = None
        mock_process.kill.return_value = None
        mock_process.poll.return_value = None # Running

        mock_popen.return_value = mock_process

        player = Player()

        # First play starts immediately (no previous process)
        player.play("url1")

        # Second play should block because it calls stop() which calls wait() on the previous process
        print("Starting second play call (expecting block)...")
        start = time.time()
        player.play("url2")
        duration = time.time() - start

        print(f"Play took {duration:.2f}s")
        self.assertGreater(duration, 0.4, "Player.play() blocked for less than the mocked wait time, meaning it did not wait properly or is already async.")

if __name__ == '__main__':
    unittest.main()
