import mpv
import logging
from typing import Optional, Callable

class Player:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        try:
            # Initialize MPV instance with specific options for better audio streaming
            self.mpv = mpv.MPV(ytdl=True, input_default_bindings=True, input_vo_keyboard=True, osc=True)
            self.mpv['vo'] = 'null' # Audio only
        except Exception as e:
            self.logger.error(f"Failed to initialize MPV: {e}")
            self.mpv = None

    def play(self, url: str):
        """Play a stream URL."""
        if self.mpv:
            self.mpv.play(url)

    def pause(self):
        """Toggle pause."""
        if self.mpv:
            self.mpv.pause = not self.mpv.pause

    def stop(self):
        """Stop playback."""
        if self.mpv:
            self.mpv.stop()
            
    def set_volume(self, volume: int):
        """Set volume (0-100)."""
        if self.mpv:
            self.mpv.volume = max(0, min(100, volume))
            
    def get_status(self) -> dict:
        """Get current playback status."""
        if not self.mpv:
            return {"state": "error", "title": "No Backend"}
            
        return {
            "title": self.mpv.media_title or "Unknown",
            "artist": self.mpv.metadata.get("artist") if self.mpv.metadata else "Unknown",
            "paused": self.mpv.pause,
            "position": self.mpv.time_pos,
            "duration": self.mpv.duration,
            "volume": self.mpv.volume
        }
