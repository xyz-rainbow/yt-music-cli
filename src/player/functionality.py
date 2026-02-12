import subprocess
import logging
import shutil
import signal
import os
import platform

class Player:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.process = None
        self.current_url = None
        self._paused = False
        
        # Check for players
        if shutil.which("mpv"):
            self.executable = "mpv"
            # --no-video for audio only
            self.args = ["--no-video"]
        elif shutil.which("ffplay"):
            self.executable = "ffplay"
            self.args = ["-nodisp", "-autoexit"]
        else:
            self.executable = None
            self.logger.error("No player (mpv or ffplay) found in PATH")

    def play(self, url: str):
        """Play a stream URL."""
        if not self.executable:
            raise RuntimeError("No audio player found (mpv or ffplay). Please install one.")

        self.stop() # Stop previous

        self.current_url = url
        self._paused = False

        try:
            cmd = [self.executable] + self.args + [url]
            # Start process non-blocking
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
        except Exception as e:
            self.logger.error(f"Playback failed: {e}")
            raise e

    def pause(self):
        """Toggle pause using process signals."""
        if not self.process or self.process.poll() is not None:
            return

        try:
            # Check for signal availability safely
            sig_stop = getattr(signal, "SIGSTOP", None)
            sig_cont = getattr(signal, "SIGCONT", None)

            if not sig_stop or not sig_cont:
                self.logger.warning("Pause not supported on this OS (missing SIGSTOP/SIGCONT).")
                return

            if self._paused:
                # Resume
                os.kill(self.process.pid, sig_cont)
                self._paused = False
            else:
                # Pause
                os.kill(self.process.pid, sig_stop)
                self._paused = True

        except Exception as e:
            self.logger.error(f"Failed to toggle pause: {e}")

    def stop(self):
        """Stop playback."""
        if self.process:
            self.process.terminate()
            try:
                self.process.wait(timeout=1)
            except subprocess.TimeoutExpired:
                self.process.kill()
            self.process = None
            self._paused = False
            
    def set_volume(self, volume: int):
        """Set volume. (Also hard without IPC)"""
        pass
            
    def get_status(self) -> dict:
        """Get current playback status."""
        is_running = self.process and self.process.poll() is None

        if not is_running:
             state = "Stopped"
             self._paused = False # Reset if process died
        elif self._paused:
             state = "Paused"
        else:
             state = "Playing"

        return {
            "title": "Track", # We don't get metadata back from subprocess easily
            "artist": "Unknown",
            "paused": self._paused,
            "state": state
        }
