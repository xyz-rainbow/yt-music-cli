import subprocess
import logging
import shutil

class Player:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.process = None
        self.current_url = None
        
        # Check for players
        if shutil.which("mpv"):
            self.executable = "mpv"
            # --no-video for audio only, --idle=yes to keep process alive? 
            # Easier to just spawn per track for this simple CLI
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
            return

        self.stop() # Stop previous

        self.current_url = url
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

    def pause(self):
        """Toggle pause. (Not easily supported in simple subprocess fire-and-forget without IPC)"""
        # For simple subprocess, we can't easily pause unless we use an IPC socket (mpv --input-ipc-server)
        # For now, let's just log that it's limited.
        self.logger.warning("Pause not implemented in simple subprocess mode")

    def stop(self):
        """Stop playback."""
        if self.process:
            self.process.terminate()
            self.process = None
            
    def set_volume(self, volume: int):
        """Set volume. (Also hard without IPC)"""
        pass
            
    def get_status(self) -> dict:
        """Get current playback status."""
        state = "Playing" if self.process and self.process.poll() is None else "Stopped"
        return {
            "title": "Track", # We don't get metadata back from subprocess easily
            "artist": "Unknown",
            "paused": False,
            "state": state
        }
