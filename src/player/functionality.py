import subprocess
import logging
import shutil
import os
import json
import socket
import time
import yt_dlp

class Player:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.process = None
        self.current_url = None
        self.ipc_path = "/tmp/ytmusic-cli-mpv.sock"
        
        # Configuration for yt-dlp
        self.ydl_opts = {
            'format': 'bestaudio/best',
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
        }
        
        if shutil.which("mpv"):
            self.executable = "mpv"
            # Buscamos el yt-dlp de nuestro .venv
            venv_ytdlp = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".venv/bin/yt-dlp")
            
            # Argumentos para inicio ultra rápido
            self.args = [
                "--no-video", 
                "--idle=yes", 
                f"--input-ipc-server={self.ipc_path}",
                "--cache=yes",
                "--demuxer-max-bytes=500KiB", # Buffer pequeño para inicio rápido
                "--demuxer-readahead-secs=1",
            ]
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
            if os.path.exists(self.ipc_path):
                try:
                    os.remove(self.ipc_path)
                except OSError:
                    pass
            
            cmd = [self.executable] + self.args
            # IMPORTANTE: start_new_session=True desacopla mpv de la terminal actual
            # stdin=subprocess.DEVNULL evita que mpv robe inputs del teclado
            self.process = subprocess.Popen(
                cmd,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True
            )
            # Give it a moment to create the socket
            for _ in range(10):
                if os.path.exists(self.ipc_path):
                    break
                time.sleep(0.1)

    def _send_command(self, command):
        """Send a JSON command and close socket immediately."""
        if not os.path.exists(self.ipc_path):
            return None
        
        try:
            # Creamos el socket solo para este comando y lo cerramos al instante
            client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            client.settimeout(0.01) # 10ms máximo
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
        except:
            pass # Ignorar errores para mantener la fluidez de la GUI
        return None

    def _get_stream_url(self, youtube_url: str) -> str:
        """Extract direct audio stream URL using yt-dlp."""
        try:
            with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
                info = ydl.extract_info(youtube_url, download=False)
                return info['url']
        except Exception as e:
            self.logger.error(f"Failed to extract stream URL: {e}")
            return youtube_url

    def play(self, url: str):
        """Play a stream URL."""
        if not self.executable:
            return

        self._ensure_process()
        self.current_url = url
        
        if self.executable == "mpv":
            # Usamos flags de carga rápida
            self._send_command(["loadfile", url, "replace"])
            self._send_command(["set_property", "pause", False])
            self._send_command(["set_property", "ytdl-format", "bestaudio"])
        else:
            # Fallback for ffplay
            self.stop()
            cmd = [self.executable] + self.args + [url]
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )

    def toggle_pause(self):
        """Toggle pause."""
        if self.executable == "mpv":
            # 'cycle pause' es atómico y mucho más rápido que preguntar y luego setear
            self._send_command(["cycle", "pause"])

    def stop(self):
        """Stop playback and kill process."""
        if self.process:
            try:
                self.process.terminate()
                self.process.wait(timeout=1)
            except:
                self.process.kill()
            self.process = None
        
        if os.path.exists(self.ipc_path):
            try:
                os.remove(self.ipc_path)
            except:
                pass
            
    def set_volume(self, volume: int):
        """Set volume (0-100)."""
        if self.executable == "mpv":
            self._send_command(["set_property", "volume", volume])
            
    def get_status(self) -> dict:
        """Get current playback status."""
        if self.executable == "mpv":
            paused = self._send_command(["get_property", "pause"])
            percent = self._send_command(["get_property", "percent-pos"])
            
            return {
                "paused": paused.get("data", False) if paused else False,
                "progress": percent.get("data", 0) if percent else 0,
                "state": "Playing" if not (paused and paused.get("data")) else "Paused"
            }
        
        state = "Playing" if self.process and self.process.poll() is None else "Stopped"
        return {
            "paused": False,
            "state": state
        }
