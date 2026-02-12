import subprocess
import logging
import shutil
import os
import json
import socket
import time
import threading
import signal
import signal

class Player:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.process = None
        self.current_url = None
        self.ipc_path = "/tmp/ytmusic-cli-mpv.sock"
        self._paused = False
        self._lock = threading.RLock()
        
        # Configuration for yt-dlp
        self.ydl_opts = {
            'format': 'bestaudio/best',
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
        }
        self.auth_file = "oauth.json" # Match AuthManager.CREDENTIALS_FILE
        
        if shutil.which("mpv"):
            self.executable = "mpv"
            # Buscamos el yt-dlp de nuestro .venv
            venv_ytdlp = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".venv/bin/yt-dlp")
            
            # Argumentos: "Pure Audio Mode" (Sin corrección A/V para evitar crujidos)
            self.args = [
                "--no-video", 
                "--idle=yes", 
                f"--input-ipc-server={self.ipc_path}",
                # Networking
                "--cache=yes",
                "--demuxer-max-bytes=128MiB",
                "--demuxer-readahead-secs=20",
                # AUDIO PURO: Desactivar sincronización de video (Causa #1 de crujidos)
                "--mc=0",                    # Disable A/V sync correction
                "--autosync=0",              # Disable auto-sync
                "--no-initial-audio-sync",   # Don't wait for sync
                "--video-sync=display-desync", # Desync video clock completely
                # Calidad y Volumen
                "--volume-max=100",          # Evitar clipping digital
                "--audio-pitch-correction=no", # No estirar el audio si hay lag
                # Formato
                "--ytdl-format=bestaudio/best",
                "--ytdl-raw-options=extractor-args=youtube:player_client=android+web+ios,js-runtimes=node",
            ]
            # Add cookies if they exist to allow streaming liked/private content
            if os.path.exists(self.auth_file):
                 # Note: yt-dlp can't always read our JSON directly as cookies, 
                 # but for now we try to let mpv handle it or we could export to netscape format.
                 # Let's at least try to point to it if it was a headers/cookies file.
                 pass
            if os.path.exists(venv_ytdlp):
                self.args.append(f"--script-opts=ytdl_hook-ytdl_path={venv_ytdlp}")
        elif shutil.which("ffplay"):
            self.executable = "ffplay"
            self.args = ["-nodisp", "-autoexit"]
        else:
            self.executable = None
            self.logger.error("No player (mpv or ffplay) found in PATH")

    def _ensure_process(self):
        """Ensure mpv is running."""
        if self.executable == "mpv" and (not self.process or self.process.poll() is not None):
            self.logger.debug("Starting mpv process...")
            if os.path.exists(self.ipc_path):
                try:
                    os.remove(self.ipc_path)
                except OSError:
                    pass
            
            cmd = [self.executable] + self.args
            
            # Use a log file for debugging playback issues
            log_file = open("player.log", "a")
            try:
                self.process = subprocess.Popen(
                    cmd,
                    stdin=subprocess.DEVNULL,
                    stdout=log_file,
                    stderr=log_file,
                    start_new_session=True
                )
                self.logger.debug(f"mpv started with PID {self.process.pid}")
            except Exception as e:
                self.logger.error(f"Failed to start mpv: {e}")
                return

            # Give it a moment to create the socket
            for i in range(20):
                if os.path.exists(self.ipc_path):
                    self.logger.debug(f"IPC socket found after {i*0.1:.1f}s")
                    break
                time.sleep(0.1)
            else:
                self.logger.error("MPV IPC socket not found after timeout")

    def _send_command(self, command):
        """Send a JSON command and close socket immediately."""
        if not os.path.exists(self.ipc_path):
            self.logger.warning(f"IPC socket {self.ipc_path} missing for command {command[0]}")
            return None
        
        try:
            # Creamos el socket solo para este comando y lo cerramos al instante
            client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            client.settimeout(0.1) # Increased timeout slightly for reliability
            client.connect(self.ipc_path)
            msg = json.dumps({"command": command}) + "\n"
            client.sendall(msg.encode())
            
            if command[0].startswith("get_"):
                response = client.recv(4096)
                client.close()
                if response:
                    return json.loads(response.decode().split("\n")[0])
            else:
                client.close()
        except Exception as e:
            self.logger.error(f"IPC error sending {command[0]}: {e}")
        return None


    def play(self, url: str):
        """Play a stream URL."""
        if not url.lower().startswith(('http://', 'https://')):
            self.logger.error(f"Security blocked: Invalid URL scheme: {repr(url)}")
            raise ValueError("Invalid URL protocol. Only http/https supported.")

        if not self.executable:
            raise RuntimeError("No audio player found (mpv or ffplay). Please install one.")

        with self._lock:
            if self.current_url == url and self.process and self.process.poll() is None:
                if self.executable == "mpv":
                    self._send_command(["set_property", "pause", False])
                return

            self._ensure_process()
            self.current_url = url
            self._paused = False
            
            if self.executable == "mpv":
                # NEW: Try to extract direct URL using yt-dlp first for better reliability
                # and to avoid mpv's ytdl-hook issues on some systems.
                try:
                    import subprocess
                    venv_ytdlp = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".venv/bin/yt-dlp")
                    ytdlp_bin = venv_ytdlp if os.path.exists(venv_ytdlp) else "yt-dlp"
                    
                    self.logger.debug(f"Extracting URL with {ytdlp_bin}...")
                    result = subprocess.run(
                        [ytdlp_bin, "-g", "-f", "bestaudio", url],
                        capture_output=True, text=True, timeout=10
                    )
                    if result.returncode == 0:
                        stream_url = result.stdout.strip()
                        self._send_command(["loadfile", stream_url, "replace"])
                        self._send_command(["set_property", "pause", False])
                        self.logger.debug("Playing via extracted direct URL")
                        return
                    else:
                        self.logger.warning(f"yt-dlp extraction failed: {result.stderr}")
                except Exception as e:
                    self.logger.warning(f"Direct extraction error: {e}")

                # Fallback to standard loadfile if extraction failed
                self._send_command(["loadfile", url, "replace"])
                self._send_command(["set_property", "pause", False])

    def enqueue(self, url: str):
        """Add a stream URL to the playlist."""
        if not url.lower().startswith(('http://', 'https://')):
            return

        with self._lock:
            self._ensure_process()
            if self.executable == "mpv":
                self._send_command(["loadfile", url, "append-play"])

    def remove_from_queue(self, url: str) -> bool:
        """Remove a specific URL from the mpv playlist. Returns True if found."""
        if self.executable != "mpv":
            return False

        with self._lock:
            playlist_resp = self._send_command(["get_property", "playlist"])
            if not playlist_resp or "data" not in playlist_resp:
                return False

            playlist = playlist_resp["data"]
            # Find the index of the item with the matching filename (URL)
            for i, item in enumerate(playlist):
                if item.get("filename") == url:
                    self._send_command(["playlist-remove", i])
                    return True
        return False


    def pause(self):
        """Toggle pause using process signals."""
        if not self.process or self.process.poll() is not None:
            return

        try:
            # Check for signal availability safely
            sig_stop = getattr(signal, "SIGSTOP", None)
            sig_cont = getattr(signal, "SIGCONT", None)

            if sig_stop is None or sig_cont is None:
                self.logger.warning("SIGSTOP/SIGCONT not supported on this platform")
                return

            if self._paused:
                os.kill(self.process.pid, sig_cont)
                self._paused = False
            else:
                os.kill(self.process.pid, sig_stop)
                self._paused = True
        except Exception as e:
            self.logger.error(f"Failed to pause/resume process: {e}")

    def toggle_pause(self):
        """Toggle pause."""
        with self._lock:
            self._ensure_process()
            if self.executable == "mpv":
                # 'cycle pause' is atomic and faster
                self._send_command(["cycle", "pause"])
            else:
                self.pause()

    def stop(self):
        """Stop playback and kill process."""
        with self._lock:
            if self.process:
                try:
                    self.process.terminate()
                    self.process.wait(timeout=1)
                except subprocess.TimeoutExpired:
                    self.process.kill()
                except Exception:
                    pass
                self.process = None
                self._paused = False
            
            if os.path.exists(self.ipc_path):
                try:
                    os.remove(self.ipc_path)
                except:
                    pass
            
    def set_volume(self, volume: int):
        """Set volume (0-100)."""
        if not (0 <= volume <= 100):
            return

        if self.executable == "mpv":
            self._send_command(["set_property", "volume", volume])
        else:
            self.logger.warning(f"Volume control not supported for {self.executable}")

    def get_volume(self) -> int:
        """Get current volume (0-100)."""
        if self.executable == "mpv":
            resp = self._send_command(["get_property", "volume"])
            if resp and "data" in resp:
                return int(resp["data"])
        return 100
            
    def get_status(self) -> dict:
        """Get current playback status."""
        with self._lock:
            if self.executable == "mpv":
                paused = self._send_command(["get_property", "pause"])
                percent = self._send_command(["get_property", "percent-pos"])
                time_pos = self._send_command(["get_property", "time-pos"])
                duration = self._send_command(["get_property", "duration"])
                
                return {
                    "paused": paused.get("data", False) if paused else False,
                    "progress": percent.get("data", 0) if percent else 0,
                    "time_pos": time_pos.get("data", 0) if time_pos else 0,
                    "duration": duration.get("data", 0) if duration else 0,
                    "state": "Playing" if not (paused and paused.get("data")) else "Paused"
                }
            
            is_running = self.process and self.process.poll() is None
            if not is_running:
                state = "Stopped"
                self._paused = False
            elif self._paused:
                state = "Paused"
            else:
                state = "Playing"
            
            return {
                "paused": self._paused,
                "state": state
            }

    def seek(self, seconds: int):
        """Seek forward or backward by seconds."""
        if self.executable == "mpv":
            # seconds can be positive (forward) or negative (backward)
            self._send_command(["seek", seconds, "relative"])
        else:
            self.logger.warning(f"Seeking not supported for {self.executable}")

    def skip_next(self):
        """Skip to the next song in the playlist."""
        if self.executable == "mpv":
            self._send_command(["playlist-next"])

    def skip_prev(self):
        """Skip to the previous song in the playlist."""
        if self.executable == "mpv":
            self._send_command(["playlist-prev"])
