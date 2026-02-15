import asyncio
import threading
import base64
import io
import httpx
import logging
import os
import json
from PIL import Image
from rich.text import Text
from textual import work
from textual.screen import Screen
from textual.widgets import Input, DataTable, Button, Label, Static, ProgressBar
from textual.containers import Container, Horizontal, Vertical
from src.player.functionality import Player
from src.tui.utils import copy_to_clipboard
from src.config import get_data_dir

logger = logging.getLogger(__name__)



class PlayerScreen(Screen):
    BINDINGS = [
        ("left", "seek_backward", "Seek -10s"),
        ("right", "seek_forward", "Seek +10s"),
        ("alt+up", "volume_up", "Vol +5%"),
        ("alt+down", "volume_down", "Vol -5%"),
        ("alt+left", "skip_prev", "Prev Song"),
        ("alt+right", "skip_next", "Next Song"),
        ("alt+enter", "add_to_queue", "Add Queue"),
        ("alt+backspace", "remove_from_queue", "Rem Queue"),
        ("alt+s", "focus_search", "Search"),
        ("alt+c", "copy_url", "Copy URL"),
        ("alt+f", "toggle_liked", "Add to Playlist"),
    ]

    CSS = """
    $accent: #FF3333;
    $secondary: #9D00FF;
    $info: #00FFFF;

    #sidebar {
        width: 20%;
        height: 100%;
        background: transparent;
        /* Remove border for a cleaner seamless look */
    }
    .sidebar-title {
        text-style: bold;
        padding: 1 1 0 1;
        color: $accent;
        text-align: left;
        border-bottom: solid $accent;
        margin: 1 1 0 1;
    }
    .volume-label {
        text-align: center;
        background: $accent 30%;
        color: white;
        text-style: bold;
        padding: 0 1;
        margin: 1 1;
        border-left: solid $accent;
    }
    #playlist-list, #queue-list {
        height: 1fr;
        border: none;
        background: transparent;
        padding-left: 1;
    }
    #main-content {
        width: 80%;
        height: 100%;
        background: transparent;
        border-left: solid $accent; /* Very subtle divider */
    }
    #player-bar {
        height: auto;
        min-height: 8; /* Compressed */
        dock: bottom;
        background: $surface-lighten-1;
        border-top: solid $accent;
        padding: 0;
    }
    #player-info-container {
        width: 100%;
        height: auto;
        align: center middle;
        padding: 0;
    }
    .song-title {
        text-style: bold;
        color: $accent;
        text-align: center;
        width: 100%;
        margin-top: 0;
    }
    .song-artist {
        color: $info;
        text-style: italic;
        text-align: center;
        width: 100%;
        margin-bottom: 0;
    }
    #player-controls-row {
        width: 100%;
        height: 3;
        align: center middle;
        margin: 0;
    }
    .btn-control {
        min-width: 6;
        height: 3;
        margin: 0 1;
        border: none;
        background: transparent;
    }
    .btn-control:hover {
        background: $accent 20%;
    }
    #time-display {
        text-align: center;
        text-style: bold;
        color: $accent;
        width: 100%;
        margin-top: -1;
    }
    ProgressBar {
        width: 100%;
        height: 1;
        margin: 0;
        background: $surface-darken-1;
        color: $accent;
    }
    .controls-hint {
        text-align: center;
        width: 100%;
        color: $text-muted;
        margin-top: -1;
        margin-bottom: 0;
    }
    #search-input {
        margin: 1 2;
        border: tall $accent;
    }
    /* DataTable header styling */
    DataTable > .datatable--header {
        background: $accent 10%;
        color: $accent;
        text-style: bold;
    }
    .hidden {
        display: none;
    }
    """

    def compose(self):
        yield Horizontal(
            Vertical(
                Label("PLAYLISTS", classes="sidebar-title"),
                DataTable(id="playlist-list"),
                Label("QUEUE", classes="sidebar-title hidden", id="queue-title"),
                DataTable(id="queue-list", classes="hidden"),
                Label("[Alt] VOL: 100%", id="volume-display", classes="volume-label"),
                id="sidebar"
            ),
            Vertical(
                Input(placeholder="Search songs...", id="search-input"),
                DataTable(id="results-table"),
                id="main-content"
            )
        )
        with Vertical(id="player-bar"):
            with Vertical(id="player-info-container"):
                yield Label("No song seleccionado", id="current-title", classes="song-title")
                yield Label("", id="current-artist", classes="song-artist")
                with Horizontal(id="player-controls-row"):
                    yield Button("⏮️", id="btn-prev", classes="btn-control")
                    yield Button("⏯️", id="btn-play-pause", classes="btn-control")
                    yield Button("⏭️", id="btn-next", classes="btn-control")
                yield Label("00:00 / 00:00", id="time-display")
            
            # Moved Progress Bar below controls ("mas baja")
            yield ProgressBar(total=100, show_bar=True, show_eta=False, show_percentage=False, id="progress-bar")
            yield Static("Atajos: [Espacio] Play/Pausa | [Alt+←/→] Saltar | [Alt+↑/↓] Vol | [Alt+Enter] Añadir Cola", classes="controls-hint")

    def on_mount(self):
        self.player = Player()
        self.results_data = {}
        self.queued_songs = []
        self.session_liked_songs = set()
        self.favorites_file = str(get_data_dir() / "favorites.json")
        self.local_favorites = self.load_favorites()
        self.current_track_id = None
        self._current_volume = 100
        self._cached_playlists = []
        self.search_timer = None  # Timer for search debounce
        self.current_search_query = ""
        self.current_results_limit = 20
        self.is_loading_more = False
        
        # Results table setup
        res_table = self.query_one("#results-table")
        res_table.add_column("Art", width=5)
        res_table.add_column("Title", width=40)
        res_table.add_column("Artist", width=30)
        res_table.cursor_type = "row"
        res_table.zebra_stripes = True

        # Playlist table setup
        p_table = self.query_one("#playlist-list")
        p_table.add_column("Playlist")
        p_table.add_row("⭐ Local Favorites", key="local_favs")
        p_table.add_row("❤️ Liked Music (API)", key="liked")
        p_table.add_row("🔄 Refresh Lists", key="refresh")
        p_table.cursor_type = "row"

        # Queue table setup
        q_table = self.query_one("#queue-list")
        q_table.add_column("Song Title")
        q_table.cursor_type = "row"
        
        self.query_one("#search-input").focus()
        
        # Start progress timer
        self.set_interval(1.0, self.update_progress)

    def update_progress(self):
        """Update progress bar and time display, and handle queue transitions."""
        try:
            status = self.player.get_status()
            if status:
                time_pos = status.get("time_pos", 0)
                duration = status.get("duration", 0)
                state = status.get("state", "Stopped")
                
                # Check for end of song to play next in queue
                # if duration > 0 and time_pos >= duration - 0.5: # 0.5s buffer
                #     self.play_next_in_queue()
                
                # mpv state logic for auto-advance
                if state == "Stopped" and self.queued_songs:
                     self.play_next_in_queue()

                # Format time (MM:SS)
                def format_time(seconds):
                    m, s = divmod(int(seconds), 60)
                    return f"{m:02d}:{s:02d}"
                
                self.query_one("#time-display").update(f"{format_time(time_pos)} / {format_time(duration)}")
                
                if duration > 0:
                    prog_bar = self.query_one("#progress-bar")
                    prog_bar.progress = (time_pos / duration) * 100
        except Exception as e:
            logger.error(f"Progress update error: {e}")

    def play_next_in_queue(self):
        """Play the next song in the queue and update UI."""
        if not self.queued_songs:
            return
            
        next_song = self.queued_songs.pop(0)
        self.update_queue_ui()
        self.play_selected_song(next_song["videoId"])
        self.notify(f"Reproduciendo: {next_song.get('title')}")

    def update_queue_ui(self):
        q_table = self.query_one("#queue-list")
        q_title = self.query_one("#queue-title")
        q_table.clear()
        
        if self.queued_songs:
            for song in self.queued_songs:
                q_table.add_row(song.get("title", "Unknown"), key=song.get("videoId"))
            q_table.remove_class("hidden")
            q_title.remove_class("hidden")
        else:
            q_table.add_class("hidden")
            q_title.add_class("hidden")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-play-pause":
            self.toggle_worker()
        elif event.button.id == "btn-prev":
            self.action_skip_prev()
        elif event.button.id == "btn-next":
            self.action_skip_next()

    @work(exclusive=True)
    async def load_home_content(self):
        """Fetch and display recommended songs from the Home section."""
        self.notify("🏠 Loading recommendations from Home...")
        try:
            tracks = await asyncio.to_thread(self.app.client.get_home)
            if tracks:
                for t in tracks:
                    if 'videoId' in t:
                        self.results_data[t['videoId']] = t
                self.populate_table(tracks)
            else:
                self.notify("No direct tracks found on Home. Try searching instead.", severity="warning")
        except Exception as e:
            self.notify(f"Error loading home: {e}", severity="error")

    def on_data_table_row_selected(self, event: DataTable.RowSelected):
        if event.data_table.id == "playlist-list":
            playlist_id = event.row_key.value
            if playlist_id == "refresh":
                self.load_playlists()
            elif playlist_id == "local_favs":
                self.load_local_favorites_content()
            else:
                self.load_playlist_content(playlist_id)
        elif event.data_table.id == "queue-list":
            # Manual selection from queue should play it and remove it/reorder?
            # For now, just play it.
            self.play_selected_song(event.row_key.value)
        elif event.data_table.id == "results-table":
            self.play_selected_song(event.row_key.value)

    @work(exclusive=True)
    async def load_playlists(self):
        try:
            playlists = await asyncio.to_thread(self.app.client.get_library_playlists)
            p_table = self.query_one("#playlist-list")
            p_table.clear()
            p_table.add_row("❤️ Liked Music", key="liked")
            p_table.add_row("🔄 Refresh Lists", key="refresh")
            for p in playlists:
                p_table.add_row(p.get("title", "Untitled"), key=p.get("playlistId"))
        except Exception as e:
            self.notify(f"Error: {e}", severity="error")

    @work(exclusive=True)
    async def load_playlist_content(self, playlist_id):
        try:
            if playlist_id == "liked":
                songs = await asyncio.to_thread(self.app.client.get_liked_songs)
                tracks = songs.get("tracks", []) if isinstance(songs, dict) else songs
            else:
                playlist_data = await asyncio.to_thread(self.app.client.get_playlist_songs, playlist_id)
                tracks = playlist_data.get("tracks", [])

            for t in tracks:
                if 'videoId' in t: self.results_data[t['videoId']] = t
            self.populate_table(tracks)
        except Exception as e:
            self.notify(f"Error: {e}", severity="error")

    def populate_table(self, results, append=False):
        table = self.query_one("#results-table")
        if not append:
            table.clear()
        
        # Get existing keys to avoid duplicates in the UI
        existing_keys = {str(k.value) for k in table.rows.keys()}
        
        for song in results:
            video_id = song.get("videoId")
            if video_id and video_id not in existing_keys:
                artists = song.get("artists", [])
                artist_name = ", ".join([a["name"] for a in artists]) if isinstance(artists, list) else "Unknown"
                table.add_row(" 🖼️ ", song.get("title", "Unknown"), artist_name, key=video_id)

    def play_selected_song(self, video_id):
        song = self.results_data.get(video_id)
        if not song: return
        self.current_track_id = video_id
        # Metadata update
        self.query_one("#current-title").update(song.get("title", "Unknown"))
        artists = song.get("artists", [])
        artist_name = ", ".join([a["name"] for a in artists]) if isinstance(artists, list) else "Unknown"
        self.query_one("#current-artist").update(artist_name)
        
        self.play_worker(f"https://music.youtube.com/watch?v={video_id}")


    @work(exclusive=True)
    async def play_worker(self, url: str):
        try: await asyncio.to_thread(self.player.play, url)
        except Exception as e: self.app.notify(f"Error: {e}", severity="error")

    @work
    async def download_art(self, url: str):
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(url, timeout=5.0)
                if resp.status_code == 200:
                    # self.query_one(AlbumArt).set_image(resp.content)
                    pass
                else:
                    self.app.notify(f"Art download failed: {resp.status_code}", severity="warning")
        except Exception as e:
            self.app.notify(f"Art error: {e}", severity="error")

    @work(exclusive=True)
    async def toggle_worker(self):
        try:
            await asyncio.to_thread(self.player.toggle_pause)
        except: pass

    def on_data_table_row_highlighted(self, event: DataTable.RowHighlighted):
        """Infinite scroll: load more results when reaching the bottom."""
        if event.data_table.id == "results-table":
            row_index = event.cursor_row
            num_rows = event.data_table.row_count
            
            # If we are within 5 rows of the bottom, load more
            if num_rows > 10 and row_index >= num_rows - 5 and not self.is_loading_more:
                if self.current_search_query:
                    self.current_results_limit += 20
                    self.run_search(self.current_search_query, append=True)

    def on_input_changed(self, event: Input.Changed):
        if event.input.id == "search-input":
            # Clear results immediately if empty
            if len(event.value) == 0:
                self.query_one("#results-table").clear()
                self.current_search_query = ""
                return

            # Cancel previous timer if user is still typing
            if self.search_timer:
                self.search_timer.stop()
            
            # Set new timer (Debounce 0.5s)
            if len(event.value) > 2:
                self.current_results_limit = 20 # Reset limit on new query
                self.search_timer = self.set_timer(0.5, lambda: self.run_search(event.value))

    @work(exclusive=True)
    async def run_search(self, query, append=False):
        self.current_search_query = query
        self.is_loading_more = True
        try:
            results = await asyncio.to_thread(self.app.client.search_songs, query, limit=self.current_results_limit)
            if results:
                for s in results:
                    if 'videoId' in s: self.results_data[s['videoId']] = s
                self.populate_table(results, append=append)
            elif not append:
                self.query_one("#results-table").clear()
        except Exception as e:
            self.notify(f"Search error: {e}", severity="error")
        finally:
            self.is_loading_more = False

    def on_key(self, event):
        if event.key == "down" and self.focused and self.focused.id == "search-input":
            self.query_one("#results-table").focus()
            event.prevent_default()
        if event.is_printable and len(event.key) == 1 and event.key != " ":
            if not isinstance(self.focused, Input): self.query_one("#search-input").focus()

    def action_volume_up(self): self.adjust_volume(5)
    def action_volume_down(self): self.adjust_volume(-5)
    def adjust_volume(self, delta):
        self._current_volume = max(0, min(100, self._current_volume + delta))
        self.query_one("#volume-display").update(f"VOL: {self._current_volume}%")
        self.volume_worker(self._current_volume)

    @work(exclusive=True)
    async def volume_worker(self, volume: int):
        try: await asyncio.to_thread(self.player.set_volume, volume)
        except: pass

    def action_seek_backward(self): self.seek_worker(-10)
    def action_seek_forward(self): self.seek_worker(10)
    @work(exclusive=True)
    async def seek_worker(self, seconds: int):
        try: await asyncio.to_thread(self.player.seek, seconds)
        except: pass

    def action_skip_next(self):
        self.player.skip_next()
        self.notify("Next song")

    def action_skip_prev(self):
        self.player.skip_prev()
        self.notify("Previous song")

    def action_add_to_queue(self):
        table = self.query_one("#results-table")
        if table.cursor_row is not None:
            row_key = table.coordinate_to_cell_key(table.cursor_coordinate).row_key
            video_id = row_key.value
            song = self.results_data.get(video_id)
            if song:
                self.player.enqueue(f"https://music.youtube.com/watch?v={video_id}")
                self.queued_songs.append(song)
                self.update_queue_ui()
                self.notify(f"Added to queue: {song.get('title')}")

    def action_remove_from_queue(self):
        if not self.queued_songs:
            self.notify("Queue is already empty", severity="error")
            return
        last_song = self.queued_songs.pop()
        video_id = last_song.get('videoId')
        if self.player.remove_from_queue(f"https://music.youtube.com/watch?v={video_id}"):
            self.update_queue_ui()
            next_up = self.queued_songs[0].get('title') if self.queued_songs else "None"
            self.notify(f"Removed: {last_song.get('title')} | Next: {next_up}", severity="warning")
        else:
            self.queued_songs.append(last_song)
            self.notify("Error removing song", severity="error")

    def action_toggle_liked(self):
        """Toggles favorite status, enforcing API success first."""
        video_id = self.current_track_id
        if not video_id:
            table = self.query_one("#results-table")
            if table.cursor_row is not None:
                video_id = table.coordinate_to_cell_key(table.cursor_coordinate).row_key.value
        
        if video_id:
            song = self.results_data.get(video_id, {"title": "Unknown Song"})
            self.toggle_like_async(video_id, song)
        else:
            self.notify("No song selected", severity="error")

    @work
    async def toggle_like_async(self, video_id: str, song: dict):
        """Async worker: API Call -> Then Local Save."""
        title = song.get("title", "Unknown")
        is_liked = video_id in self.local_favorites
        
        # 1. Optimistic UI feedback or "Syncing..."
        action = "Removing..." if is_liked else "Liking..."
        self.notify(f"{action} {title} (Syncing API...)", timeout=2.0)
        
        try:
            # 2. Call API
            if is_liked:
                await asyncio.to_thread(self.app.client.unlike_song, video_id)
            else:
                await asyncio.to_thread(self.app.client.like_song, video_id)
            
            # 3. On Authenticated Success: Update Local State
            if is_liked:
                del self.local_favorites[video_id]
                self.notify(f"Removed from Favorites: {title}")
            else:
                clean_song = {
                    "videoId": video_id,
                    "title": title,
                    "artists": song.get("artists", [{"name": "Unknown"}])
                }
                self.local_favorites[video_id] = clean_song
                self.notify(f"Saved to Favorites: {title}")
            
            # 4. Persist
            self.save_favorites()
            
        except Exception as e:
            # 5. On Failure: Revert/Do nothing and Warn
            logger.error(f"API Sync failed for {video_id}: {e}")
            self.notify(f"Failed to sync with YouTube. Not saved locally.", severity="error")

    def load_favorites(self):
        """Load favorites as a dictionary of videoId -> metadata."""
        if os.path.exists(self.favorites_file):
            try:
                with open(self.favorites_file, "r") as f:
                    data = json.load(f)
                    # Migration: If it was a list (IDs only) or set, return empty dict or try to fetch?
                    # For now, if list, just convert to dict with unknown metadata to avoid crash
                    if isinstance(data, list): 
                        return {vid: {"title": "Unknown", "videoId": vid} for vid in data}
                    return data # Expecting dict
            except: return {}
        return {}

    def save_favorites(self):
        """Save the favorites dictionary directly."""
        with open(self.favorites_file, "w") as f:
            json.dump(self.local_favorites, f)

    @work(exclusive=True)
    async def load_local_favorites_content(self):
        """Loads and displays the locally stored favorites."""
        try:
            if not os.path.exists(self.favorites_file):
                self.notify("No local favorites yet.")
                return
            
            # local_favorites is now the master source of truth
            favs = self.local_favorites
            
            tracks = []
            for vid, song in favs.items():
                song["videoId"] = vid
                tracks.append(song)
                self.results_data[vid] = song
            
            self.populate_table(tracks)
            self.notify(f"Loaded {len(tracks)} favorites.")
        except Exception as e:
            self.notify(f"Error loading favorites: {e}", severity="error")

    def action_toggle_pause(self): self.toggle_worker()
    def key_space(self): self.action_toggle_pause()
    def key_q(self): self.app.exit()
    def action_focus_search(self): self.query_one("#search-input").focus()

    def action_copy_url(self):
        """Copies the current or highlighted song URL to clipboard."""
        # 1. Check if a song is currently playing
        video_id = self.current_track_id
        
        # 2. Fallback: if no song playing, get the highlighted row in the table
        if not video_id:
            table = self.query_one("#results-table")
            if table.cursor_row is not None:
                row_key = table.coordinate_to_cell_key(table.cursor_coordinate).row_key
                video_id = row_key.value

        if video_id:
            url = f"https://music.youtube.com/watch?v={video_id}"
            copy_to_clipboard(self.app, url)
        else:
            self.notify("No song selected to copy", severity="error")
