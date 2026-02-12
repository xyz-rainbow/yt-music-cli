import threading
import time
import unittest
import sys
import os
from unittest.mock import MagicMock, patch
from concurrent.futures import ThreadPoolExecutor

# Mock dependencies before import
sys.modules['yt_dlp'] = MagicMock()
sys.modules['ytmusicapi'] = MagicMock()

# Ensure src is in path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.player.functionality import Player

class TestPlayerConcurrency(unittest.TestCase):
    @patch('shutil.which')
    @patch('subprocess.Popen')
    def test_concurrent_play(self, mock_popen, mock_which):
        mock_which.return_value = "/usr/bin/mpv"

        # Setup mock process
        mock_process = MagicMock()
        # wait sleeps for 0.1s to simulate blocking stop
        mock_process.wait.side_effect = lambda timeout=None: time.sleep(0.1)
        mock_process.poll.return_value = None

        mock_popen.return_value = mock_process

        player = Player()

        num_threads = 5
        start_time = time.time()

        def play_task(i):
            player.play(f"http://example.com/{i}")

        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(play_task, i) for i in range(num_threads)]
            for future in futures:
                try:
                    future.result() # Wait for all and check for exceptions
                except Exception as e:
                    self.fail(f"Thread raised exception: {e}")

        duration = time.time() - start_time
        print(f"Total duration for {num_threads} concurrent plays: {duration:.2f}s")

        # The first play doesn't wait (no previous process).
        # The subsequent 4 plays wait for the previous one to stop (0.1s each).
        # Total expected wait: ~0.4s.
        # Plus some overhead.

        self.assertGreater(duration, 0.35, "Concurrent play calls should be serialized by the lock")
        self.assertEqual(mock_popen.call_count, num_threads, "Should have started 5 processes")

if __name__ == '__main__':
    unittest.main()
