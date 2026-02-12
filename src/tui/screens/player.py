import asyncio
import threading
import base64
import io
import httpx
import logging
from PIL import Image
from rich.text import Text
from textual import work
from textual.screen import Screen
from textual.widgets import Input, DataTable, Button, Label, Static
from textual.containers import Container, Horizontal, Vertical
from src.player.functionality import Player

logger = logging.getLogger(__name__)

class AlbumArt(Static):
    """A widget to display album art using high-quality block characters via Rich."""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._art_text = Text("\n\n [ NO ART ] ", justify="center")

    def _generate_block_art(self, img):
        target_width = 34
        target_height = 16
        small_img = img.convert("RGB").resize((target_width, target_height * 2), Image.Resampling.LANCZOS)
        text = Text()
        for y in range(0, small_img.height, 2):
            for x in range(small_img.width):
                r1, g1, b1 = small_img.getpixel((x, y))
                r2, g2, b2 = small_img.getpixel((x, y + 1)) if y + 1 < small_img.height else (0, 0, 0)
                text.append("▀", style=f"color(#{r1:02x}{g1:02x}{b1:02x}) on color(#{r2:02x}{g2:02x}{b2:02x})")
            text.append("\n")
        return text

    def set_image(self, image_bytes: bytes):
        try:
            img = Image.open(io.BytesIO(image_bytes))
            self._art_text = self._generate_block_art(img)
            self.update(self._art_text)
        except Exception as e:
            self.update(Text(f"Error: {e}", style="red"))

    def render(self):
        return self._art_text

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
        ("alt+h", "search_home", "Home"),
        ("alt+f", "toggle_liked", "Like/Unlike"),
    ]

    CSS = """
    $accent: #FF3333;
    $secondary: #9D00FF;
    $info: #00FFFF;

    #sidebar {
        width: 20%;
        height: 100%;
        background: transparent;
        border-right: solid $accent;
    }
    .sidebar-title {
        text-style: bold;
        padding: 1;
        background: $accent;
        color: $text;
        text-align: center;
    }
    .volume-label {
        text-align: center;
        background: $secondary;
        color: white;
        text-style: bold;
        padding: 0 1;
        margin: 1 0;
    }
    #playlist-list, #queue-list {
        height: 1fr;
        border: none;
        background: transparent;
    }
    #main-content {
        width: 50%;
        height: 100%;
        background: transparent;
    }
    #now-playing {
        width: 30%;
        height: 100%;
        background: transparent;
        border-left: solid $accent;
        padding: 1;
        align: center top;
    }
    AlbumArt {
        width: 100%;
        height: 18;
        margin: 1 0;
        content-align: center middle;
        background: transparent;
        border: tall $secondary;
    }
    #player-bar {
        height: 3;
        dock: bottom;
        background: $secondary;
        color: white;
        content-align: center middle;
        text-style: bold;
    }
    DataTable {
        scrollbar-gutter: stable;
        overflow-x: hidden;
    }
    .song-title {
        text-style: bold;
        color: $accent;
        text-align: center;
        width: 100%;
    }
    .song-artist {
        color: $info;
        text-align: center;
        width: 100%;
        margin-top: 1;
    }
    .song-album {
        color: $text-muted;
        text-align: center;
        width: 100%;
        text-style: italic;
    }
    #search-input {
        margin: 1;
        border: tall $accent;
    }
    .hidden {
        display: none;
    }
    """

    def compose(self):
        yield Horizontal(
            Vertical(
                Label("LIBRARY", classes="sidebar-title"),
                Button("Search Home", id="btn-home", variant="default"),
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
            ),
            Vertical(
                Label("NOW PLAYING", classes="sidebar-title"),
                AlbumArt(id="album-art"),
                Label("No song selected", id="current-title", classes="song-title"),
                Label("", id="current-artist", classes="song-artist"),
                Label("", id="current-album", classes="song-album"),
                id="now-playing"
            )
        )
        yield Static("Controls: [Space] Pause | [Alt+←/→] Skip | [Alt+Enter] Queue | [Alt+f] Like | [Alt+h] Home | [Alt+s] Search | [Esc] Account", id="player-bar")

    def on_mount(self):
        self.player = Player()
        self.results_data = {}
        self.queued_songs = []
        self.session_liked_songs = set() # Track likes in current session
        self.current_track_id = None
        self._current_volume = 100
        
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
        p_table.add_row("❤️ Liked Music", key="liked")
        p_table.add_row("🔄 Refresh Lists", key="refresh")
        p_table.cursor_type = "row"

        # Queue table setup
        q_table = self.query_one("#queue-list")
        q_table.add_column("Song Title")
        q_table.cursor_type = "row"
        
        self.query_one("#search-input").focus()

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
        if event.button.id == "btn-home":
            self.load_home_content()

    @work(exclusive=True)
    async def load_home_content(self):
        """Fetch and display recommended songs from the Home section."""
        self.query_one("#player-bar").update("🏠 Loading recommendations from Home...")
        try:
            tracks = await asyncio.to_thread(self.app.client.get_home)
            if tracks:
                for t in tracks:
                    if 'videoId' in t:
                        self.results_data[t['videoId']] = t
                self.populate_table(tracks)
                self.query_one("#player-bar").update("🏠 Home recommendations loaded.")
            else:
                self.notify("No direct tracks found on Home. Try searching instead.", severity="warning")
        except Exception as e:
            self.notify(f"Error loading home: {e}", severity="error")

    def on_data_table_row_selected(self, event: DataTable.RowSelected):
        if event.data_table.id == "playlist-list":
            playlist_id = event.row_key.value
            if playlist_id == "refresh":
                self.load_playlists()
            else:
                self.load_playlist_content(playlist_id)
        elif event.data_table.id == "queue-list":
            # Play song from queue
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

    def populate_table(self, results):
        table = self.query_one("#results-table")
        table.clear()
        for song in results:
            video_id = song.get("videoId")
            if video_id:
                artists = song.get("artists", [])
                artist_name = ", ".join([a["name"] for a in artists]) if isinstance(artists, list) else "Unknown"
                table.add_row(" 🖼️ ", song.get("title", "Unknown"), artist_name, key=video_id)

    def play_selected_song(self, video_id):
        song = self.results_data.get(video_id)
        if not song: return
        self.current_track_id = video_id
        self.query_one("#current-title").update(song.get("title", "Unknown"))
        artists = song.get("artists", [])
        artist_name = ", ".join([a["name"] for a in artists]) if isinstance(artists, list) else "Unknown"
        self.query_one("#current-artist").update(artist_name)
        album = song.get("album")
        album_name = album.get("name", "Unknown") if isinstance(album, dict) else "Unknown"
        self.query_one("#current-album").update(f"Album: {album_name}")
        thumbnails = song.get("thumbnails", [])
        if thumbnails: self.download_art(thumbnails[-1]["url"])
        self.query_one("#player-bar").update(f"Buffering: {song.get('title')}...")
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
                if resp.status_code == 200: self.query_one(AlbumArt).set_image(resp.content)
        except: pass

    @work(exclusive=True)
    async def toggle_worker(self):
        try:
            await asyncio.to_thread(self.player.toggle_pause)
            status = await asyncio.to_thread(self.player.get_status)
            state = "Paused" if status.get("paused") else "Playing"
            self.query_one("#player-bar").update(f"Status: {state}")
        except: pass

    def on_input_changed(self, event: Input.Changed):
        if event.input.id == "search-input":
            if len(event.value) > 2: self.run_search(event.value)
            elif len(event.value) == 0: self.query_one("#results-table").clear()

    @work(exclusive=True)
    async def run_search(self, query):
        try:
            results = await asyncio.to_thread(self.app.client.search_songs, query)
            for s in results:
                if 'videoId' in s: self.results_data[s['videoId']] = s
            self.populate_table(results)
        except: pass

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
        """Remove the last song added to the queue."""
        if not self.queued_songs:
            self.notify("Queue is already empty", severity="error")
            return

        # Pop the last song added
        last_song = self.queued_songs.pop()
        video_id = last_song.get('videoId')
        url = f"https://music.youtube.com/watch?v={video_id}"
        
        if self.player.remove_from_queue(url):
            self.update_queue_ui()
            
            # Determine what's next in the queue (the head)
            next_up = self.queued_songs[0].get('title') if self.queued_songs else "None"
            status_msg = f"Removed: {last_song.get('title')} | Next up: {next_up}"
            
            self.notify(status_msg, severity="warning")
            self.query_one("#player-bar").update(status_msg)
        else:
            # Re-add if removal failed for some reason
            self.queued_songs.append(last_song)
            self.notify("Failed to remove from player queue", severity="error")

    def action_add_to_liked(self):
        # Deprecated by toggle_liked
        pass

    def action_toggle_liked(self):
        """Toggle 'Like' status for the currently selected song."""
        table = self.query_one("#results-table")
        if table.cursor_row is not None:
            row_key = table.coordinate_to_cell_key(table.cursor_coordinate).row_key
            video_id = row_key.value
            song = self.results_data.get(video_id)
            if song:
                is_liked = video_id in self.session_liked_songs
                self.toggle_liked_worker(video_id, song.get('title'), is_liked)

    @work(thread=True)
    def toggle_liked_worker(self, video_id, title, was_liked):
        try:
            if was_liked:
                self.app.client.unlike_song(video_id)
                self.session_liked_songs.remove(video_id)
                self.app.notify(f"Removed from favorites: {title}", severity="warning")
            else:
                self.app.client.like_song(video_id)
                self.session_liked_songs.add(video_id)
                self.app.notify(f"Added to favorites: {title}")
        except Exception as e:
            self.app.notify(f"Error toggling like: {e}", severity="error")

    def action_toggle_pause(self): self.toggle_worker()
    def key_space(self): self.action_toggle_pause()
    def key_q(self): self.app.exit()
        def action_focus_search(self):
            self.query_one("#search-input").focus()
    
        def action_search_home(self):
            """Action to trigger home recommendations."""
            self.load_home_content()
    
